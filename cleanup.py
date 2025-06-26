#!/usr/bin/env python3
"""
SWE-bench Heavy: Cleanup Script
Resets ONLY test data for new runs while preserving all production files.
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


def clean_test_directories():
    """Clean ONLY test data directories, preserve all production files."""
    test_dirs = ['issues', 'logs', 'results', 'runs']
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"✅ Cleaned test directory: {test_dir}")
    
    # Recreate runs directory (empty, for working copies)
    os.makedirs('runs', exist_ok=True)
    with open('runs/.gitignore', 'w') as f:
        f.write("# Working copies - not tracked in git\n*\n!.gitignore\n")
    
    # Recreate other test directories
    for test_dir in ['issues', 'logs', 'results']:
        os.makedirs(test_dir, exist_ok=True)
    
    print("✅ Test directories reset")


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


def validate_environment():
    """Validate that essential files are preserved."""
    essential_files = [
        'setup.py', 'get_next_issue.py', 'grading_fast.py', 'record_progress.py',
        'instructions.md', 'heavy.md', 'install.md', 'swe_bench_lite.jsonl', 'clone_missing_repos.py'
    ]
    essential_dirs = ['repos']
    
    missing = []
    for file in essential_files:
        if not os.path.exists(file):
            missing.append(file)
    
    for dir in essential_dirs:
        if not os.path.exists(dir):
            missing.append(f"{dir}/")
    
    if missing:
        print(f"❌ CRITICAL: Missing essential files/dirs: {missing}")
        print("This indicates the environment may be corrupted!")
        return False
    
    # Check repos has content
    if not os.listdir('repos'):
        print("❌ CRITICAL: repos/ directory is empty!")
        return False
    
    repo_count = len([d for d in os.listdir('repos') if os.path.isdir(os.path.join('repos', d))])
    print(f"✅ Environment validated: {repo_count} repositories preserved")
    return True


def main():
    """Main cleanup process - SAFE test data cleanup only."""
    parser = argparse.ArgumentParser(description='SWE-bench Heavy Safe Cleanup')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup')
    parser.add_argument('--status-only', action='store_true', help='Show status without cleaning')
    
    args = parser.parse_args()

    print("SWE-bench Heavy Safe Cleanup")
    print("="*50)
    print("This script ONLY cleans test data:")
    print("✅ PRESERVES: All scripts, docs, repos/, swe_bench_lite.jsonl")
    print("🗑️  CLEANS: issues/, logs/, results/, runs/, state.json, progress.md")
    print("="*50)

    # Validate environment first
    if not validate_environment():
        print("❌ Environment validation failed - aborting for safety")
        sys.exit(1)

    # Show current status
    show_current_status()

    if args.status_only:
        return

    # Confirm cleanup
    print(f"\n⚠️  This will reset test data for a fresh start.")
    print("All production files will be preserved.")
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cleanup cancelled")
        return

    # Create backup unless disabled
    backup_dir = None
    if not args.no_backup:
        backup_dir = backup_current_state()

    # Perform SAFE cleanup (test data only)
    reset_state()
    reset_progress()
    clean_test_directories()

    # Final validation
    if not validate_environment():
        print("❌ CRITICAL: Environment corrupted during cleanup!")
        sys.exit(1)

    print("\n" + "="*50)
    print("✅ SAFE CLEANUP COMPLETE")
    print("="*50)
    
    if backup_dir:
        print(f"Backup saved to: {backup_dir}")
    
    print("Test environment reset - all production files preserved")
    print("\nNext steps:")
    print("1. Run 'python3 setup.py' to configure test scope")
    print("2. Start testing with 'python3 get_next_issue.py'")
    print("3. For bots: 'read instructions.md and attempt completion when all issues are resolved'")


if __name__ == "__main__":
    main()
