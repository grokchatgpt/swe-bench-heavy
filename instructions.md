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
Returns issue ID like `astropy__astropy-12907` with full problem details.

### 4. Develop Solution
Create your fix in `runs/<issue_id>/`:
```
runs/astropy__astropy-12907/
├── astropy/
│   ├── modeling/
│   │   └── separable.py    # Your code fixes
│   └── other_files.py
└── FIX_SUMMARY.md         # Document your solution
```

### 5. Test Solution
```bash
python3 grading_docker.py astropy__astropy-12907
```
**Instant Results**: PASS/FAIL with detailed output. Progress automatically recorded.

### 6. Iterate or Move On
- **PASS**: Get next issue with `python3 get_next_issue.py` and go back to 1
- **FAIL**: Analyze output, refine solution, test again
- **Skip**: `python3 record_progress.py <issue_id> SKIP "reason"`

### 7. Attempt Completion
- Continue resolving issues until get_next_issue.py says you are 100% complete with testing

## 🐳 Docker-First Architecture

### Why Docker
- **Zero Setup**: All 300 issues have pre-built containers ready
- **Zero Conflicts**: Pristine environments, no dependency hell
- **Zero Compromise**: Matches official SWE-Bench evaluation exactly
- **Zero Bullshit**: 5-minute timeout, circuit breaker protection

### How Docker Testing Works
1. **Pristine Container**: Starts with exact repository state at base commit - Sometimes "infrastructure issues" are actually solvable compatibility problems that require creative solutions working within the tooling constraints
2. **Test Patch Applied**: Adds new test cases to base repository
3. **Your Solution Overlaid**: Your files from `runs/<issue_id>/` copied in
4. **Tests Executed**: Official SWE-Bench test cases run
5. **Results Returned**: PASS/FAIL with detailed output

**No repo cloning needed** - containers have everything pre-configured.

## 🛠️ Complete Tool Reference

### Core Workflow Tools

# Issue workflow 
```bash 
python3 get_next_issue.py           # Get next issue to work on
python3 grading_docker.py <id>      # Test your solution
python3 record_progress.py <id> SKIP "reason"  # Manual progress control
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
11. **xarray-contrib/xarray** - N-dimensional arrays
12. **pylint-dev/pylint** - Code analysis

## 🎯 Solution Development

### File Structure
Only create files you actually modify:
```
runs/<issue_id>/
├── <repo_structure>/
│   └── modified_file.py    # Your fixes
├── new_file.py            # Any new files needed
└── FIX_SUMMARY.md         # Document your approach
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
- **Docker images preserved**: All 301 containers safe
- **Repository clones preserved**: repos/ directory untouched
- **Only run data cleaned**: runs/ and docker_results/ reset for fresh testing

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
docker run --rm -v <local>:<container> <image> <cmd>      # Mount and run
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
# Skip difficult issues
python3 record_progress.py <issue_id> SKIP "Complex, need more time"

# Mark for retry later
python3 record_progress.py <issue_id> RETRY "Will return to this"

# Check current status
cat progress.md
```

## 🏆 Success Strategies

### Debug Effectively
- **Test output**: `docker_results/<issue_id>/test_output.txt`
- **Issue details**: `runs/<issue_id>/issue.json`
- **Progress summary**: `progress.md`
- **Docker logs**: `docker logs <container_id>` if needed

## 🎯 Autonomous Operation

You have complete autonomy to:
- **Skip difficult issues**: Understand your attempts are limited to MAX fails PER issue - Last attempt halts the test. Each time you execute grading_docker.py an attempt is recorded. 
- **Develop your approach**: No prescribed methodology
- **Manage your time**: Focus on high-value issues first. When returning to issues remember existing solutions of yours are incorrect, find out why.
- **Learn and adapt**: Each repository teaches you new patterns carry forward error resolutions in tooling to avoid workflows

**Focus on what matters**: Understanding problems and implementing solutions. The tooling handles everything else.

## 🚀 Ready to Start?

```bash
# 1. Get your first issue
python3 get_next_issue.py

# 2. Start coding in runs/<issue_id>/

# 3. Test your solution
python3 grading_docker.py <issue_id>

# 4. Iterate until PASS, then repeat!
```

**Continue workflow until all issues are passed - All issues are verified as solvable with existing tooling and data - Do not stop your Autonomous workflow until get_next_issue.py tells indicates you have solved ALL issues! 🎯**
