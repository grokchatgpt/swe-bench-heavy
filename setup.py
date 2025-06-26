#!/usr/bin/env python3
"""
SWE-bench Heavy: Automated Setup Script
Downloads dataset and prepares the test environment.
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path


def download_dataset():
    """Download SWE-bench Lite dataset."""
    dataset_file = "swe_bench_lite.jsonl"
    
    if os.path.exists(dataset_file):
        print(f"✅ Dataset {dataset_file} already exists")
        return True
    
    # Try to copy from SWE-bench directory if it exists
    swe_bench_path = "SWE-bench/data/swe_bench_lite.jsonl"
    if os.path.exists(swe_bench_path):
        print(f"Found dataset in SWE-bench directory, copying...")
        try:
            import shutil
            shutil.copy2(swe_bench_path, dataset_file)
            print(f"✅ Dataset copied successfully: {dataset_file}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to copy dataset: {e}")
    
    # Try multiple download URLs
    dataset_urls = [
        "https://github.com/princeton-nlp/SWE-bench/raw/main/data/swe_bench_lite.jsonl",
        "https://raw.githubusercontent.com/princeton-nlp/SWE-bench/main/data/swe_bench_lite.jsonl",
        "https://github.com/princeton-nlp/SWE-bench/releases/download/v1.0.0/swe_bench_lite.jsonl"
    ]
    
    for dataset_url in dataset_urls:
        print(f"Trying to download from {dataset_url}...")
        try:
            urllib.request.urlretrieve(dataset_url, dataset_file)
            print(f"✅ Dataset downloaded successfully: {dataset_file}")
            return True
        except Exception as e:
            print(f"Failed: {e}")
            continue
    
    print("ERROR: Could not download dataset from any source.")
    print("Please manually download swe_bench_lite.jsonl and place it in this directory.")
    print("You can find it at: https://github.com/princeton-nlp/SWE-bench")
    return False


def verify_prerequisites():
    """Check that required tools are available."""
    required_tools = ['git', 'rsync']
    python_tools = ['python3', 'pip3']
    
    # Check for python3 and pip3 specifically
    missing_tools = []
    
    # Check standard tools
    for tool in required_tools:
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)
    
    # Check Python tools specifically
    for tool in python_tools:
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)
    
    if missing_tools:
        print("ERROR: Missing required tools:")
        for tool in missing_tools:
            print(f"- {tool}")
        print("\nPlease install missing tools and run setup again.")
        return False
    
    print("✅ All required tools are available")
    return True


def create_directories():
    """Create necessary directories."""
    directories = [
        'issues',
        'logs',
        'results'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")


def make_scripts_executable():
    """Make Python scripts executable."""
    scripts = [
        'get_next_issue.py',
        'record_progress.py',
        'grading_fast.py',
        'setup.py',
        'cleanup.py'
    ]
    
    for script in scripts:
        if os.path.exists(script):
            os.chmod(script, 0o755)
            print(f"Made executable: {script}")


def validate_dataset():
    """Validate the downloaded dataset."""
    dataset_file = "swe_bench_lite.jsonl"
    
    if not os.path.exists(dataset_file):
        print(f"ERROR: Dataset file {dataset_file} not found")
        return False
    
    try:
        issue_count = 0
        issue_ids = []
        
        with open(dataset_file, 'r') as f:
            for line in f:
                if line.strip():
                    issue = json.loads(line)
                    
                    # Validate required fields
                    required_fields = ['instance_id', 'repo', 'base_commit', 'problem_statement']
                    for field in required_fields:
                        if field not in issue:
                            print(f"ERROR: Missing required field '{field}' in dataset")
                            return False
                    
                    issue_ids.append(issue['instance_id'])
                    issue_count += 1
        
        print(f"✅ Dataset validated: {issue_count} issues found")
        
        # Validate that all repos are pre-downloaded
        print("Validating pre-downloaded repositories...")
        missing_repos = []
        
        for issue_id in issue_ids:
            repo_path = f"repos/{issue_id}"
            if not os.path.exists(repo_path):
                missing_repos.append(issue_id)
            elif not os.path.exists(f"{repo_path}/repo"):
                missing_repos.append(f"{issue_id} (missing repo/ directory)")
        
        if missing_repos:
            print(f"ERROR: Missing {len(missing_repos)} repositories:")
            for repo in missing_repos[:10]:  # Show first 10
                print(f"- {repo}")
            if len(missing_repos) > 10:
                print(f"... and {len(missing_repos) - 10} more")
            print("\nPlease ensure all repositories are downloaded to repos/ directory")
            return False
        
        print(f"✅ All {issue_count} repositories are present in repos/ directory")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to validate dataset: {e}")
        return False


def install_python_dependencies():
    """Install required Python packages with proper environment handling."""
    # Base packages for the benchmark
    base_packages = [
        'pytest',
        'requests',
        'gitpython'
    ]
    
    # Repository-specific packages detected from dataset
    repo_packages = {
        'astropy': ['astropy', 'numpy', 'scipy', 'PyYAML'],
        'scikit-learn': ['scikit-learn', 'numpy', 'scipy', 'pandas', 'joblib'],
        'sympy': ['sympy', 'mpmath'],
        'django': ['Django', 'psycopg2-binary', 'Pillow'],
        'flask': ['Flask', 'Werkzeug', 'Jinja2', 'click'],
        'requests': ['requests', 'urllib3', 'chardet', 'certifi'],
        'matplotlib': ['matplotlib', 'numpy', 'cycler', 'kiwisolver'],
        'pytest': ['pytest', 'pluggy', 'py'],
        'sphinx': ['Sphinx', 'docutils', 'Pygments'],
        'pandas': ['pandas', 'numpy', 'python-dateutil', 'pytz']
    }
    
    # Auto-detect required packages from dataset
    print("Auto-detecting required packages from dataset...")
    required_packages = set(base_packages)
    
    try:
        with open('swe_bench_lite.jsonl', 'r') as f:
            repos_found = set()
            for line in f:
                if line.strip():
                    issue = json.loads(line)
                    repo_name = issue['repo'].split('/')[0]  # Get org name
                    repo_full = issue['repo'].split('/')[1] if '/' in issue['repo'] else repo_name  # Get repo name
                    repos_found.add(repo_name)
                    repos_found.add(repo_full)
            
            print(f"Found repositories: {sorted(repos_found)}")
            
            # Add packages for detected repositories
            for repo in repos_found:
                if repo in repo_packages:
                    required_packages.update(repo_packages[repo])
                    print(f"Added packages for {repo}: {repo_packages[repo]}")
    
    except Exception as e:
        print(f"Warning: Could not auto-detect packages: {e}")
        print("Installing base packages only")
    
    packages = sorted(list(required_packages))
    print(f"Installing {len(packages)} packages: {packages}")
    
    print("Installing Python dependencies...")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("✅ Virtual environment detected")
    else:
        print("⚠️ Not in virtual environment - will try multiple installation methods")
    
    for package in packages:
        success = False
        install_methods = []
        
        if in_venv:
            # In virtual environment - use normal pip
            install_methods.append([sys.executable, '-m', 'pip', 'install', package])
        else:
            # Not in venv - try user install first, then system with break-system-packages
            install_methods.extend([
                [sys.executable, '-m', 'pip', 'install', '--user', package],
                [sys.executable, '-m', 'pip', 'install', '--break-system-packages', package]
            ])
        
        for method in install_methods:
            try:
                result = subprocess.run(method, check=True, capture_output=True, text=True)
                print(f"✅ Installed: {package}")
                success = True
                break
            except subprocess.CalledProcessError as e:
                continue
        
        if not success:
            print(f"⚠️ Could not install {package} - checking if already available...")
            
            # Check if package is available anyway
            try:
                __import__(package.replace('-', '_'))
                print(f"✅ {package} is already available")
            except ImportError:
                print(f"❌ {package} not available")
                print(f"   To fix: Create virtual environment with:")
                print(f"   python3 -m venv swe_venv && source swe_venv/bin/activate && python3 setup.py")


def configure_test_mode():
    """Interactive configuration of test parameters."""
    print("\n" + "="*50)
    print("TEST CONFIGURATION")
    print("="*50)
    
    state_file = "state.json"
    
    # Load current state
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
    else:
        # Default state
        state = {
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
    
    print(f"Current configuration:")
    print(f"- Mode: {state['test_config']['mode']}")
    print(f"- Total issues: {state['test_config']['total_issues']}")
    print(f"- Dataset: {state['test_config']['dataset_file']}")
    
    print("\nTest modes:")
    print("1. ALL - Test all 300 issues")
    print("2. SIZE - Test first N issues")
    print("3. RANGE - Test issues from index M to N")
    print("4. Keep current configuration")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == '1':
        state['test_config']['mode'] = 'ALL'
        state['test_config']['total_issues'] = 300
        state['test_config']['start_index'] = 0
        state['test_config']['end_index'] = 299
    elif choice == '2':
        try:
            n = int(input("Enter number of issues to test: "))
            state['test_config']['mode'] = 'SIZE'
            state['test_config']['total_issues'] = n
            state['test_config']['start_index'] = 0
            state['test_config']['end_index'] = n - 1
        except ValueError:
            print("Invalid number, keeping current configuration")
    elif choice == '3':
        try:
            start = int(input("Enter start index: "))
            end = int(input("Enter end index: "))
            state['test_config']['mode'] = 'RANGE'
            state['test_config']['start_index'] = start
            state['test_config']['end_index'] = end
            state['test_config']['total_issues'] = end - start + 1
        except ValueError:
            print("Invalid range, keeping current configuration")
    
    # Save updated state
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"\n✅ Configuration saved to {state_file}")


def test_setup():
    """Test the setup by running basic commands."""
    print("\n" + "="*50)
    print("TESTING SETUP")
    print("="*50)
    
    # Test get_next_issue.py
    print("Testing issue selection...")
    try:
        result = subprocess.run(['python3', 'get_next_issue.py'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Issue selection works")
        else:
            print(f"❌ Issue selection failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Issue selection test failed: {e}")
    
    # Test record_progress.py
    print("Testing progress recording...")
    try:
        result = subprocess.run([
            'python3', 'record_progress.py', 'test_setup', 'SKIP', 'Setup test'
        ], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Progress recording works")
        else:
            print(f"❌ Progress recording failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Progress recording test failed: {e}")


def main():
    """Main setup process."""
    print("SWE-bench Heavy Setup")
    print("="*50)
    
    # Step 1: Check prerequisites
    if not verify_prerequisites():
        sys.exit(1)
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Download dataset
    if not download_dataset():
        sys.exit(1)
    
    # Step 4: Validate dataset
    if not validate_dataset():
        sys.exit(1)
    
    # Step 5: Install dependencies
    install_python_dependencies()
    
    # Step 6: Make scripts executable
    make_scripts_executable()
    
    # Step 7: Configure test parameters
    configure_test_mode()
    
    # Step 8: Test setup
    test_setup()
    
    print("\n" + "="*50)
    print("SETUP COMPLETE")
    print("="*50)
    print("Your SWE-bench Heavy environment is ready!")
    print("\nNext steps:")
    print("1. For autonomous bot testing:")
    print("   Tell your bot: 'read instructions.md and attempt completion when all issues are resolved'")
    print("2. For manual testing:")
    print("   python3 get_next_issue.py")
    print("3. To reset the environment:")
    print("   python3 cleanup.py")
    print("\nSee install.md for detailed usage instructions.")


if __name__ == "__main__":
    main()
