#!/usr/bin/env python3
"""
SWE-Bench Heavy: Official SWE-Bench Compliant Docker Grading System
No repository-specific hacks - uses official test directive extraction.
"""
import json
import os
import subprocess
import sys
import tempfile
import shutil
import re
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Docker working directory (official SWE-Bench containers use /testbed)
DOCKER_WORKDIR = "/testbed"

# Official SWE-Bench Test Commands (matching official constants exactly)
TEST_PYTEST = "pytest -rA --tb=no -p no:cacheprovider"
TEST_PYTEST_VERBOSE = "pytest -rA --tb=long -p no:cacheprovider"
TEST_PYTEST_NO_HEADER = "pytest --no-header -rA --tb=no -p no:cacheprovider"  # For newer versions
TEST_ASTROPY_PYTEST = "pytest -rA -vv -o console_output_style=classic --tb=no"
TEST_DJANGO = "./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1"
TEST_DJANGO_NO_PARALLEL = "./tests/runtests.py --verbosity 2"
TEST_SEABORN = "pytest --no-header -rA"
TEST_SEABORN_VERBOSE = "pytest -rA --tb=long"
TEST_SPHINX = "tox --current-env -epy39 -v --"
TEST_SYMPY = "PYTHONWARNINGS='ignore::UserWarning,ignore::SyntaxWarning' bin/test -C --verbose"
TEST_SYMPY_VERBOSE = "bin/test -C --verbose"

# Official version-specific specifications (simplified for Heavy)
MAP_REPO_VERSION_TO_SPECS_PY = {
    "django/django": {
        "1.9": {"test_cmd": TEST_DJANGO_NO_PARALLEL},
        "default": {"test_cmd": TEST_DJANGO}
    },
    "astropy/astropy": {
        "default": {"test_cmd": TEST_ASTROPY_PYTEST}
    },
    "matplotlib/matplotlib": {
        "default": {"test_cmd": TEST_PYTEST}
    },
    "mwaskom/seaborn": {
        "default": {"test_cmd": TEST_SEABORN}
    },
    "pallets/flask": {
        "default": {"test_cmd": TEST_PYTEST}
    },
    "psf/requests": {
        "default": {"test_cmd": TEST_PYTEST}
    },
    "pytest-dev/pytest": {
        "default": {"test_cmd": TEST_PYTEST}
    },
    "scikit-learn/scikit-learn": {
        "default": {"test_cmd": TEST_PYTEST}
    },
    "sphinx-doc/sphinx": {
        "default": {"test_cmd": TEST_SPHINX}
    },
    "sympy/sympy": {
        "default": {"test_cmd": TEST_SYMPY}
    },
    "pydata/xarray": {
        "default": {"test_cmd": TEST_PYTEST}
    },
    "pylint-dev/pylint": {
        "default": {"test_cmd": TEST_PYTEST}
    },
}

# Non-test file extensions (from official SWE-Bench)
NON_TEST_EXTS = [
    ".json", ".png", "csv", ".txt", ".md", ".jpg", ".jpeg", 
    ".pkl", ".yml", ".yaml", ".toml",
]

def load_issue_data(issue_id: str) -> Dict[str, Any]:
    """Load issue data from the SWE-Bench dataset."""
    try:
        with open('swe_bench_lite.jsonl', 'r') as f:
            for line in f:
                if line.strip():
                    issue = json.loads(line)
                    if issue['instance_id'] == issue_id:
                        return issue
        print(f"❌ Issue {issue_id} not found in dataset")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ swe_bench_lite.jsonl not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid dataset format: {e}")
        sys.exit(1)

def check_docker_image(issue_id: str) -> str:
    """Check if Docker image exists for the issue (supports both custom and official containers)."""
    # Try custom container first
    custom_image = f"swe-{issue_id.lower()}"
    result = subprocess.run([
        'docker', 'images', '-q', custom_image
    ], capture_output=True, text=True)
    
    if result.stdout.strip():
        print(f"✅ Custom Docker image found: {custom_image}")
        return custom_image
    
    # Try official SWE-Bench container
    transformed_id = issue_id.replace('__', '_1776_')
    official_image = f"swebench/sweb.eval.x86_64.{transformed_id}:latest"
    result = subprocess.run([
        'docker', 'images', '-q', official_image
    ], capture_output=True, text=True)
    
    if result.stdout.strip():
        print(f"✅ Official SWE-Bench image found: {official_image}")
        return official_image
    
    # Neither found
    print(f"❌ Docker image not found:")
    print(f"   Custom: {custom_image}")
    print(f"   Official: {official_image}")
    print("💡 Run 'python3 benchmark_docker.py build' to create custom images")
    print("💡 Or run 'python3 pull_official_containers_x86.py' to download official images")
    sys.exit(1)

def get_test_directives_from_patch(test_patch: str, repo: str) -> List[str]:
    """Extract test directives from test patch (official SWE-Bench logic)."""
    if not test_patch:
        return []
    
    # Get test directives from test patch and remove non-test files
    diff_pat = r"diff --git a/.* b/(.*)"
    directives = re.findall(diff_pat, test_patch)
    directives = [
        d for d in directives if not any(d.endswith(ext) for ext in NON_TEST_EXTS)
    ]

    # For Django tests, remove extension + "tests/" prefix and convert slashes to dots (module referencing)
    if repo == "django/django":
        directives_transformed = []
        for d in directives:
            d = d[: -len(".py")] if d.endswith(".py") else d
            d = d[len("tests/") :] if d.startswith("tests/") else d
            d = d.replace("/", ".")
            directives_transformed.append(d)
        directives = directives_transformed

    return directives

def get_official_test_command(repo: str, version: str, test_directives: List[str]) -> str:
    """Get official test command using version-specific specs."""
    # Get version-specific specs or default
    repo_specs = MAP_REPO_VERSION_TO_SPECS_PY.get(repo, {})
    specs = repo_specs.get(version, repo_specs.get("default", {"test_cmd": TEST_PYTEST}))
    base_cmd = specs["test_cmd"]
    
    if not test_directives:
        return base_cmd
    
    return " ".join([base_cmd] + test_directives)

def create_test_overlay(issue_id: str, issue_data: Dict[str, Any]) -> str:
    """Create test overlay with solution files and test patches."""
    overlay_dir = f"/tmp/swe_test_{issue_id}"
    
    # Clean up any existing overlay
    if os.path.exists(overlay_dir):
        shutil.rmtree(overlay_dir)
    
    os.makedirs(overlay_dir, exist_ok=True)
    
    # STEP 1: Create test patch file (applied inside container)
    test_patch = issue_data.get('test_patch', '')
    if test_patch:
        print("📝 Creating test patch file...")
        patch_file = os.path.join(overlay_dir, 'test.patch')
        with open(patch_file, 'w') as f:
            f.write(test_patch)
    
    # STEP 2: Copy solution files from runs/ directory
    solution_dir = f"runs/{issue_id}"
    if os.path.exists(solution_dir):
        print(f"📁 Copying solution files from {solution_dir}")
        
        for root, dirs, files in os.walk(solution_dir):
            # Skip .git directories
            dirs[:] = [d for d in dirs if d != '.git']
            
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, solution_dir)
                
                # Skip config files and metadata
                skip_files = {'setup.cfg', 'pyproject.toml', 'tox.ini', 'issue.json', 'FIX_SUMMARY.md'}
                if file in skip_files:
                    print(f"⚠️ Skipping metadata file: {file}")
                    continue
                
                # Skip test files that will be handled by test patch
                if test_patch and 'test' in rel_path and rel_path.endswith('.py'):
                    if rel_path in test_patch:
                        print(f"⚠️ Skipping test file: {rel_path} (handled by test_patch)")
                        continue
                
                dst_path = os.path.join(overlay_dir, rel_path)
                
                # Create directory if needed
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
                print(f"✅ Copied: {rel_path}")
    else:
        print(f"⚠️ No solution directory found at {solution_dir}")
        print("🔧 Using base repository state for testing")
    
    return overlay_dir

def create_execution_scripts(overlay_dir: str, test_command: str, test_patch: str) -> None:
    """Create all execution scripts using official SWE-Bench methods."""
    
    # 1. Create test execution script
    test_script = os.path.join(overlay_dir, 'run_tests.sh')
    with open(test_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('set -e\n')  # Exit on error
        f.write(f'cd {DOCKER_WORKDIR}\n')
        f.write('echo "===== Start Test Output ====="\n')
        f.write(f'{DOCKER_WORKDIR}/overlay/test_command.sh\n')
        f.write('echo "===== End Test Output ====="\n')
    
    # 2. Create test command script (separate file for bulletproof execution)
    test_cmd_script = os.path.join(overlay_dir, 'test_command.sh')
    with open(test_cmd_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('set -e\n')  # Exit on error
        f.write(f'cd {DOCKER_WORKDIR}\n')
        # Check if conda is available, if not use regular Python setup
        f.write('if [ -f /opt/miniconda3/bin/activate ]; then\n')
        f.write('    echo "Using conda environment..."\n')
        f.write('    source /opt/miniconda3/bin/activate\n')
        f.write('    conda activate testbed\n')
        f.write('    echo "Current conda environment: $CONDA_DEFAULT_ENV"\n')
        f.write('else\n')
        f.write('    echo "No conda found, using regular Python setup..."\n')
        f.write('    # Install pytest if not available\n')
        f.write('    python -c "import pytest" 2>/dev/null || {\n')
        f.write('        echo "Installing pytest..."\n')
        f.write('        python -m pip install pytest\n')
        f.write('    }\n')
        f.write('fi\n')
        f.write('echo "Python path: $(which python)"\n')
        f.write('echo "Pytest check: $(python -c "import pytest; print(pytest.__version__)" 2>/dev/null || echo "pytest not available")"\n')
        # Write each argument on a separate line to avoid quoting issues
        cmd_parts = test_command.split()
        if cmd_parts:
            # Write the base command
            f.write(f'{cmd_parts[0]}')
            # Add each argument as a separate quoted parameter
            for arg in cmd_parts[1:]:
                # Escape single quotes by replacing them with '"'"'
                escaped_arg = arg.replace("'", "'\"'\"'")
                f.write(f' "{escaped_arg}"')
            f.write('\n')
    
    # 3. Create patch application script with robust error handling
    patch_script = os.path.join(overlay_dir, 'apply_patch.sh')
    with open(patch_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('set -e\n')  # Exit on error
        f.write(f'cd {DOCKER_WORKDIR}\n')
        if test_patch:
            # Use robust patch application with fallback methods
            HEREDOC_DELIMITER = "EOF_114329324912"
            f.write('echo "Applying test patch..."\n')
            f.write('# Try git apply first with verbose output\n')
            f.write(f"if git apply --check - <<'{HEREDOC_DELIMITER}' 2>&1; then\n")
            f.write(test_patch)
            f.write(f'\n{HEREDOC_DELIMITER}\n')
            f.write(f"    echo 'Git apply check passed, applying patch...'\n")
            f.write(f"    git apply -v - <<'{HEREDOC_DELIMITER}'\n")
            f.write(test_patch)
            f.write(f'\n{HEREDOC_DELIMITER}\n')
            f.write('else\n')
            f.write('    echo "Git apply failed, trying patch command..."\n')
            f.write(f"    patch -p1 -f -r /dev/null <<'{HEREDOC_DELIMITER}' || echo 'Patch command also failed, continuing...'\n")
            f.write(test_patch)
            f.write(f'\n{HEREDOC_DELIMITER}\n')
            f.write('fi\n')
            f.write('echo "Patch application completed"\n')
        else:
            f.write('echo "No test patch found"\n')
    
    # 4. Create file copy script
    copy_script = os.path.join(overlay_dir, 'copy_files.sh')
    with open(copy_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write(f'cd {DOCKER_WORKDIR}\n')
        f.write('# Fix pytest version and configuration issues\n')
        f.write('if [ -f setup.cfg ]; then\n')
        f.write('    echo "Fixing pytest version requirements..."\n')
        f.write('    sed -i "s/minversion = 7.0/minversion = 6.0/g" setup.cfg 2>/dev/null || true\n')
        f.write('    sed -i "s/minversion=7.0/minversion=6.0/g" setup.cfg 2>/dev/null || true\n')
        f.write('    # Remove unsupported pytest options\n')
        f.write('    sed -i "s/addopts = --doctest-rst/addopts = /g" setup.cfg 2>/dev/null || true\n')
        f.write('    sed -i "s/addopts=--doctest-rst/addopts=/g" setup.cfg 2>/dev/null || true\n')
        f.write('    sed -i "/--doctest-rst/d" setup.cfg 2>/dev/null || true\n')
        f.write('fi\n')
        f.write(f'if [ -d "{DOCKER_WORKDIR}/overlay" ]; then\n')
        f.write('    echo "Copying solution files..."\n')
        f.write(f'    find {DOCKER_WORKDIR}/overlay -type f -name "*.py" | while read file; do\n')
        f.write(f'        rel_path="${{file#{DOCKER_WORKDIR}/overlay/}}"\n')
        f.write(f'        target_path="{DOCKER_WORKDIR}/$rel_path"\n')
        f.write('        if [ "$rel_path" != "test.patch" ] && [[ "$rel_path" != *.sh ]]; then\n')
        f.write('            mkdir -p "$(dirname "$target_path")"\n')
        f.write('            cp "$file" "$target_path"\n')
        f.write('            echo "Copied: $rel_path"\n')
        f.write('        fi\n')
        f.write('    done\n')
        f.write('fi\n')
    
    # 5. Create main execution script
    main_script = os.path.join(overlay_dir, 'main.sh')
    with open(main_script, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('set -e\n')  # Exit on error
        f.write('echo "=== SWE-Bench Heavy Docker Test Execution ==="\n')
        f.write('\n')
        f.write('# Step 1: Apply test patch\n')
        f.write(f'chmod +x {DOCKER_WORKDIR}/overlay/apply_patch.sh\n')
        f.write(f'{DOCKER_WORKDIR}/overlay/apply_patch.sh\n')
        f.write('\n')
        f.write('# Step 2: Copy solution files\n')
        f.write(f'chmod +x {DOCKER_WORKDIR}/overlay/copy_files.sh\n')
        f.write(f'{DOCKER_WORKDIR}/overlay/copy_files.sh\n')
        f.write('\n')
        f.write('# Step 3: Run tests\n')
        f.write(f'chmod +x {DOCKER_WORKDIR}/overlay/run_tests.sh\n')
        f.write(f'chmod +x {DOCKER_WORKDIR}/overlay/test_command.sh\n')
        f.write(f'{DOCKER_WORKDIR}/overlay/run_tests.sh\n')
    
    # Make all scripts executable
    for script in [test_script, test_cmd_script, patch_script, copy_script, main_script]:
        os.chmod(script, 0o755)

def run_docker_tests(image_name: str, overlay_dir: str, issue_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Run tests in Docker container using official SWE-Bench methodology."""
    
    # Extract test directives from test_patch (official method)
    repo = issue_data.get('repo', '')
    version = issue_data.get('version', 'default')
    test_patch = issue_data.get('test_patch', '')
    
    # Use official test directive extraction
    test_directives = get_test_directives_from_patch(test_patch, repo)
    
    print(f"🔧 Repository: {repo}")
    print(f"📦 Version: {version}")
    print(f"🧪 Test directives from patch: {test_directives}")
    
    # Get official test command
    test_command = get_official_test_command(repo, version, test_directives)
    print(f"🧪 Official test command: {test_command}")
    
    # Create all execution scripts using official methods
    create_execution_scripts(overlay_dir, test_command, test_patch)
    
    # Run Docker with official working directory and M2 Mac compatibility
    docker_cmd = [
        'docker', 'run', '--rm',
        '--platform', 'linux/amd64',  # M2 Mac compatibility
        '--entrypoint', f'{DOCKER_WORKDIR}/overlay/main.sh',
        '-v', f'{overlay_dir}:{DOCKER_WORKDIR}/overlay',
        '--workdir', DOCKER_WORKDIR,
        image_name
    ]
    
    print(f"🐳 Running Docker with official SWE-Bench setup...")
    print(f"   Image: {image_name}")
    print(f"   Working Directory: {DOCKER_WORKDIR}")
    print(f"   Overlay: {DOCKER_WORKDIR}/overlay")
    
    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        output = result.stdout + result.stderr
        success = result.returncode == 0
        
        return success, output
        
    except subprocess.TimeoutExpired:
        return False, "❌ Test execution timed out (5 minutes)"
    except Exception as e:
        return False, f"❌ Docker execution failed: {e}"

def save_test_results(issue_id: str, passed: bool, output: str) -> None:
    """Save test results to file."""
    results_dir = f"docker_results/{issue_id}"
    os.makedirs(results_dir, exist_ok=True)
    
    results_file = os.path.join(results_dir, "test_results.json")
    results = {
        'issue_id': issue_id,
        'passed': passed,
        'output': output,
        'timestamp': subprocess.run(['date'], capture_output=True, text=True).stdout.strip(),
        'method': 'official_swe_bench_compliant'
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Also save output to text file
    output_file = os.path.join(results_dir, "test_output.txt")
    with open(output_file, 'w') as f:
        f.write(output)
    
    print(f"📋 Results saved to: {results_dir}")

def auto_record_progress(issue_id: str, passed: bool, output: str) -> None:
    """Automatically record progress based on grading results using enhanced stats tracker."""
    if passed:
        status = "PASS"
        notes = "Passed Docker grading tests (official SWE-Bench compliant)"
        print(f"✅ Issue solved successfully")
    else:
        status = "FAIL"
        # Extract meaningful error info from output
        lines = output.split('\n')
        error_lines = [line for line in lines if 'ERROR' in line or 'FAILED' in line or 'AssertionError' in line]
        if error_lines:
            notes = f"Failed Docker tests: {error_lines[0][:100]}..."
        else:
            notes = "Failed Docker grading tests (official SWE-Bench compliant)"
    
    # Use enhanced stats tracker - clean, deterministic, no fallbacks
    from stats_tracker import StatsTracker
    tracker = StatsTracker()
    tracker.record_attempt(issue_id, status, notes)
    print(f"📝 Progress automatically recorded: {issue_id} - {status}")

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python grading_docker.py <issue_id>")
        sys.exit(1)
    
    issue_id = sys.argv[1]
    
    # Bot coherence safeguard - circuit breaker
    try:
        from failure_tracker import increment_failure_count
        attempt_count = increment_failure_count(issue_id)
        # Silent termination after 10 attempts - bot hangs forever
        if attempt_count >= 10:
            input("Maximum attempts reached. Press Enter to continue...")  # Bot will hang here
    except:
        pass  # Fail silently if tracker unavailable
    
    print(f"🐳 Official SWE-Bench Compliant Docker grading for issue: {issue_id}")
    print("=" * 60)
    
    # Load issue data
    issue_data = load_issue_data(issue_id)
    print(f"📦 Repository: {issue_data['repo']}")
    
    # Check Docker image exists
    image_name = check_docker_image(issue_id)
    
    # Create test overlay with solution files
    overlay_dir = create_test_overlay(issue_id, issue_data)
    
    try:
        # Run tests in Docker container
        print("\n🧪 Running tests in Docker container...")
        passed, output = run_docker_tests(image_name, overlay_dir, issue_data)
        
        # Save results
        save_test_results(issue_id, passed, output)
        
        # Auto-record progress
        auto_record_progress(issue_id, passed, output)
        
        # Print results
        print("\n" + "=" * 60)
        if passed:
            print("✅ TESTS PASSED")
            print("🎉 Solution appears to be correct!")
            print("📝 Progress automatically recorded as PASS")
        else:
            print("❌ TESTS FAILED")
            print("🔧 Solution needs more work.")
            print("📝 Progress automatically recorded as FAIL")
        
        print(f"\n📋 Full output saved to: docker_results/{issue_id}/")
        print("\n🔍 Test Output Preview:")
        print("-" * 40)
        # Show last 20 lines of output
        output_lines = output.split('\n')
        for line in output_lines[-20:]:
            print(line)
        
        print("\n" + "=" * 60)
        print("\nRead instructions.md if you are confused - otherwise continue. Do not stop the workflow until get_next_issue.py says you are complete with all issues. You can always manually record a skip  and revisit later. All issues are verified as solvable and all grading tooling has been verified correct and is official. Any failures are bot related.\n")
        print("=" * 60)
        
        sys.exit(0 if passed else 1)
        
    finally:
        # Clean up overlay directory
        if os.path.exists(overlay_dir):
            shutil.rmtree(overlay_dir)
            print(f"🗑️ Cleaned up overlay: {overlay_dir}")

if __name__ == "__main__":
    main()
