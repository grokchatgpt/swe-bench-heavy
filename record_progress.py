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
    
    if is_real_issue:
        current['issues_attempted'] += 1
    
    if status == 'PASS':
        if is_real_issue:
            current['issues_passed'] += 1
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
    
    # Update issue status tracking
    state['issue_status'][issue_id] = {
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'notes': notes
    }
    
    # Save state
    update_state(state)
    
    # Update progress log
    update_progress_log(issue_id, status, notes)
    
    print(f"Progress recorded: {issue_id} - {status}")
    if notes:
        print(f"Notes: {notes}")
    
    # Print current stats
    print(f"\nCurrent Progress:")
    print(f"- Attempted: {current['issues_attempted']}/300")
    print(f"- Passed: {current['issues_passed']}")
    print(f"- Failed: {current['issues_failed']}")
    print(f"- Skipped: {current['issues_skipped']}")
    
    if current['issues_attempted'] > 0:
        success_rate = current['issues_passed'] / current['issues_attempted'] * 100
        print(f"- Success Rate: {success_rate:.1f}%")
    
    # Show if this was excluded from stats
    if not is_real_issue:
        print(f"\nNOTE: '{issue_id}' excluded from benchmark statistics (setup/test issue)")


if __name__ == "__main__":
    main()
