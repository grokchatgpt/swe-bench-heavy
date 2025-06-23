#!/usr/bin/env python3
"""
SWE-bench Heavy: Reset to Pristine State
Cleans up development clutter and sets up proper directory structure for GitHub upload.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

def clean_development_files():
    """Remove development and testing files that aren't part of the production toolchain."""
    dev_files = [
        'clone_missing_repos.py',  # Development utility, not needed in production
        'grading.py',              # Keep grading_fast.py instead
        'validate.py',             # Development utility
        'issues/',                 # Remove all previous test runs
        'logs/',                   # Remove log files
        'results/',                # Remove result files
        '.pytest_cache/',          # Remove pytest cache
        '__pycache__/',            # Remove Python cache
    ]
    
    print("Cleaning development files...")
    for item in dev_files:
        if os.path.exists(item):
            if os.path.isdir(item):
                print(f"Removing directory: {item}")
                shutil.rmtree(item)
            else:
                print(f"Removing file: {item}")
                os.remove(item)
    
    # Clean any .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'))

def reorganize_repositories():
    """Move runs/ to repos/ for pristine originals, create empty runs/ for working copies."""
    print("Reorganizing repository structure...")
    
    # If repos/ already exists, remove it
    if os.path.exists('repos'):
        print("Removing existing repos/ directory...")
        shutil.rmtree('repos')
    
    # Move runs/ to repos/ (these become the pristine originals)
    if os.path.exists('runs'):
        print("Moving runs/ to repos/ (pristine originals)...")
        shutil.move('runs', 'repos')
    else:
        print("ERROR: No runs/ directory found!")
        sys.exit(1)
    
    # Create empty runs/ directory for working copies
    print("Creating empty runs/ directory for working copies...")
    os.makedirs('runs', exist_ok=True)
    
    # Create .gitignore for runs/ directory
    with open('runs/.gitignore', 'w') as f:
        f.write("# Working copies - not tracked in git\n")
        f.write("*\n")
        f.write("!.gitignore\n")

def reset_state_files():
    """Reset state files to pristine initial state."""
    print("Resetting state files...")
    
    # Reset state.json to initial state
    initial_state = {
        "test_config": {
            "mode": "ALL",
            "total_issues": 300,
            "dataset_file": "swe_bench_lite.jsonl",
            "start_index": 0,
            "end_index": 299
        },
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
        json.dump(initial_state, f, indent=2)
    
    # Reset progress.md
    with open('progress.md', 'w') as f:
        f.write("# SWE-bench Heavy Progress Log\n\n")
        f.write("This file tracks progress during test runs.\n\n")
        f.write("## Current Status\n")
        f.write("- Issues Attempted: 0/300\n")
        f.write("- Issues Passed: 0\n")
        f.write("- Issues Failed: 0\n")
        f.write("- Issues Skipped: 0\n")
        f.write("- Success Rate: 0.0%\n\n")
        f.write("## Issue Log\n")
        f.write("(Issues will be logged here as they are processed)\n")

def update_setup_script():
    """Update setup.py to use the new repos/ -> runs/ architecture."""
    print("Updating setup.py for new architecture...")
    
    # Read current setup.py
    with open('setup.py', 'r') as f:
        content = f.read()
    
    # Replace runs/ references with repos/ for validation
    content = content.replace(
        'source_repo_dir = f"runs/{issue_id}"',
        'source_repo_dir = f"repos/{issue_id}"'
    )
    content = content.replace(
        'repo_path = f"runs/{issue_id}"',
        'repo_path = f"repos/{issue_id}"'
    )
    content = content.replace(
        'print("✅ All {issue_count} repositories are present in runs/ directory")',
        'print("✅ All {issue_count} repositories are present in repos/ directory")'
    )
    content = content.replace(
        'print("\\nPlease ensure all repositories are downloaded to runs/ directory")',
        'print("\\nPlease ensure all repositories are downloaded to repos/ directory")'
    )
    
    with open('setup.py', 'w') as f:
        f.write(content)

def update_grading_script():
    """Update grading_fast.py to use repos/ for pristine sources."""
    print("Updating grading_fast.py for new architecture...")
    
    with open('grading_fast.py', 'r') as f:
        content = f.read()
    
    # Update to use repos/ for pristine sources
    content = content.replace(
        'source_repo_dir = f"runs/{issue_id}/repo"',
        'source_repo_dir = f"repos/{issue_id}/repo"'
    )
    content = content.replace(
        'print("Make sure you\'ve run setup.py to download all repositories")',
        'print("Make sure repositories are in repos/ directory")'
    )
    
    with open('grading_fast.py', 'w') as f:
        f.write(content)

def create_production_readme():
    """Create a clean README for the production toolchain."""
    readme_content = """# SWE-bench Heavy

A benchmark for testing autonomous AI coding abilities using the SWE-bench Lite dataset without aids like BM25 retrieval, Oracle hints, or RAG.

## Quick Start

1. **Setup Environment**:
   ```bash
   python3 setup.py
   ```

2. **For Autonomous AI Testing**:
   ```
   read instructions.md and attempt completion when all issues are resolved
   ```

3. **For Manual Testing**:
   ```bash
   python3 get_next_issue.py
   # Work on issue in issues/<issue_id>/repo/
   python3 grading_fast.py <issue_id>
   python3 record_progress.py <issue_id> PASS "Fixed the bug"
   ```

## Architecture

- `repos/` - Pristine original repositories (300 issues)
- `runs/` - Working copies created during testing (gitignored)
- `issues/` - Individual issue workspaces created during testing

## Core Tools

- `setup.py` - Environment setup and validation
- `get_next_issue.py` - Issue selection
- `grading_fast.py` - Fast test execution (specific tests only)
- `record_progress.py` - Progress tracking
- `cleanup.py` - Reset test state
- `reset_pristine.py` - Reset to clean state for development

## Documentation

- `heavy.md` - Detailed benchmark description
- `instructions.md` - AI bot instructions
- `install.md` - Complete setup guide

## Test Configuration

Edit `state.json` to configure test scope:
- `ALL` - Test all 300 issues
- `SIZE` - Test first N issues  
- `RANGE` - Test specific issue range

## Features

- **No Training Wheels**: No BM25, Oracle hints, or RAG
- **Autonomous**: Self-directed issue resolution
- **Resumable**: Continue interrupted test runs
- **Fast Testing**: Targeted test execution
- **Context Efficient**: Designed for AI context window management

This is Heavy mode - pure autonomous AI problem-solving capability measurement.
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content)

def create_gitignore():
    """Create appropriate .gitignore for the project."""
    gitignore_content = """# Working directories
runs/
issues/
logs/
results/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/

# Virtual environments
venv/
env/
ENV/
swe_venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)

def validate_final_state():
    """Validate that the final state is correct."""
    print("Validating final state...")
    
    required_files = [
        'setup.py',
        'get_next_issue.py', 
        'grading_fast.py',
        'record_progress.py',
        'cleanup.py',
        'reset_pristine.py',
        'instructions.md',
        'heavy.md',
        'install.md',
        'README.md',
        'state.json',
        'progress.md',
        'swe_bench_lite.jsonl',
        '.gitignore'
    ]
    
    required_dirs = [
        'repos/',
        'runs/'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    missing_dirs = []
    for dir in required_dirs:
        if not os.path.exists(dir):
            missing_dirs.append(dir)
    
    if missing_files or missing_dirs:
        print("❌ Validation failed!")
        if missing_files:
            print(f"Missing files: {missing_files}")
        if missing_dirs:
            print(f"Missing directories: {missing_dirs}")
        return False
    
    # Check repos/ has content
    if not os.listdir('repos'):
        print("❌ repos/ directory is empty!")
        return False
    
    # Check runs/ is empty (except .gitignore)
    runs_contents = os.listdir('runs')
    if runs_contents != ['.gitignore']:
        print(f"❌ runs/ should only contain .gitignore, found: {runs_contents}")
        return False
    
    print("✅ Final state validation passed!")
    return True

def main():
    """Main cleanup process."""
    print("SWE-bench Heavy: Reset to Pristine State")
    print("=" * 50)
    
    # Confirm with user
    response = input("This will clean all development files and reset state. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(0)
    
    # Step 1: Clean development files
    clean_development_files()
    
    # Step 2: Reorganize repositories
    reorganize_repositories()
    
    # Step 3: Reset state files
    reset_state_files()
    
    # Step 4: Update scripts for new architecture
    update_setup_script()
    update_grading_script()
    
    # Step 5: Create production documentation
    create_production_readme()
    create_gitignore()
    
    # Step 6: Validate final state
    if validate_final_state():
        print("\n" + "=" * 50)
        print("✅ PRISTINE STATE READY FOR GITHUB!")
        print("=" * 50)
        print("Repository structure:")
        print("- repos/ - 300 pristine original repositories")
        print("- runs/ - Empty (working copies created during testing)")
        print("- Clean production toolchain files only")
        print("- Reset state files")
        print("- Updated documentation")
        print("\nReady for: git add . && git commit -m 'SWE-bench Heavy toolchain'")
    else:
        print("❌ Validation failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
