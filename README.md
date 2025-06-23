# SWE-bench Heavy

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
