#!/usr/bin/env python3
"""
swe-bench-heavy: Get Next Issue Tool
Selects the next issue for the bot to work on based on current state and strategy.
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

def load_state() -> Dict[str, Any]:
    """Load current test state."""
    try:
        with open('state.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: state.json not found. Run setup first.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid state.json: {e}")
        sys.exit(1)

def load_dataset() -> list:
    """Load SWE-bench Lite dataset."""
    state = load_state()
    dataset_file = state['test_config']['dataset_file']
    
    if not os.path.exists(dataset_file):
        print(f"ERROR: Dataset file {dataset_file} not found.")
        print("Run the setup script to download the dataset.")
        sys.exit(1)
    
    issues = []
    try:
        with open(dataset_file, 'r') as f:
            for line in f:
                if line.strip():
                    issues.append(json.loads(line))
        return issues
    except Exception as e:
        print(f"ERROR: Failed to load dataset: {e}")
        sys.exit(1)

def update_state(state: Dict[str, Any]) -> None:
    """Save updated state."""
    state['current_state']['last_activity'] = datetime.now().isoformat()
    with open('state.json', 'w') as f:
        json.dump(state, f, indent=2)

def check_current_issue_validation(state: Dict[str, Any]) -> Optional[str]:
    """Check if current issue needs proper grading validation."""
    current_index = state['current_state'].get('current_issue_index')
    
    if current_index is None:
        return None  # No current issue
    
    # Load dataset to get current issue ID
    try:
        with open(state['test_config']['dataset_file'], 'r') as f:
            issues = []
            for line in f:
                if line.strip():
                    issues.append(json.loads(line))
            
            if current_index < len(issues):
                current_issue_id = issues[current_index]['instance_id']
                
                # Check if this issue has been properly validated
                if current_issue_id not in state['completed_issues'] and \
                   current_issue_id not in state['failed_issues'] and \
                   current_issue_id not in state['skipped_issues']:
                    
                    # Check if grading has been attempted
                    grading_file = f"issues/{current_issue_id}/test_results.json"
                    if not os.path.exists(grading_file):
                        return current_issue_id
                    
                    # Check if progress has been recorded properly
                    if 'issue_attempts' in state and current_issue_id in state['issue_attempts']:
                        attempts = state['issue_attempts'][current_issue_id]['attempts']
                        # Look for recent grading-based attempts
                        for attempt in reversed(attempts):
                            if 'official' in attempt.get('notes', '').lower():
                                return None  # Found proper grading
                        
                        # No grading-based attempts found
                        return current_issue_id
                    else:
                        # No attempt tracking
                        return current_issue_id
    except Exception:
        pass
    
    return None


def select_next_issue(state: Dict[str, Any], issues: list) -> Optional[Dict[str, Any]]:
    """Select next issue based on strategy with validation requirements."""
    config = state['test_config']
    current = state['current_state']
    
    # CRITICAL: Check if current issue needs proper validation
    unvalidated_issue = check_current_issue_validation(state)
    if unvalidated_issue:
        print(f"❌ VALIDATION REQUIRED")
        print(f"Current issue '{unvalidated_issue}' has not been properly graded.")
        print(f"")
        print(f"Options:")
        print(f"1. Test your solution: python3 grading_fast.py {unvalidated_issue}")
        print(f"2. Skip this issue: python3 record_progress.py {unvalidated_issue} SKIP 'Skipping for now'")
        print(f"")
        print(f"You must choose one option before getting the next issue.")
        return None
    
    # Check if we have retry queue items
    if state['retry_queue']:
        issue_id = state['retry_queue'].pop(0)
        for issue in issues:
            if issue['instance_id'] == issue_id:
                print(f"RETRY: Selecting issue {issue_id} from retry queue")
                return issue
    
    # Find next unprocessed issue
    start_idx = config['start_index']
    end_idx = config['end_index']
    
    for i in range(start_idx, min(end_idx + 1, len(issues))):
        issue = issues[i]
        issue_id = issue['instance_id']
        
        # Skip if already completed
        if issue_id in state['completed_issues']:
            continue
            
        # Skip if currently failed (will be in retry queue if we want to retry)
        if issue_id in state['failed_issues'] and issue_id not in state['retry_queue']:
            continue
            
        return issue
    
    return None

def main():
    """Main entry point."""
    state = load_state()
    issues = load_dataset()
    
    # Initialize session if first run
    if not state['current_state']['session_start']:
        state['current_state']['session_start'] = datetime.now().isoformat()
    
    next_issue = select_next_issue(state, issues)
    
    if not next_issue:
        print("No more issues to process!")
        print(f"Completed: {len(state['completed_issues'])}")
        print(f"Failed: {len(state['failed_issues'])}")
        print(f"Skipped: {len(state['skipped_issues'])}")
        sys.exit(0)
    
    issue_id = next_issue['instance_id']
    
    # Update state
    state['current_state']['current_issue_index'] = issues.index(next_issue)
    update_state(state)
    
    # Output issue information
    print(f"ISSUE_ID: {issue_id}")
    print(f"REPO: {next_issue['repo']}")
    print(f"BASE_COMMIT: {next_issue['base_commit']}")
    print(f"PROBLEM_STATEMENT:")
    print(next_issue['problem_statement'])
    print(f"\nHINTS_TEXT:")
    print(next_issue.get('hints_text', 'No hints available'))
    print(f"\nTEST_PATCH:")
    print(next_issue.get('test_patch', 'No test patch available'))
    
    # Create issue-specific directory
    issue_dir = f"issues/{issue_id}"
    os.makedirs(issue_dir, exist_ok=True)
    
    # Save issue details to file
    with open(f"{issue_dir}/issue.json", 'w') as f:
        json.dump(next_issue, f, indent=2)
    
    # Set up working directory in runs folder
    work_dir = f"runs/{issue_id}"
    repo_source = f"repos/{issue_id}/repo"
    
    if os.path.exists(repo_source):
        # Remove existing work directory if it exists
        if os.path.exists(work_dir):
            import shutil
            shutil.rmtree(work_dir)
        
        # Copy repo to runs directory for work
        import shutil
        shutil.copytree(repo_source, work_dir)
        print(f"Repository copied from: {repo_source}")
        print(f"Work directory: {work_dir}")
    else:
        print(f"WARNING: Pre-downloaded repo not found at {repo_source}")
        print("Bot will need to clone the repository manually")
        print(f"Work directory: {issue_dir}")
    
    print(f"\nIssue details saved to: {issue_dir}/issue.json")

if __name__ == "__main__":
    main()
