#!/usr/bin/env python3
"""
SWE-bench Heavy: Cleanup Script
Resets the test environment for new runs.
"""
import json
import os
import shutil
import sys
import argparse
from datetime import datetime


def reset_state():
    """Reset state.json to initial configuration."""
    # Load current config to preserve test settings
    try:
        with open('state.json', 'r') as f:
            current_state = json.load(f)
        test_config = current_state.get('test_config', {})
    except (FileNotFoundError, json.JSONDecodeError):
        # Default configuration
        test_config = {
            "mode": "ALL",
            "total_issues": 300,
            "dataset_file": "swe_bench_lite.jsonl",
            "start_index": 0,
            "end_index": 299
        }

    # Reset to initial state
    fresh_state = {
        "test_config": test_config,
        "current_state": {
            "current_issue_index": 0,
            "issues_attempted": 0,
            "issues_passed": 0,
            "issues_failed": 0,
            "issues_skipped": 0,
            "last_activity": None,
            "session_start": None
        },
        "issue_status": {},
        "failed_issues": [],
        "skipped_issues": [],
        "completed_issues": [],
        "retry_queue": []
    }

    with open('state.json', 'w') as f:
        json.dump(fresh_state, f, indent=2)
    
    print("✅ State reset to initial configuration")


def reset_progress():
    """Reset progress.md to initial state."""
    # Load test config to populate template
    try:
        with open('state.json', 'r') as f:
            state = json.load(f)
        config = state['test_config']
        mode = config.get('mode', 'ALL')
        dataset = config.get('dataset_file', 'swe_bench_lite.jsonl')
        total = config.get('total_issues', 300)
    except (FileNotFoundError, json.JSONDecodeError):
        mode = 'ALL'
        dataset = 'swe_bench_lite.jsonl'
        total = 300

    initial_progress = f"""# SWE-bench Heavy Progress Log

## Test Configuration
- **Mode**: {mode}
- **Dataset**: {dataset}
- **Started**: Not started yet
- **Status**: Ready to begin

## Current Statistics
- **Issues Attempted**: 0/{total}
- **Issues Passed**: 0
- **Issues Failed**: 0
- **Issues Skipped**: 0
- **Success Rate**: 0%

## Recent Activity
*No activity yet*

## Issue Details
*Issue progress will be logged here*

## Notes
- Test environment reset and ready
- All tooling in place for autonomous operation
- Bot can resume from any interruption using this log
"""

    with open('progress.md', 'w') as f:
        f.write(initial_progress)
    
    print("✅ Progress log reset")


def clean_issues_directory(specific_issues=None):
    """Clean the issues directory."""
    issues_dir = 'issues'
    if not os.path.exists(issues_dir):
        print("No issues directory found")
        return

    if specific_issues:
        # Clean only specific issues
        for issue_id in specific_issues:
            issue_path = os.path.join(issues_dir, issue_id)
            if os.path.exists(issue_path):
                shutil.rmtree(issue_path)
                print(f"✅ Cleaned issue: {issue_id}")
            else:
                print(f"⚠️ Issue not found: {issue_id}")
    else:
        # Clean entire issues directory
        shutil.rmtree(issues_dir)
        os.makedirs(issues_dir)
        print("✅ All issue directories cleaned")


def clean_logs():
    """Clean log files."""
    log_dirs = ['logs', 'results']
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            shutil.rmtree(log_dir)
            os.makedirs(log_dir)
            print(f"✅ Cleaned {log_dir} directory")


def backup_current_state():
    """Create a backup of current state before cleanup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    # Backup key files
    files_to_backup = ['state.json', 'progress.md']
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"Backed up {file}")

    # Backup issues directory if it exists
    if os.path.exists('issues'):
        shutil.copytree('issues', os.path.join(backup_dir, 'issues'))
        print("Backed up issues directory")

    print(f"✅ Backup created: {backup_dir}")
    return backup_dir


def show_current_status():
    """Show current test status before cleanup."""
    try:
        with open('state.json', 'r') as f:
            state = json.load(f)
        current = state['current_state']
        
        print("Current Test Status:")
        print(f"- Issues Attempted: {current['issues_attempted']}")
        print(f"- Issues Passed: {current['issues_passed']}")
        print(f"- Issues Failed: {current['issues_failed']}")
        print(f"- Issues Skipped: {current['issues_skipped']}")
        print(f"- Completed Issues: {len(state['completed_issues'])}")
        print(f"- Failed Issues: {len(state['failed_issues'])}")
        print(f"- Retry Queue: {len(state['retry_queue'])}")
        
        if current['session_start']:
            print(f"- Session Started: {current['session_start']}")
        if current['last_activity']:
            print(f"- Last Activity: {current['last_activity']}")
    except (FileNotFoundError, json.JSONDecodeError):
        print("No current state found")


def main():
    """Main cleanup process."""
    parser = argparse.ArgumentParser(description='SWE-bench Heavy Cleanup Tool')
    parser.add_argument('--issues', nargs='+', help='Specific issue IDs to clean')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup')
    parser.add_argument('--keep-logs', action='store_true', help='Keep log directories')
    parser.add_argument('--status-only', action='store_true', help='Show status without cleaning')
    
    args = parser.parse_args()

    print("SWE-bench Heavy Cleanup")
    print("="*50)

    # Show current status
    show_current_status()

    if args.status_only:
        return

    # Confirm cleanup
    if not args.issues:
        print("\n⚠️ This will reset the entire test environment!")
        print("All progress will be lost unless backed up.")
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Cleanup cancelled")
            return
    else:
        print(f"\n⚠️ This will clean specific issues: {', '.join(args.issues)}")
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Cleanup cancelled")
            return

    # Create backup unless disabled
    backup_dir = None
    if not args.no_backup:
        backup_dir = backup_current_state()

    # Perform cleanup
    if args.issues:
        # Clean specific issues
        clean_issues_directory(args.issues)
    else:
        # Full cleanup
        reset_state()
        reset_progress()
        clean_issues_directory()
        if not args.keep_logs:
            clean_logs()

    print("\n" + "="*50)
    print("CLEANUP COMPLETE")
    print("="*50)
    
    if backup_dir:
        print(f"Backup saved to: {backup_dir}")
    
    if args.issues:
        print(f"Cleaned specific issues: {', '.join(args.issues)}")
    else:
        print("Test environment completely reset")

    print("\nNext steps:")
    print("1. Run 'python3 setup.py' if you need to reconfigure")
    print("2. Start testing with 'python3 get_next_issue.py'")
    print("3. For bots: 'read instructions.md and attempt completion when all issues are resolved'")


if __name__ == "__main__":
    main()
