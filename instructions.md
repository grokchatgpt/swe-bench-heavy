# SWE-Bench Heavy: Autonomous Issue Solving

## Mission
You are an autonomous AI coder solving GitHub issues from SWE-bench Lite dataset. Fix as many issues as possible using the **Docker-based tooling** provided. No repo cloning, no dependency issues, no bullshit - just pure problem solving.

## Why "Heavy"?
SWE-Bench Heavy eliminates performance aids (RAG, BM25 retrieval, Oracle hints) that require complex setup. You get 300 verified bugs across 12 codebases with nothing but essential tools. 

The challenge: resolve as many as possible autonomously with sustained coherence across multiple issues in a single session. The human has selected an unknown number of issues from the 300 issue problem set - solve the unknown number of issues until the tooling notifies you the test is complete.

## 🚀 Bot Workflow (Start Here)

### 1. Get Next Issue 
```bash
python3 get_next_issue.py
```
Returns issue ID like `astropy__astropy-12907` with **COMPLETE** problem details including:
- **Problem Statement**: Full description of what's broken
- **FAIL_TO_PASS Tests**: Tests that must start passing  
- **PASS_TO_PASS Tests**: Tests that must continue passing
- **Repository/Commit Info**: Which codebase and base commit

**CRITICAL**: This output contains ALL the information you need - don't look for `issue.json` files that don't exist yet!

### 2. **Create Work Directory**
```bash
mkdir -p runs/<issue_id>
```
The `get_next_issue.py` tool mentions it creates directories, but **create it explicitly** to avoid fumbling.

### 3. **CRITICAL: Extract Original Files FIRST** 
Before making ANY changes, extract the complete original files from Docker containers:

## 🐳 **CORRECTED DOCKER CONTAINER STRUCTURE**

**CRITICAL**: SWE-Bench containers are **development environments** with source code at `/testbed/`, NOT production site-packages installations!

### **Container Discovery Pattern**
```bash
# 1. ALWAYS find the actual Docker image name for your issue FIRST
docker images | grep <repo_name>
# This reveals the true image name with swebench/ prefix and version numbers

# 2. Discover container structure with the ACTUAL image name
docker run --rm --entrypoint bash <actual_image_name> -c "pwd && ls -la"
# This will show you're in /testbed with the source code

# 3. Extract source files from /testbed/, NOT site-packages
docker run --rm --entrypoint cat <actual_image_name> /testbed/<relative_path> > runs/<issue_id>/<relative_path>
```

### **File Extraction Examples**

**IMPORTANT**: The image names below are EXAMPLES. You MUST use `docker images | grep <repo>` to find your actual image names!

```bash
# Example discovery workflow:
docker images | grep astropy
# Returns: swebench/sweb.eval.x86_64.astropy_1776_astropy-12907

# Then extract with ACTUAL image name:
docker run --rm --entrypoint cat swebench/sweb.eval.x86_64.astropy_1776_astropy-12907:latest /testbed/astropy/modeling/separable.py > runs/astropy__astropy-12907/astropy/modeling/separable.py
```

**Real Image Name Patterns** (you'll discover these with `docker images`):
```bash
# 1. Astropy - Astronomy library
swebench/sweb.eval.x86_64.astropy_1776_astropy-12907:latest

# 2. Django - Web framework  
swebench/sweb.eval.x86_64.django_1776_django-11422:latest

# 3. Matplotlib - Plotting library
swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-18869:latest

# 4. Seaborn - Statistical visualization
swebench/sweb.eval.x86_64.mwaskom_1776_seaborn-2389:latest

# 5. Flask - Micro web framework
swebench/sweb.eval.x86_64.pallets_1776_flask-4045:latest

# 6. Requests - HTTP library
swebench/sweb.eval.x86_64.psf_1776_requests-2317:latest

# 7. Pytest - Testing framework
swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-5692:latest

# 8. Scikit-learn - Machine learning
swebench/sweb.eval.x86_64.scikit-learn_1776_scikit-learn-13779:latest

# 9. Sphinx - Documentation generator
swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-8713:latest

# 10. SymPy - Symbolic mathematics
swebench/sweb.eval.x86_64.sympy_1776_sympy-18057:latest

# 11. Xarray - N-dimensional arrays
swebench/sweb.eval.x86_64.pydata_1776_xarray-4094:latest

# 12. Pylint - Code analysis
swebench/sweb.eval.x86_64.pylint-dev_1776_pylint-2906:latest
```

**Key Pattern**: `swebench/sweb.eval.x86_64.<repo>_<version>_<repo>-<issue_number>:latest`

### **Essential Docker Discovery Commands**

```bash
# Step 1: Find your exact image name
docker images | grep <repo_name>

# Step 2: Discover container working directory and structure
docker run --rm --entrypoint bash <actual_image_name> -c "pwd && ls -la"

# Step 3: Find specific files in the testbed
docker run --rm --entrypoint find <actual_image_name> /testbed -name "<filename>.py" -type f

# Step 4: List testbed directory structure  
docker run --rm --entrypoint bash <actual_image_name> -c "find /testbed -type f -name '*.py' | head -20"

# Step 5: Check if file exists before extracting
docker run --rm --entrypoint test <actual_image_name> -f /testbed/<path> && echo "EXISTS" || echo "NOT FOUND"
```

### **Platform Warnings (SAFE TO IGNORE)**
You may see this warning - it's harmless (ARM M2 native, Docker is emulating x86/64):
```
WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8)
```
This is just a platform mismatch warning. The containers work fine despite this warning.

**Why This Matters**: You need the COMPLETE original file structure, not just the parts you think you need. Missing imports, classes, or dependencies will cause failures.

### 4. Develop Solution
Create your fix in `runs/<issue_id>/`:
```
runs/astropy__astropy-12907/
├── astropy/
│   ├── modeling/
│   │   └── separable.py    # Your code fixes
│   └── other_files.py

```

### 5. Test Solution
```bash
python3 grading_docker.py astropy__astropy-12907
```
**Instant Results**: PASS/FAIL with detailed output. Progress automatically recorded.
- If your solution is a PASS, document it your runs directory:
```
runs/astropy__astropy-12907/
└── FIX_SUMMARY.md         # Document your solution
```

### 6. Iterate
- **PASS**: Get next issue with `python3 get_next_issue.py` and go back to 1
- **FAIL**: Analyze output, refine solution, test again

### 7. Attempt Completion
- Continue resolving issues until get_next_issue.py says you are 100% complete with testing - "CONGRATULATIONS"

## 🐳 Docker-First Architecture

### Why Docker
- **Zero Setup**: All 300 issues have pre-built containers ready
- **Zero Conflicts**: Pristine environments, no dependency hell
- **Zero Compromise**: Matches official SWE-Bench evaluation exactly
- **Zero Bullshit**: 5-minute timeout, circuit breaker protection

### How Docker Testing Works
1. **Pristine Container**: Starts with exact repository state at base commit from `/testbed/`
2. **Test Patch Applied**: Adds new test cases to base repository
3. **Your Solution Overlaid**: Your files from `runs/<issue_id>/` copied into `/testbed/`
4. **Tests Executed**: Official SWE-Bench test cases run
5. **Results Returned**: PASS/FAIL with detailed output

**No repo cloning needed** - containers have source code at `/testbed/`.

## 🛠️ Complete Tool Reference

### Core Workflow Tools

```bash 
python3 get_next_issue.py           # Get next issue to work on
python3 grading_docker.py <id>      # Test your solution
```

## 📊 Supported Repositories (12 Total)

1. **astropy/astropy** - Astronomy library
2. **django/django** - Web framework  
3. **matplotlib/matplotlib** - Plotting library
4. **mwaskom/seaborn** - Statistical visualization
5. **pallets/flask** - Micro web framework
6. **psf/requests** - HTTP library
7. **pytest-dev/pytest** - Testing framework
8. **scikit-learn/scikit-learn** - Machine learning
9. **sphinx-doc/sphinx** - Documentation generator
10. **sympy/sympy** - Symbolic mathematics
11. **pydata/xarray** - N-dimensional arrays
12. **pylint-dev/pylint** - Code analysis

## 🎯 Solution Development

### File Structure
Only create files you actually modify:
```
runs/<issue_id>/
├── <repo_structure>/
│   └── modified_file.py    # Your fixes
├── new_file.py            # Any new files needed
└── FIX_SUMMARY.md         # Document your approach - always document previous issue before getting a new issue
```

### Key Principles
- **Minimal Changes**: Only modify what's necessary
- **Follow Patterns**: Study existing codebase conventions
- **Test-Driven**: Let failing tests guide your solution
- **Document**: Explain your approach in FIX_SUMMARY.md

### Understanding Issues
Each issue provides:
- **Problem Statement**: What's broken and needs fixing
- **FAIL_TO_PASS Tests**: Tests that must start passing
- **PASS_TO_PASS Tests**: Existing tests that must stay passing
- **Repository Context**: Which codebase and base commit

## 🔒 Safety & Protection

### Asset Protection  
- **Docker images preserved**: All containers safe
- **Repository clones preserved**: `/testbed/` directory in containers untouched
- **Only run data cleaned**: `runs/` and `docker_results/` reset for fresh testing

### Error Handling
- **5-minute timeout** prevents runaway processes
- **Graceful container cleanup** after each test
- **Comprehensive validation** of all inputs
- **Detailed error reporting** for debugging

## ⚠️ CRITICAL: Terminal Safety Rules

### NEVER Use These Commands (Will Hang Terminal)
```bash
# ❌ FORBIDDEN - These will break testing:
docker run ... << 'EOF'     # Heredoc syntax hangs terminal
docker run ... -c "cat > file << 'EOF'"  # Nested heredoc breaks
docker run ... bash -c 'print("...'     # Unclosed quotes hang
```

### ✅ Safe Docker Commands Only
```bash
# ✅ SAFE - Use these patterns:
docker run --rm --entrypoint cat <image> <file>           # Extract files
docker run --rm --entrypoint python <image> -c "code"     # Run Python
docker run --rm --entrypoint bash <image> -c "command"    # Run shell commands
```

### Debug Rules
- **Use simple commands**: Single-line Docker commands only
- **No interactive shells**: Never use `docker run -it` 
- **No heredocs**: Never use `<< 'EOF'` syntax in Docker commands
- **Test commands first**: Verify Docker syntax before execution
- **Immediate failure**: If terminal hangs, test is cancelled

## 📈 Progress Tracking

### Automatic Tracking
- **state.json**: Machine-readable progress state
- **progress.md**: Human-readable progress summary  
- **failure_tracker.json**: Attempt counting per issue
- **docker_results/**: Detailed test outputs saved

### Manual Control
```bash
# Check current status if resuming an interrupted session
cat progress.md
```

## 🏆 Success Strategies

### Debug Effectively
- **Test output**: `docker_results/<issue_id>/test_output.txt`
- **Issue details**: From `get_next_issue.py` output (already provided)
- **Docker logs**: If needed

## ⚡ ANTI-FUMBLING: Efficiency Guidelines

### 🚫 NEVER Do These (Token Wasters)
1. **Blind File Exploration**: Don't use `list_files` to hunt for files - extract from Docker `/testbed/` first
2. **Wrong Path Assumptions**: Don't assume site-packages - source code is at `/testbed/`
3. **Multiple Failed `replace_in_file` Attempts**: If you fail twice, switch to `write_to_file`
4. **Searching for Missing Classes**: Extract the complete original file from `/testbed/` to see ALL dependencies
5. **Guessing File Paths**: Use Docker commands to find exact paths in `/testbed/`
6. **Wrong Image Names**: ALWAYS use `docker images | grep <repo>` to find actual image names first
7. **🚨 CRITICAL: Using `write_to_file` on Large Files**: Never use `write_to_file` on files >800 lines - it will truncate due to output window limits

### ✅ ALWAYS Do These (Efficiency Patterns)
1. **Discover Image Name First**: `docker images | grep <repo_name>`
2. **Discover Container Structure**: `docker run --rm --entrypoint bash <actual_image> -c "pwd && ls -la"`
3. **Extract Complete Files from /testbed/**: `docker run --rm --entrypoint cat <actual_image> /testbed/<path> > runs/<issue_id>/<path>`
4. **Use get_next_issue.py Output**: All issue details already provided - no need to hunt for files
5. **Use `write_to_file` for Complex Changes**: When modifying > 200 lines of a file
6. **Follow the Patch Template**: The `patch` field shows you exactly what to implement
7. **Test Early and Often**: Don't build complex solutions without testing
8. **🔧 LARGE FILE WORKAROUND**: For files >800 lines: Extract to temp file, use `replace_in_file` on temp, then `cp` to final location

### 🔧 Large File Modification Strategy
When dealing with files >800 lines that would truncate with `write_to_file`:

```bash
# Step 1: Extract original file to a working copy
docker run --rm --entrypoint cat <image> /testbed/<path> > runs/<issue_id>/temp_<filename>

# Step 2: Use replace_in_file on the working copy for targeted changes
# This avoids output window limits since you're only changing specific sections

# Step 3: Copy the modified file to the correct location
cp runs/<issue_id>/temp_<filename> runs/<issue_id>/<correct_path>

# Example from django__django-10924:
docker run --rm --entrypoint cat <image> /testbed/django/db/models/fields/__init__.py > runs/django__django-10924/complete_fields_init.py
# Then use replace_in_file on complete_fields_init.py 
cp runs/django__django-10924/complete_fields_init.py runs/django__django-10924/django/db/models/fields/__init__.py
```

**Why This Works**: 
- Avoids `write_to_file` truncation on large files
- `replace_in_file` only outputs the changed sections 
- Preserves complete file structure and all dependencies
- Much faster than recreating entire files

### 🎯 Optimal Workflow Pattern
```bash
# 1. Get issue  
python3 get_next_issue.py

# 2. Find actual Docker image name
docker images | grep <repo_name>

# 3. Discover container structure
docker run --rm --entrypoint bash <actual_image_name> -c "pwd && ls -la"

# 4. Extract original file(s) from /testbed/ IMMEDIATELY
docker run --rm --entrypoint cat <actual_image_name> /testbed/<path> > runs/<issue_id>/<path>

# 5. Analyze issue details (already provided by get_next_issue.py)
# No need to read files - all details already in memory

# 6. Implement the exact changes shown in the patch
# Use write_to_file for complete file replacement

# 7. Test immediately
python3 grading_docker.py <issue_id>

# 8. If FAIL, analyze test output and debug
# If PASS, move to next issue
```

## 🎯 Autonomous Operation

You have complete autonomy to:
- **Develop your approach**: No prescribed methodology

**Focus on what matters**: Understanding problems and implementing solutions. The tooling handles everything else.


## 🚀 Ready to Start?

```bash
# 1. Get your first issue
python3 get_next_issue.py

# 2. Find the actual Docker image name
docker images | grep <repo_name>

# 3. Discover container structure and extract files from /testbed/
docker run --rm --entrypoint bash <actual_image_name> -c "pwd && ls -la"
docker run --rm --entrypoint cat <actual_image_name> /testbed/<path> > runs/<issue_id>/<path>

# 4. Test your solution
python3 grading_docker.py <issue_id>

# 5. Iterate until PASS, then repeat!
```

NOTE: Always do fix summary before calling get_next_issue.py.

**Continue workflow until all issues are passed - Do not stop until get_next_issue.py prints "CONGRATULATIONS you have solved ALL issues" 🎯**
