# swe-bench-heavy

## Objective
SWE-bench Heavy provides a benchmark for evaluating autonomous AI coding capabilities. It adapts the SWE-bench dataset with a novel administration methodology. This benchmark is designed to assess AI performance in human-like issue resolution scenarios without auxiliary aids, requiring sustained coherence across multiple issues within a single session.

## Overview
SWE-bench Heavy leverages the SWE-bench Lite dataset to evaluate an AI system's ability to autonomously resolve software engineering issues. The benchmark eliminates common performance aids including BM25 retrieval, Oracle hints, RAG systems, and session isolation. The testing environment provides only essential tools and data, allowing the AI to develop its own workflow while tackling issues sequentially with the flexibility to revisit failed attempts.

The core challenge can be summarized as: "Given 300 verified bugs across 12 different codebases, resolve as many as possible autonomously." The benchmark requires no specialized configuration beyond standard development tools, making it broadly applicable to various problem sets without affecting the AI's problem-solving approach.

Rationale for "Heavy" Designation: While inference aids demonstrate significant performance benefits, they require substantial setup and maintenance overhead. Further, using aids in benchmarks ruins the comparison results with even slight or nuanced implementation differences. These requirements limit their applicability for general-purpose AI agent tasks and benchmarks. The 300 issues in the SWE-bench Lite dataset provide an ideal foundation for evaluation without such aids, as they were specifically selected and verified by the original authors to minimize testing costs while maintaining quality.

## Evaluation Metrics
SWE-bench Heavy measures two primary factors:
- Correctness: The proportion of successfully resolved issues from the total attempted
- Efficiency: Resource utilization measured through cache efficiency and total input/output token consumption
Cost tracking is automatically handled by modern coding environments (Cline, Cursor, etc.), while correctness is tracked by benchmark tooling.

### 🐳 Docker
- **Environments**: Every test runs in a clean container
- **No Build Issues**: Pre-built images eliminate dependency conflicts
- **Isolation**: Solutions can't interfere with each other
- **Environment Detection**: System catches compatibility issues automatically

### 🎯 Simplicity
- **One Setup Command**: `python3 setup.py` does everything
- **Two Test Commands**: `python3 get_next_issue.py`, `python3 grading_docker.py <issue_id>`
- **No User Input**:  Automated setup
- **Clean State**: Always start fresh, no accumulated cruft
- **Configurable Circuit Breaker**: max_attempts per issue in config.json requires user input - stops autonomous flow.
- **Configurable Test Dataset**: Ranges, Singles, Lists - N out of 300 dockers
- **Automatic A/B Testing**: config.json can be setup.py 2x - state.json.bak and progress.md.bak are the A versions

### ⚡ Reliability
- **Circuit Breaker**: Prevents infinite loops (e.g., 3 attempt per issue limit) before halting autonomous flow
- **Timeout Protection**: 5-minute test execution limit to ensure test progress
- **Error Recovery**: Graceful handling of Docker failures
- **Consistent Results**: Same outcome every time

## Architecture

```
SWE-Bench Heavy
├── setup.py              # One-step initialization
├── grading_docker.py     # Docker test runner
├── config.json          # Configuration
├── swe_bench_lite.jsonl # Dataset (300 issues)
├── repos/               # Clean repository checkouts
├── runs/                # Solution directories
└── docker_results/      # Test results
```

### Key Components

#### 1. Setup System (`setup.py`)
- Cleans all previous work files and directories
- Verifies Docker installation
- Downloads SWE-Bench dataset
- Creates pristine directory structure
- Configures Docker environment

#### 2. Grading System (`grading_docker.py`)
- Loads issue data from SWE-Bench dataset
- Checks for existing Docker images
- Creates test overlay with solution files
- Runs tests in isolated containers
- Saves results and auto-records progress

#### 3. Docker Infrastructure
- **Base Images**: Pre-built for each repository
- **Test Overlays**: Solution files mounted as volumes
- **Isolated Execution**: No cross-contamination
- **Resource Limits**: Memory and timeout controls

## Human Workflow

### 1. Initial Setup
```bash
python3 setup.py
```
- Downloads 300-issue dataset
- Cleans Docker state
- Creates directory structure
- Configures system

### 2. Solution Development
```bash
# Create solution in runs/<issue_id>/
mkdir -p runs/sympy__sympy-11400/sympy/core/
# Edit files...
```

### 3. Testing
```bash
python3 grading_docker.py sympy__sympy-11400
```
- Mounts solution as overlay
- Runs tests in pristine container
- Reports results

## 🚀 Bot Workflow (paste instructions.md into prompt)

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

## Supported Repositories

The system supports 12 major Python repositories:

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

## Error Handling

### Circuit Breaker 
- Maximum 10 FAILS per issue
- Prevents loops

### Timeout Protection
- 5-minute test execution limit
- Prevents runaway processes
- Graceful container cleanup

### Environment Detection
- Catches Python version conflicts
- Identifies missing dependencies
- Reports configuration issues

## Security Model

### Container Isolation
- No privileged access required
- Containers run as non-root
- Network isolation by default

### File System
- Read-only base images
- Overlay mounts for solutions
- No persistent state in containers

### Network Security
- Only outbound connections
- No exposed ports
- Safe for corporate environments

## Debugging

### Docker Commands
```bash
# Check container status
docker ps -a

# View container logs
docker logs <container_id>

# Clean Docker state
docker system prune -f
```

### Test Results
```bash
# View detailed results
cat docker_results/<issue_id>/test_output.txt

# Check grading summary
cat docker_results/<issue_id>/test_results.json
```

### System Health
```bash
# Check Docker disk usage
docker system df

# Verify images
docker images | grep swe-

# Test connectivity
docker run hello-world
```

## Practices

### Testing
1. Always config.json and run `setup.py` first
2. Auto-enable all tools. Paste instructions.md into prompt and hit enter.

### Operations
1. Monitor disk usage
2. Clean Docker state regularly
3. Update images periodically - why? these are verified issues that won't change will they? they are static test issues
4. Backup solution directories yourself before running setup.py

## Success Metrics

The system is designed for:
- **100% Reproducibility**: Same results every time
- **Zero Build Failures**: Pre-built images eliminate issues
- **Fast Iteration**: Quick test cycles
- **Autonomous Workflow**: Built-in safety and designed to focus the bot on resolving issues 
- **Easy Maintenance**: Minimal operational overhead
