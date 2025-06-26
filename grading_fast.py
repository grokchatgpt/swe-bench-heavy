#!/usr/bin/env python3
"""
SWE-bench Heavy: Fast Grading Tool
Runs only the specific tests mentioned in FAIL_TO_PASS and PASS_TO_PASS for quick validation.
"""
import json
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple


def load_issue_data(issue_id: str) -> Dict[str, Any]:
    """Load issue data from the issues directory."""
    issue_file = f"issues/{issue_id}/issue.json"
    if not os.path.exists(issue_file):
        print(f"ERROR: Issue data not found: {issue_file}")
        sys.exit(1)
    
    with open(issue_file, 'r') as f:
        return json.load(f)


def setup_test_environment(issue_data: Dict[str, Any], issue_id: str) -> str:
    """Set up isolated test environment for the issue."""
    repo_name = issue_data['repo']
    base_commit = issue_data['base_commit']
    
    # Use pre-downloaded repository from runs/ directory
    source_repo_dir = f"repos/{issue_id}/repo"
    if not os.path.exists(source_repo_dir):
        print(f"ERROR: Pre-downloaded repository not found: {source_repo_dir}")
        print("Make sure repositories are in repos/ directory")
        sys.exit(1)
    
    # Create test environment directory
    test_env_dir = f"issues/{issue_id}/test_env"
    if os.path.exists(test_env_dir):
        shutil.rmtree(test_env_dir)
    
    print(f"Setting up test environment for {repo_name}...")
    try:
        # Copy the pre-downloaded repository
        shutil.copytree(source_repo_dir, test_env_dir)
        print(f"Test environment ready")
    except Exception as e:
        print(f"ERROR: Failed to setup test environment: {e}")
        sys.exit(1)
    
    return test_env_dir


def apply_test_patch(test_env_dir: str, issue_data: Dict[str, Any]) -> bool:
    """Apply the test patch to create the test cases."""
    test_patch = issue_data.get('test_patch', '')
    if not test_patch:
        print("WARNING: No test patch available")
        return False
    
    # Write patch to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(test_patch)
        patch_file = f.name
    
    try:
        # Apply patch
        result = subprocess.run([
            'git', 'apply', '--verbose', patch_file
        ], cwd=test_env_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"WARNING: Test patch application failed: {result.stderr}")
            return False
        
        print("Test patch applied successfully")
        return True
    except Exception as e:
        print(f"ERROR: Failed to apply test patch: {e}")
        return False
    finally:
        os.unlink(patch_file)


def copy_solution_files(test_env_dir: str, issue_id: str) -> None:
    """Copy solution files from the working directory to test environment."""
    work_dir = f"runs/{issue_id}"
    
    # If no solution directory exists, create it from the pre-downloaded repo
    if not os.path.exists(work_dir):
        print(f"No solution directory found, creating from pre-downloaded repo...")
        source_repo_dir = f"repos/{issue_id}/repo"
        if not os.path.exists(source_repo_dir):
            print(f"ERROR: Pre-downloaded repository not found: {source_repo_dir}")
            sys.exit(1)
        
        # Create the issues directory structure
        os.makedirs(f"issues/{issue_id}", exist_ok=True)
        
        # Copy the pre-downloaded repo to the work directory
        shutil.copytree(source_repo_dir, work_dir)
        print(f"Work directory created: {work_dir}")
    
    # Copy all files from work directory to test environment (this will be the same initially)
    try:
        # Use rsync to copy files, preserving structure
        subprocess.run([
            'rsync', '-av', '--exclude=.git', f"{work_dir}/", f"{test_env_dir}/"
        ], check=True, capture_output=True, text=True)
        print("Solution files copied to test environment")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to copy solution files: {e}")
        sys.exit(1)


def run_specific_tests(test_env_dir: str, issue_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Run only the specific tests mentioned in FAIL_TO_PASS and PASS_TO_PASS."""
    try:
        # Install package if setup.py exists
        setup_py = os.path.join(test_env_dir, 'setup.py')
        if os.path.exists(setup_py):
            print("Installing package...")
            subprocess.run([
                'pip', 'install', '-e', '.'
            ], cwd=test_env_dir, check=True, capture_output=True, text=True)
        
        # Get specific tests to run
        fail_to_pass = issue_data.get('FAIL_TO_PASS', [])
        pass_to_pass = issue_data.get('PASS_TO_PASS', [])
        
        all_tests = []
        # Handle both string and list formats
        if isinstance(fail_to_pass, str):
            # Parse string format like '["test_prefix_operations"]'
            import ast
            try:
                fail_to_pass = ast.literal_eval(fail_to_pass)
            except:
                fail_to_pass = [fail_to_pass] if fail_to_pass else []
        if isinstance(pass_to_pass, str):
            try:
                pass_to_pass = ast.literal_eval(pass_to_pass)
            except:
                pass_to_pass = [pass_to_pass] if pass_to_pass else []
                
        if isinstance(fail_to_pass, list):
            all_tests.extend(fail_to_pass)
        if isinstance(pass_to_pass, list):
            all_tests.extend(pass_to_pass)
        
        if not all_tests:
            print("No specific tests found, running generic test discovery...")
            result = subprocess.run([
                'python', '-m', 'pytest', '-xvs', '--tb=short'
            ], cwd=test_env_dir, capture_output=True, text=True, timeout=120)
            return result.returncode == 0, result.stdout + result.stderr
        
        print(f"Running specific tests: {all_tests}")
        
        # For sympy, run the specific test file
        if 'sympy' in issue_data.get('repo', '').lower():
            # Look for test_prefix_operations in the test names
            if any('test_prefix' in test for test in all_tests):
                test_file = 'sympy/physics/units/tests/test_prefixes.py'
                cmd = ['python', '-m', 'pytest', '-xvs', test_file, '--tb=short']
            else:
                # Use test name filtering
                test_names = [t.split('.')[-1] if '.' in t else t for t in all_tests]
                cmd = ['python', '-m', 'pytest', '-xvs', '-k', ' or '.join(test_names), '--tb=short']
        else:
            # Generic approach - run tests by name
            test_names = [t.split('.')[-1] if '.' in t else t for t in all_tests]
            cmd = ['python', '-m', 'pytest', '-xvs', '-k', ' or '.join(test_names), '--tb=short']
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, cwd=test_env_dir, capture_output=True, text=True, timeout=120
        )
        
        return result.returncode == 0, result.stdout + result.stderr
        
    except subprocess.TimeoutExpired:
        return False, "Test execution timed out"
    except Exception as e:
        return False, f"Test execution failed: {e}"


def save_test_results(issue_id: str, passed: bool, output: str) -> None:
    """Save test results to file."""
    results_dir = f"issues/{issue_id}"
    results_file = os.path.join(results_dir, "test_results.json")
    
    results = {
        'issue_id': issue_id,
        'passed': passed,
        'output': output,
        'timestamp': subprocess.run(['date'], capture_output=True, text=True).stdout.strip()
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also save output to text file
    output_file = os.path.join(results_dir, "test_output.txt")
    with open(output_file, 'w') as f:
        f.write(output)


def auto_record_progress(issue_id: str, passed: bool, output: str) -> None:
    """Automatically record progress based on grading results."""
    try:
        if passed:
            status = "PASS"
            notes = "Passed official grading tests"
        else:
            status = "FAIL"
            # Extract meaningful error info from output
            lines = output.split('\n')
            error_lines = [line for line in lines if 'ERROR' in line or 'FAILED' in line or 'AssertionError' in line]
            if error_lines:
                notes = f"Failed official tests: {error_lines[0][:100]}..."
            else:
                notes = "Failed official grading tests"
        
        # Call record_progress.py to update state
        result = subprocess.run([
            sys.executable, 'record_progress.py', issue_id, status, notes
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"📝 Progress automatically recorded: {issue_id} - {status}")
        else:
            print(f"⚠️ Failed to record progress: {result.stderr}")
    
    except Exception as e:
        print(f"⚠️ Failed to auto-record progress: {e}")


def create_issue_metadata(issue_data: Dict[str, Any], issue_id: str) -> None:
    """Create issue.json file from dataset if missing."""
    issue_dir = f"issues/{issue_id}"
    issue_file = f"{issue_dir}/issue.json"
    
    if not os.path.exists(issue_file):
        os.makedirs(issue_dir, exist_ok=True)
        
        # Create issue metadata from dataset
        issue_metadata = {
            'instance_id': issue_data['instance_id'],
            'repo': issue_data['repo'],
            'base_commit': issue_data['base_commit'],
            'problem_statement': issue_data['problem_statement'],
            'FAIL_TO_PASS': issue_data.get('FAIL_TO_PASS', []),
            'PASS_TO_PASS': issue_data.get('PASS_TO_PASS', []),
            'test_patch': issue_data.get('test_patch', ''),
            'patch': issue_data.get('patch', ''),
            'created_at': subprocess.run(['date', '-Iseconds'], capture_output=True, text=True).stdout.strip()
        }
        
        with open(issue_file, 'w') as f:
            json.dump(issue_metadata, f, indent=2)
        
        print(f"Created issue metadata: {issue_file}")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python grading_fast.py <issue_id>")
        sys.exit(1)
    
    issue_id = sys.argv[1]
    
    # Load issue data from dataset
    try:
        with open('swe_bench_lite.jsonl', 'r') as f:
            issue_data = None
            for line in f:
                if line.strip():
                    issue = json.loads(line)
                    if issue['instance_id'] == issue_id:
                        issue_data = issue
                        break
            
            if not issue_data:
                print(f"ERROR: Issue {issue_id} not found in dataset")
                sys.exit(1)
    
    except FileNotFoundError:
        print("ERROR: swe_bench_lite.jsonl not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid dataset format: {e}")
        sys.exit(1)
    
    print(f"Fast grading for issue: {issue_id}")
    print(f"Repository: {issue_data['repo']}")
    
    # Create issue metadata if missing
    create_issue_metadata(issue_data, issue_id)
    
    # Set up test environment
    test_env_dir = setup_test_environment(issue_data, issue_id)
    
    # Apply test patch (creates the test cases)
    patch_applied = apply_test_patch(test_env_dir, issue_data)
    if not patch_applied:
        print("WARNING: Proceeding without test patch")
    
    # Copy solution files
    copy_solution_files(test_env_dir, issue_id)
    
    # Run specific tests
    print("Running specific tests...")
    passed, output = run_specific_tests(test_env_dir, issue_data)
    
    # Save results
    save_test_results(issue_id, passed, output)
    
    # Automatically record progress
    auto_record_progress(issue_id, passed, output)
    
    # Print results
    if passed:
        print("✅ TESTS PASSED")
        print("Solution appears to be correct!")
        print("✅ Progress automatically recorded as PASS")
    else:
        print("❌ TESTS FAILED")
        print("Solution needs more work.")
        print("📝 Progress automatically recorded as FAIL")
    
    print("\nTest Output:")
    print(output)
    
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
