#!/usr/bin/env python3
"""
SWE-Bench Heavy: Automated Setup
Bulletproof initialization that preserves all valuable assets.
Only cleans run data, never touches repos or Docker images.

Usage: python3 setup.py
"""
import os
import subprocess
import sys
import json

def run_cmd(cmd, check=True, capture=False):
    """Run command with proper error handling."""
    print(f"🔧 {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        if capture:
            print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def clean_run_data():
    """Clean only run data for fresh testing - preserves all valuable assets."""
    print("🧹 Cleaning run data for fresh start...")
    
    import shutil
    import time
    
    # Only clean these directories - they contain test runs, not valuable assets
    clean_dirs = ['runs', 'docker_results']
    
    for dir_name in clean_dirs:
        if os.path.exists(dir_name):
            # Count items before cleanup
            try:
                items_before = len(os.listdir(dir_name))
                print(f"  Found {items_before} items in {dir_name}/")
            except:
                items_before = 0
            
            # Attempt cleanup with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.rmtree(dir_name)
                    print(f"  Cleaned: {dir_name}/ (attempt {attempt + 1})")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"  ❌ Failed to clean {dir_name} after {max_retries} attempts: {e}")
                        print(f"  🔧 Trying alternative cleanup method...")
                        
                        # Alternative: remove contents individually
                        try:
                            for item in os.listdir(dir_name):
                                item_path = os.path.join(dir_name, item)
                                if os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                                else:
                                    os.remove(item_path)
                            print(f"  ✅ Alternative cleanup successful for {dir_name}/")
                        except Exception as e2:
                            print(f"  ❌ Alternative cleanup also failed: {e2}")
                            sys.exit(1)
                    else:
                        print(f"  ⚠️ Cleanup attempt {attempt + 1} failed, retrying...")
                        time.sleep(0.5)
        
        # Recreate empty directory
        os.makedirs(dir_name, exist_ok=True)
        
        # Verify cleanup was successful
        try:
            items_after = len(os.listdir(dir_name))
            if items_after == 0:
                print(f"  ✅ Created clean {dir_name}/")
            else:
                print(f"  ❌ WARNING: {dir_name}/ still contains {items_after} items!")
                print(f"  Items: {os.listdir(dir_name)}")
        except:
            print(f"  ✅ Created {dir_name}/")

def reset_state_files():
    """Reset state tracking files for fresh start with .bak backups for A/B testing."""
    print("🔄 Resetting state tracking with .bak backups...")
    
    # Create .bak versions of existing files for A/B testing
    backup_files = ['state.json', 'progress.md']
    for filename in backup_files:
        if os.path.exists(filename):
            backup_name = f"{filename}.bak"
            try:
                import shutil
                shutil.copy2(filename, backup_name)
                print(f"  📋 Backed up: {filename} -> {backup_name}")
            except Exception as e:
                print(f"  ⚠️ Could not backup {filename}: {e}")
    
    # Calculate total issues from config
    total_issues = 300  # Default fallback
    issue_selection = "0-299"  # Default fallback
    
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
                issue_selection = config.get('issue_selection', '0-299')
                
                # Parse issue selection to get total count
                if '-' in issue_selection:
                    start, end = map(int, issue_selection.split('-'))
                    total_issues = end - start + 1
                else:
                    # Handle single issue or comma-separated list
                    issues = issue_selection.split(',')
                    total_issues = len(issues)
    except Exception as e:
        print(f"  ⚠️ Could not parse config for issue count: {e}")
        print(f"  Using default: {total_issues} issues")
    
    # Reset state.json to initial state with enhanced structure
    initial_state = {
        "test_config": {
            "mode": "RANGE",
            "total_issues": total_issues,
            "dataset_file": "swe_bench_lite.jsonl",
            "start_index": 0,
            "end_index": total_issues - 1
        },
        "current_state": {
            "current_issue_index": 0,
            "issues_attempted": 0,
            "issues_passed": 0,
            "issues_failed": 0,
            "issues_skipped": 0,
            "last_activity": None,
            "session_start": None,
            "total_attempts": 0,
            "unique_issues_attempted": 0,
            "avg_attempts_per_issue": 0.0,
            "session_duration_minutes": 0.0
        },
        "issue_status": {},
        "failed_issues": [],
        "skipped_issues": [],
        "completed_issues": [],
        "retry_queue": [],
        "issue_attempts": {},
        "overall_stats": {},
        "current_issue_index": 0,
        "last_updated": None
    }
    
    try:
        with open('state.json', 'w') as f:
            json.dump(initial_state, f, indent=2)
        print("  ✅ Reset: state.json")
    except Exception as e:
        print(f"  ⚠️ Could not reset state.json: {e}")
    
    # Reset failure_tracker.json - tracks fail attempts per issue
    try:
        with open('failure_tracker.json', 'w') as f:
            json.dump({}, f, indent=2)
        print("  ✅ Reset: failure_tracker.json")
    except Exception as e:
        print(f"  ⚠️ Could not reset failure_tracker.json: {e}")
    
    # Reset progress.md - human-readable progress log with enhanced structure
    initial_progress = f"""# SWE-bench Heavy Progress Log

## Test Configuration
- **Mode**: RANGE
- **Dataset**: swe_bench_lite.jsonl
- **Issue Selection**: {issue_selection}
- **Total Issues**: {total_issues}
- **Started**: Not started yet
- **Status**: Ready to begin

## Current Statistics (Per-Issue Tracking)
- **Unique Issues Attempted**: 0/{total_issues}
- **Total Attempts**: 0
- **Issues Passed**: 0
- **Issues Failed**: 0
- **Issues Skipped**: 0
- **Success Rate**: 0.0%
- **Avg Attempts per Issue**: 0.0

## Overall Statistics (Aggregated Across All Issues)
- **Total Issues Processed**: 0
- **Overall Success Rate**: 0.0%
- **First Attempt Success Rate**: 0.0%
- **Retry Success Rate**: 0.0%
- **Max Attempts on Single Issue**: 0
- **Avg Time per Successful Issue**: 0.0 minutes

## Recent Activity
No activity yet - ready to start testing

## Current Issue Details
No issues attempted yet

## Notes
- Enhanced stats tracking with per-issue and overall statistics
- Individual attempt tracking per issue implemented
- Automatic progress updates and backup system active
- Session management and timing tracking active
"""
    
    try:
        with open('progress.md', 'w') as f:
            f.write(initial_progress)
        print("  ✅ Reset: progress.md")
    except Exception as e:
        print(f"  ⚠️ Could not reset progress.md: {e}")

def ensure_directories():
    """Create required directories if missing."""
    print("📁 Ensuring directories exist...")
    dirs = ['runs', 'docker_results', 'issues']
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            print(f"  Created: {d}/")
        else:
            print(f"  Exists: {d}/")

def check_docker():
    """Verify Docker is available."""
    print("🐳 Checking Docker...")
    try:
        result = run_cmd("docker --version", capture=True)
        print(f"  {result.stdout.strip()}")
    except:
        print("❌ Docker not found! Install Docker first.")
        sys.exit(1)

def download_dataset():
    """Download SWE-Bench Lite dataset if needed."""
    print("📊 Checking dataset...")
    if not os.path.exists('swe_bench_lite.jsonl'):
        print("  Downloading SWE-Bench Lite dataset...")
        run_cmd("curl -o swe_bench_lite.jsonl https://raw.githubusercontent.com/princeton-nlp/SWE-bench/main/swe_bench_lite.jsonl")
    else:
        print("  Dataset already exists")

def check_assets():
    """Verify valuable assets exist."""
    print("🏆 Checking valuable assets...")
    
    # Check repos
    if os.path.exists('repos') and os.listdir('repos'):
        repo_count = len([d for d in os.listdir('repos') if os.path.isdir(f'repos/{d}')])
        print(f"  ✅ Found {repo_count} repositories")
    else:
        print("  ⚠️ No repositories found - you may need to clone them")
    
    # Check Docker images
    try:
        result = run_cmd("docker images --format 'table {{.Repository}}' | grep swe- | wc -l", capture=True)
        image_count = int(result.stdout.strip())
        if image_count > 0:
            print(f"  ✅ Found {image_count} SWE Docker images")
        else:
            print("  ⚠️ No SWE Docker images found - you may need to build them")
    except:
        print("  ⚠️ Could not check Docker images")

def create_config():
    """Create default configuration if missing."""
    if os.path.exists('config.json'):
        print("⚙️ Configuration already exists")
        # Check if NoSkipping field exists, add it if missing
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            # Add NoSkipping field if missing (default to False for backward compatibility)
            if 'NoSkipping' not in config:
                config['NoSkipping'] = False
                with open('config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                print("  ✅ Added NoSkipping field to existing config")
        except Exception as e:
            print(f"  ⚠️ Could not update config with NoSkipping: {e}")
        return
        
    print("⚙️ Creating default configuration...")
    config = {
        "docker_timeout": 300,
        "max_attempts": 10,
        "issue_selection": "0-299",
        "NoSkipping": False,
        "repos": [
            "astropy/astropy",
            "django/django", 
            "matplotlib/matplotlib",
            "mwaskom/seaborn",
            "pallets/flask",
            "psf/requests",
            "pytest-dev/pytest",
            "scikit-learn/scikit-learn",
            "sphinx-doc/sphinx",
            "sympy/sympy",
            "xarray-contrib/xarray",
            "pylint-dev/pylint"
        ]
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("  Created config.json with NoSkipping feature")

def is_first_time_setup():
    """Check if this is the first time setup is being run."""
    # Check for key indicators that setup has been run before
    indicators = [
        'repos',  # Repository directory
        'swe_bench_lite.jsonl',  # Dataset file
        'config.json'  # Config file
    ]
    
    return not all(os.path.exists(indicator) for indicator in indicators)

def main():
    """Main setup routine - automated and safe."""
    print("🚀 SWE-Bench Heavy: Automated Setup")
    print("=" * 50)
    
    first_time = is_first_time_setup()
    
    if first_time:
        print("🆕 First-time setup detected")
        print("This will set up the complete environment")
    else:
        print("🔄 Existing setup detected")
        print("This will only clean run data and refresh configuration")
    
    # Step 1: Ensure Docker works
    check_docker()
    
    # Step 2: Clean run data for fresh testing
    clean_run_data()
    
    # Step 3: Reset state tracking files
    reset_state_files()
    
    # Step 4: Create directories if missing
    ensure_directories()
    
    # Step 5: Download dataset if missing
    download_dataset()
    
    # Step 6: Create config if missing (includes NoSkipping field)
    create_config()
    
    # Step 7: Check valuable assets
    check_assets()
    
    print("\n✅ Setup complete!")
    print("📖 Read instructions.md to get started")
    print("🎯 Run: python3 grading_docker.py <issue_id>")
    print("🎯 Run: python3 select_issues.py '0-10' to select specific issues")
    print("\n💡 This setup preserves all repos/ and Docker images")
    print("💡 Only runs/ and docker_results/ are cleaned for fresh testing")
    print("💡 NoSkipping feature available - set 'NoSkipping': true in config.json")
    
    if first_time:
        print("\n🚨 FIRST TIME SETUP NOTES:")
        print("- You may need to clone repositories: check repos/ directory")
        print("- You may need to build Docker images: check docker images")
        print("- Run 'python3 select_issues.py --help' for issue selection help")
        print("- Set 'NoSkipping': true in config.json to retry same issue until passed")

if __name__ == "__main__":
    main()
