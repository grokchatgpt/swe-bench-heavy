#!/usr/bin/env python3
"""
SWE-bench Heavy: Progress Recording Tool
Records issue progress and updates state for resumption capability.
"""
import json
import sys
from datetime import datetime
from typing import Dict, Any


def load_state() -> Dict[str, Any]:
    """Load current test state."""
    try:
        with open('state.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: state.json not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid state.json: {e}")
        sys.exit(1)


def update_state(state: Dict[str, Any]) -> None:
    """Save updated state."""
    state['current_state']['last_activity'] = datetime.now().isoformat()
    with open('state.json', 'w') as f:
        json.dump(state, f, indent=2)


def is_benchmark_issue(issue_id: str) -> bool:
    """Check if this is a real benchmark issue (not setup/test)."""
    # Exclude setup and test issues from statistics
    setup_patterns = ['test_setup', 'setup_test', 'test_issue']
    return issue_id not in setup_patterns and not issue_id.startswith('test_')


def update_progress_log(issue_id: str, status: str, notes: str = "") -> None:
    """Update the human-readable progress log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Read current progress
    try:
        with open('progress.md', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = "# SWE-bench Heavy Progress Log\n\n"
    
    # Update statistics section
    state = load_state()
    stats = state['current_state']
    total_attempted = stats['issues_attempted']
    total_passed = stats['issues_passed']
    total_failed = stats['issues_failed']
    total_skipped = stats['issues_skipped']
    success_rate = (total_passed / total_attempted * 100) if total_attempted > 0 else 0
    
    # Find and update statistics section
    lines = content.split('\n')
    new_lines = []
    in_stats = False
    in_recent = False
    in_details = False
    
    for line in lines:
        if line.startswith('## Current Statistics'):
            in_stats = True
            new_lines.append(line)
        elif line.startswith('## Recent Activity'):
            in_stats = False
            in_recent = True
            new_lines.append(line)
        elif line.startswith('## Issue Details'):
            in_recent = False
            in_details = True
            new_lines.append(line)
        elif line.startswith('##') and in_stats:
            in_stats = False
            new_lines.append(line)
        elif line.startswith('##') and in_recent:
            in_recent = False
            new_lines.append(line)
        elif line.startswith('##') and in_details:
            in_details = False
            new_lines.append(line)
        elif in_stats and line.startswith('- **'):
            # Replace statistics lines
            if 'Issues Attempted' in line:
                new_lines.append(f"- **Issues Attempted**: {total_attempted}/300")
            elif 'Issues Passed' in line:
                new_lines.append(f"- **Issues Passed**: {total_passed}")
            elif 'Issues Failed' in line:
                new_lines.append(f"- **Issues Failed**: {total_failed}")
            elif 'Issues Skipped' in line:
                new_lines.append(f"- **Issues Skipped**: {total_skipped}")
            elif 'Success Rate' in line:
                new_lines.append(f"- **Success Rate**: {success_rate:.1f}%")
            else:
                new_lines.append(line)
        elif in_recent and line.startswith('*'):
            # Replace recent activity
            new_lines.append(f"**{timestamp}**: {issue_id} - {status}" + (f" ({notes})" if notes else ""))
        elif in_details and line == "*Issue progress will be logged here*":
            # Replace placeholder
            new_lines.append(f"### {issue_id} - {status}")
            new_lines.append(f"- **Timestamp**: {timestamp}")
            new_lines.append(f"- **Status**: {status}")
            if notes:
                new_lines.append(f"- **Notes**: {notes}")
            new_lines.append("")
        else:
            new_lines.append(line)
    
    # If we're in details section, add new entry
    if in_details and not any('*Issue progress will be logged here*' in line for line in lines):
        new_lines.append(f"### {issue_id} - {status}")
        new_lines.append(f"- **Timestamp**: {timestamp}")
        new_lines.append(f"- **Status**: {status}")
        if notes:
            new_lines.append(f"- **Notes**: {notes}")
        new_lines.append("")
    
    # Write updated progress
    with open('progress.md', 'w') as f:
        f.write('\n'.join(new_lines))


def track_attempt(state: Dict[str, Any], issue_id: str, status: str, notes: str) -> None:
    """Track individual attempts per issue."""
    # Initialize issue attempts tracking if not exists
    if 'issue_attempts' not in state:
        state['issue_attempts'] = {}
    
    if issue_id not in state['issue_attempts']:
        state['issue_attempts'][issue_id] = {
            'attempt_count': 0,
            'attempts': [],
            'current_status': None
        }
    
    # Increment attempt count for this issue
    state['issue_attempts'][issue_id]['attempt_count'] += 1
    attempt_num = state['issue_attempts'][issue_id]['attempt_count']
    
    # Record this attempt
    attempt_record = {
        'attempt': attempt_num,
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'notes': notes
    }
    
    state['issue_attempts'][issue_id]['attempts'].append(attempt_record)
    state['issue_attempts'][issue_id]['current_status'] = status
    
    print(f"📊 Attempt #{attempt_num} for {issue_id}: {status}")


def update_attempt_statistics(state: Dict[str, Any]) -> None:
    """Update statistics to include attempt tracking."""
    current = state['current_state']
    
    # Calculate total attempts across all issues
    total_attempts = 0
    unique_issues_attempted = 0
    
    if 'issue_attempts' in state:
        for issue_id, attempts_data in state['issue_attempts'].items():
            if is_benchmark_issue(issue_id):
                total_attempts += attempts_data['attempt_count']
                unique_issues_attempted += 1
    
    # Update new statistics
    current['total_attempts'] = total_attempts
    current['unique_issues_attempted'] = unique_issues_attempted
    
    if unique_issues_attempted > 0:
        current['avg_attempts_per_issue'] = total_attempts / unique_issues_attempted
    else:
        current['avg_attempts_per_issue'] = 0


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python record_progress.py <issue_id> <status> [notes]")
        print("Status codes: PASS, FAIL, SKIP, RETRY")
        sys.exit(1)
    
    issue_id = sys.argv[1]
    status = sys.argv[2].upper()
    notes = sys.argv[3] if len(sys.argv) > 3 else ""
    
    valid_statuses = ['PASS', 'FAIL', 'SKIP', 'RETRY']
    if status not in valid_statuses:
        print(f"ERROR: Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}")
        sys.exit(1)
    
    # Load and update state
    state = load_state()
    current = state['current_state']
    
    # Only update counters for real benchmark issues
    is_real_issue = is_benchmark_issue(issue_id)
    
    # Check if this issue had previous attempts and subtract old status
    if is_real_issue and 'issue_attempts' in state and issue_id in state['issue_attempts']:
        prev_attempts = state['issue_attempts'][issue_id]['attempts']
        if len(prev_attempts) > 0:  # Had previous attempts
            # Subtract previous result from counters
            last_status = prev_attempts[-1]['status']
            if last_status == 'PASS':
                current['issues_passed'] -= 1
            elif last_status == 'FAIL':
                current['issues_failed'] -= 1
            elif last_status == 'SKIP':
                current['issues_skipped'] -= 1
    
    # Track this attempt (AFTER checking previous attempts)
    track_attempt(state, issue_id, status, notes)
    
    # Update legacy counters (for first attempt only)
    if is_real_issue and state['issue_attempts'][issue_id]['attempt_count'] == 1:
        current['issues_attempted'] += 1
    
    if status == 'PASS':
        if is_real_issue:
            current['issues_passed'] += 1
        if issue_id not in state['completed_issues']:
            state['completed_issues'].append(issue_id)
        # Remove from other lists if present
        for lst in ['failed_issues', 'skipped_issues', 'retry_queue']:
            if issue_id in state[lst]:
                state[lst].remove(issue_id)
    elif status == 'FAIL':
        if is_real_issue:
            current['issues_failed'] += 1
        if issue_id not in state['failed_issues']:
            state['failed_issues'].append(issue_id)
        # Remove from other lists if present
        for lst in ['completed_issues', 'skipped_issues', 'retry_queue']:
            if issue_id in state[lst]:
                state[lst].remove(issue_id)
    elif status == 'SKIP':
        if is_real_issue:
            current['issues_skipped'] += 1
        if issue_id not in state['skipped_issues']:
            state['skipped_issues'].append(issue_id)
        # Remove from other lists if present
        for lst in ['completed_issues', 'failed_issues', 'retry_queue']:
            if issue_id in state[lst]:
                state[lst].remove(issue_id)
    elif status == 'RETRY':
        # Add to retry queue if not already there
        if issue_id not in state['retry_queue']:
            state['retry_queue'].append(issue_id)
    
    # Update legacy issue status tracking (overwrites previous)
    state['issue_status'][issue_id] = {
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'notes': notes
    }
    
    # Update attempt statistics
    update_attempt_statistics(state)
    
    # Save state
    update_state(state)
    
    # Update progress log
    update_progress_log(issue_id, status, notes)
    
    print(f"Progress recorded: {issue_id} - {status}")
    if notes:
        print(f"Notes: {notes}")
    
    # Print current stats
    print(f"\nCurrent Progress:")
    print(f"- Unique Issues Attempted: {current.get('unique_issues_attempted', current['issues_attempted'])}/300")
    print(f"- Total Attempts: {current.get('total_attempts', current['issues_attempted'])}")
    print(f"- Passed: {current['issues_passed']}")
    print(f"- Failed: {current['issues_failed']}")
    print(f"- Skipped: {current['issues_skipped']}")
    
    if current.get('unique_issues_attempted', current['issues_attempted']) > 0:
        success_rate = current['issues_passed'] / current.get('unique_issues_attempted', current['issues_attempted']) * 100
        print(f"- Success Rate: {success_rate:.1f}%")
        
        avg_attempts = current.get('avg_attempts_per_issue', 1.0)
        print(f"- Avg Attempts per Issue: {avg_attempts:.1f}")
    
    # Show attempt history for this issue
    if is_real_issue and 'issue_attempts' in state and issue_id in state['issue_attempts']:
        attempts_data = state['issue_attempts'][issue_id]
        if attempts_data['attempt_count'] > 1:
            print(f"\nAttempt History for {issue_id}:")
            for attempt in attempts_data['attempts']:
                print(f"  #{attempt['attempt']}: {attempt['status']} - {attempt['notes'][:50]}...")
    
    # Show if this was excluded from stats
    if not is_real_issue:
        print(f"\nNOTE: '{issue_id}' excluded from benchmark statistics (setup/test issue)")


if __name__ == "__main__":
    main()
