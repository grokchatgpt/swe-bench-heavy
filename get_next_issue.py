#!/usr/bin/env python3
"""
SWE-Bench Heavy: Get Next Issue Tool
Selects the next issue for the bot to work on using the perfect Docker tooling.
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

def load_dataset() -> list:
    """Load SWE-bench Lite dataset."""
    if not os.path.exists('swe_bench_lite.jsonl'):
        print("ERROR: swe_bench_lite.jsonl not found.")
        print("Run: python3 setup.py")
        sys.exit(1)
    
    issues = []
    try:
        with open('swe_bench_lite.jsonl', 'r') as f:
            for line in f:
                if line.strip():
                    issues.append(json.loads(line))
        return issues
    except Exception as e:
        print(f"ERROR: Failed to load dataset: {e}")
        sys.exit(1)

def load_config() -> Dict[str, Any]:
    """Load configuration."""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json not found. Run setup first.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid config.json: {e}")
        sys.exit(1)

def load_progress() -> Dict[str, Any]:
    """Load progress state."""
    if not os.path.exists('state.json'):
        # Initialize empty state
        return {
            'completed_issues': [],
            'failed_issues': [],
            'skipped_issues': [],
            'current_issue_index': 0
        }
    
    try:
        with open('state.json', 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Reset corrupted state
        return {
            'completed_issues': [],
            'failed_issues': [],
            'skipped_issues': [],
            'current_issue_index': 0
        }

def save_progress(progress: Dict[str, Any]) -> None:
    """Save progress state."""
    progress['last_updated'] = datetime.now().isoformat()
    with open('state.json', 'w') as f:
        json.dump(progress, f, indent=2)

def parse_issue_selection(selection_str: str, total_issues: int) -> list:
    """Parse issue selection string into list of indices."""
    if not selection_str:
        return list(range(total_issues))
    
    indices = []
    parts = selection_str.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if '-' in part:
            # Range format: "10-20"
            start, end = part.split('-', 1)
            start_idx = int(start.strip())
            end_idx = int(end.strip())
            indices.extend(range(start_idx, end_idx + 1))
        else:
            # Single index: "42"
            indices.append(int(part))
    
    # Filter valid indices
    return [i for i in indices if 0 <= i < total_issues]

def check_failure_attempts(issue_id: str) -> int:
    """Check how many times this issue has failed."""
    try:
        from failure_tracker import get_failure_count
        return get_failure_count(issue_id)
    except:
        return 0

def select_next_issue(issues: list, config: Dict[str, Any], progress: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Select next issue based on configuration and progress."""
    
    # Parse issue selection from config
    selection_str = config.get('issue_selection', '0-299')
    selected_indices = parse_issue_selection(selection_str, len(issues))
    
    if not selected_indices:
        return None
    
    # Calculate completion statistics - FIXED: Handle overlapping issue states correctly
    total_selected = len(selected_indices)
    completed = len(progress.get('completed_issues', []))
    failed = len(progress.get('failed_issues', []))
    skipped = len(progress.get('skipped_issues', []))
    
    # FIXED: Calculate unique issues processed (an issue can move between states)
    all_processed_issues = set(
        progress.get('completed_issues', []) + 
        progress.get('failed_issues', []) + 
        progress.get('skipped_issues', [])
    )
    unique_processed = len(all_processed_issues)
    remaining = total_selected - unique_processed
    
    print(f"📊 Progress: {completed} completed, {failed} failed, {skipped} skipped")
    print(f"📊 Unique issues processed: {unique_processed}/{total_selected}, {remaining} remaining")
    
    # Get current position in the selection list
    current_idx = progress.get('current_issue_index', 0)
    
    # Find current position in selected_indices list
    current_position = 0
    if current_idx in selected_indices:
        current_position = selected_indices.index(current_idx)
    
    # PHASE 1: Look for fresh unprocessed issues first
    for i in range(current_position, len(selected_indices)):
        idx = selected_indices[i]
        
        if idx >= len(issues):
            continue
            
        issue = issues[idx]
        issue_id = issue['instance_id']
        
        # Skip if already completed
        if issue_id in progress.get('completed_issues', []):
            continue
            
        # Skip if in failed/skipped lists (will handle these in Phase 2)
        if issue_id in progress.get('failed_issues', []) or issue_id in progress.get('skipped_issues', []):
            continue
            
        # Skip if failed too many times (circuit breaker)
        failure_count = check_failure_attempts(issue_id)
        max_attempts = config.get('max_attempts', 10)
        if failure_count >= max_attempts:
            print(f"⚠️ Skipping {issue_id}: {failure_count}/{max_attempts} attempts exceeded")
            continue
        
        # This is a fresh unprocessed issue
        progress['current_issue_index'] = idx
        return issue
    
    # PHASE 2: No fresh issues left, try failed/skipped issues for retry
    print("🔄 No fresh issues remaining. Checking failed/skipped issues for retry...")
    
    # Collect retry candidates with their attempt counts
    retry_candidates = []
    for idx in selected_indices:
        if idx >= len(issues):
            continue
            
        issue = issues[idx]
        issue_id = issue['instance_id']
        
        # Skip if already completed
        if issue_id in progress.get('completed_issues', []):
            continue
            
        # Only consider failed/skipped issues now
        if issue_id not in progress.get('failed_issues', []) and issue_id not in progress.get('skipped_issues', []):
            continue
            
        # Skip if failed too many times (circuit breaker - requires human intervention)
        failure_count = check_failure_attempts(issue_id)
        max_attempts = config.get('max_attempts', 10)
        if failure_count >= max_attempts:
            print(f"⚠️ Skipping {issue_id}: {failure_count}/{max_attempts} attempts exceeded (requires human intervention)")
            continue
        
        # Add to retry candidates with attempt count for sorting
        retry_candidates.append((failure_count, idx, issue_id, issue))
    
    # Sort by attempt count (lowest first) - prioritize issues with fewer attempts
    retry_candidates.sort(key=lambda x: x[0])
    
    # Try the issue with the lowest attempt count first
    for failure_count, idx, issue_id, issue in retry_candidates:
        max_attempts = config.get('max_attempts', 10)
        
        # This is a retry candidate
        if issue_id in progress.get('failed_issues', []):
            print(f"🔄 Retrying previously failed issue: {issue_id} (attempt {failure_count + 1}/{max_attempts})")
        else:
            print(f"🔄 Retrying previously skipped issue: {issue_id} (attempt {failure_count + 1}/{max_attempts})")
        
        progress['current_issue_index'] = idx
        return issue
    
    # PHASE 3: Check if we have true 100% completion (all issues passed)
    total_completed = len(progress.get('completed_issues', []))
    if total_completed == total_selected:
        print("🎉 TRUE 100% COMPLETION: All issues have been PASSED!")
        return None
    
    # PHASE 4: There are unresolved issues but they hit circuit breakers
    unresolved_count = total_selected - total_completed
    print(f"⚠️ {unresolved_count} issues remain unresolved but have hit circuit breakers (max attempts exceeded)")
    print("💡 These require human intervention to continue")
    return None

def setup_work_directory(issue_id: str, repo_name: str) -> str:
    """Set up work directory for the issue."""
    work_dir = f"runs/{issue_id}"
    
    # Create work directory
    os.makedirs(work_dir, exist_ok=True)
    
    # Check if we have a pre-cloned repo
    repo_source = f"repos/{issue_id}/repo"
    if os.path.exists(repo_source) and os.listdir(repo_source):
        print(f"📁 Repository available at: {repo_source}")
        print(f"💡 You can copy files from there to your work directory: {work_dir}")
    else:
        print(f"📁 Work directory ready: {work_dir}")
        print(f"💡 Create files as needed - directories will be auto-created")
    
    return work_dir

def main():
    """Main entry point."""
    print("🎯 SWE-Bench Heavy: Getting Next Issue")
    print("=" * 50)
    
    # Load data
    issues = load_dataset()
    config = load_config()
    progress = load_progress()
    
    print(f"📊 Dataset: {len(issues)} total issues")
    print(f"⚙️ Selection: {config.get('issue_selection', '0-299')}")
    print(f"📈 Progress: {len(progress.get('completed_issues', []))} completed, {len(progress.get('failed_issues', []))} failed")
    
    # Select next issue
    next_issue = select_next_issue(issues, config, progress)
    
    if not next_issue:
        print("\n🎉 YOU HAVE COMPLETED ALL THE ASSIGNED ISSUES! CONGRATULATIONS! THE TESTING IS 100% COMPLETE.")
        print("=" * 60)
        print(f"✅ Completed: {len(progress.get('completed_issues', []))}")
        print(f"❌ Failed: {len(progress.get('failed_issues', []))}")
        print(f"⏭️ Skipped: {len(progress.get('skipped_issues', []))}")
        
        # Calculate final statistics
        total_processed = len(progress.get('completed_issues', [])) + len(progress.get('failed_issues', [])) + len(progress.get('skipped_issues', []))
        completed = len(progress.get('completed_issues', []))
        if total_processed > 0:
            success_rate = (completed / total_processed) * 100
            print(f"📊 Final Success Rate: {success_rate:.1f}%")
        
        print("\n🏆 USE attempt_completion TO SIGNAL YOU ARE FINISHED.")
        print("=" * 60)
        print("\n💡 You can also:")
        print("  - Reset progress: rm state.json")
        sys.exit(0)
    
    issue_id = next_issue['instance_id']
    repo_name = next_issue['repo']
    
    # Save progress
    save_progress(progress)
    
    # Set up work directory
    work_dir = setup_work_directory(issue_id, repo_name)
    
    # Display issue information
    print(f"\n🎯 NEXT ISSUE: {issue_id}")
    print(f"📦 Repository: {repo_name}")
    print(f"🔗 Base Commit: {next_issue['base_commit'][:12]}...")
    print(f"📁 Work Directory: {work_dir}")
    
    print(f"\n📋 PROBLEM STATEMENT:")
    print("-" * 40)
    problem = next_issue['problem_statement']
    # Truncate very long problem statements
    if len(problem) > 1000:
        print(problem[:1000] + "...")
        print(f"[Truncated - full problem statement has {len(problem)} characters]")
    else:
        print(problem)
    
    # Show test information
    fail_to_pass = next_issue.get('FAIL_TO_PASS', [])
    pass_to_pass = next_issue.get('PASS_TO_PASS', [])
    
    if fail_to_pass:
        print(f"\n🧪 TESTS THAT MUST PASS:")
        if isinstance(fail_to_pass, list):
            for test in fail_to_pass[:3]:  # Show first 3
                print(f"  - {test}")
            if len(fail_to_pass) > 3:
                print(f"  ... and {len(fail_to_pass) - 3} more")
        else:
            print(f"  - {fail_to_pass}")
    
    if pass_to_pass:
        print(f"\n✅ TESTS THAT MUST STILL PASS:")
        if isinstance(pass_to_pass, list):
            print(f"  - {len(pass_to_pass)} existing tests must continue to pass")
        else:
            print(f"  - {pass_to_pass}")
    
    # Save issue details
    issue_file = f"{work_dir}/issue.json"
    with open(issue_file, 'w') as f:
        json.dump(next_issue, f, indent=2)
    print(f"\n💾 Issue details saved to: {issue_file}")
    
    # Show next steps
    print(f"\n🚀 NEXT STEPS:")
    print(f"1. Analyze the problem in {work_dir}/")
    print(f"2. Develop your solution")
    print(f"3. Test with: python3 grading_docker.py {issue_id}")
    print(f"4. Iterate until tests pass. Read instructions.md if you are confused - otherwise proceed to solving the problem. Hint: If this is not your first attempt at the problem - your existing solution is wrong - analyze why.")
    
    # Show failure attempts if any
    failure_count = check_failure_attempts(issue_id)
    if failure_count > 0:
        print(f"\n⚠️ This issue has {failure_count} previous failure attempts")
        print(f"💡 Maximum attempts allowed: {config.get('max_attempts', 10)}")
    
    print(f"\n🎯 Ready to work on: {issue_id}")

if __name__ == "__main__":
    main()
