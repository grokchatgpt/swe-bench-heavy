# swe-bench-heavy Installation Guide 
This guide will help you set up the SWE-bench Heavy benchmark for autonomous AI testing. 

## Prerequisites
- Python 3.8+
- Git
- pip
- rsync (for file copying)
- Internet connection (for downloading dataset and repositories) 

## Quick Setup
1. **Download SWE-bench Lite Dataset**: 
```bash
# Download the dataset (this will be automated in setup script)
wget https://github.com/princeton-nlp/SWE-bench/releases/download/v1.0.0/swe_bench_lite.jsonl
``` 
2. **Configure Test Parameters**: Edit `state.json` to configure your test run: 
```json
{ "test_config": { "mode": "ALL", // Options: "ALL", "SIZE", 
"RANGE" "total_issues": 300, // For SIZE mode: number of issues 
"dataset_file": "swe_bench_lite.jsonl", 
"start_index": 0, // For RANGE mode: start index 
"end_index": 299 // For RANGE mode: end index }
}
``` 

**Test Modes**: - `ALL`: Test all 300 issues in the dataset
- `SIZE`: Test first N issues (set `total_issues`)
- `RANGE`: Test issues from index M to N (set `start_index` and `end_index`) 3. Inclusive and 0 indexed.

**Verify Setup**: 
```bash
python get_next_issue.py # Should show first issue
python record_progress.py test_issue SKIP "Testing setup" # Should update progress
``` 

## Directory Structure
After setup, your directory will look like: 
``` test/
├── heavy.md # Benchmark description
├── instructions.md # Bot instructions
├── install.md # This file
├── state.json # Test state and configuration
├── progress.md # Human-readable progress log
├── get_next_issue.py # Issue selection tool
├── record_progress.py # Progress recording tool
├── grading_fast.py # Fast solution testing tool
├── setup.py # Automated setup script
├── cleanup.py # Reset script
├── swe_bench_lite.jsonl # Dataset (downloaded)
├── repos/ # Pre-downloaded repositories (pristine)
│ └── <issue_id>/
│     └── repo/ # Original repository at base commit
├── runs/ # Working directories (copies for modifications)
│ └── <issue_id>/ # Your workspace for each issue
└── issues/ # Issue-specific metadata and results
    └── <issue_id>/
        ├── issue.json # Issue details
        ├── test_env/ # Isolated test environment
        ├── test_results.json # Test results
        └── test_output.txt # Test output
``` 
## Running the Benchmark

### For Bots (Autonomous)
Tell your bot: 
```
read instructions.md and attempt completion when all issues are resolved
``` 

### For Humans (Manual Testing)
1. **Get next issue**: 
```bash
python get_next_issue.py
``` 
2. **Work on the issue** in the `runs/<issue_id>/` directory (automatically copied from pre-downloaded repos)
3. **Test your solution**: 
```bash
python3 grading_fast.py <issue_id>
```
4. **Record progress**: 
```bash
python record_progress.py <issue_id> PASS "Fixed the bug"
python record_progress.py <issue_id> FAIL "Need more investigation"
python record_progress.py <issue_id> SKIP "Too complex for now"
python record_progress.py <issue_id> RETRY "Will try again later"
``` 

## Resumption
The benchmark is designed for seamless resumption: 
- **State**: Tracked in `state.json`
- **Progress**: Human-readable log in `progress.md`
- **Issue Status**: Each issue maintains its own state If interrupted, simply restart with the same command. The system will continue where it left off. 

## Cleanup and Reset
To reset for a new test run: 
```bash
python cleanup.py # Removes all issue directories and resets state
``` 
To clean specific issues: 
```bash
python cleanup.py --issues django__django-11964 flask__flask-1234
``` 

## Configuration Options

### Test Scope

Edit `state.json` to change test scope: 
```json
{ "test_config": { "mode": "SIZE", "total_issues": 50, // Test first 50 issues only 
"dataset_file": "swe_bench_lite.jsonl" }
}
``` 

```json
{ "test_config": { "mode": "RANGE", "start_index": 100, // Start from issue 100 
"end_index": 149, // End at issue 149 (50 issues total) 
"dataset_file": "swe_bench_lite.jsonl" }
}
``` 

### Custom Dataset
To use a different dataset: 
1. Place your `.jsonl` file in the test directory
2. Update `dataset_file` in `state.json`
3. Ensure your dataset follows SWE-bench format 

## Troubleshooting

### Common Issues
1. **"Dataset not found"**: Run the setup script to download `swe_bench_lite.jsonl` 2. **"Git clone failed"**: Check internet connection and GitHub access 
3. **"Test execution failed"**: Ensure Python dependencies are installed 
4. **"Permission denied"**: Make sure scripts are executable: 
```bash
chmod +x *.py
``` 

### Debug Mode
Add debug output to any script: 
```bash
python -u get_next_issue.py # Unbuffered output
PYTHONPATH=. python3 grading_fast.py <issue_id> # Add current dir to path
``` 

## Performance Notes
- **Disk Space**: Each issue requires ~100-500MB for repository and test environment
- **Memory**: Test execution may require 1-2GB RAM per issue
- **Network**: Initial setup downloads ~1GB of repositories
- **Time**: One time LONG clone time for all 300 

## Security Notes
- Test environments are isolated in separate directories
- No network access during test execution (after initial setup)
- All repositories are cloned to specific commits (no latest code)
- Test patches are applied in isolated environments This benchmark is designed to be completely self-contained and autonomous. No human intervention should be required during execution.
