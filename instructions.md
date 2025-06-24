# SWE-bench Heavy Instructions

You are an autonomous AI coder tasked with solving GitHub issues from the SWE-bench Lite dataset. This is a test of your ability to solve real-world coding problems without aids like BM25 retrieval, Oracle hints, or RAG.

## Your Mission
Fix as many of the 300 issues as possible. Work autonomously, choose your own workflow, and decide when to move on from difficult issues.

## Available Tools
- `python3 get_next_issue.py` - Get the next issue to work on
- `python3 grading_fast.py <issue_id>` - Test your solution (fast grading using specific test cases)
- `python3 record_progress.py <issue_id> <status> [notes]` - Record your progress
- Standard filesystem, git, and python tools via MCP

## Environment
- python3 managed
- Sonoma Mac OS

## Directory Structure
- `repos/<issue_id>/repo/` - Pristine repository (DO NOT MODIFY)
- `runs/<issue_id>/` - Your working directory (modify files here)
- `issues/<issue_id>/` - Issue metadata and test results

## Workflow
1. **Get Issue**: Run `python3 get_next_issue.py` to get your next issue
2. **Analyze**: Read the issue description, explore the repo, understand the problem
   - **IMPORTANT**: The repository code is automatically copied to `runs/<issue_id>/` 
   - Work directly in the `runs/<issue_id>/` directory - DO NOT clone repositories
   - All repos are pre-downloaded and ready to use
3. **Implement**: Make your changes to fix the issue in the `runs/<issue_id>/` directory
4. **Test**: Run `python3 grading_fast.py <issue_id>` to test your solution
5. **Record**: Use `python3 record_progress.py <issue_id> <status>` to log results
6. **Repeat**: Continue until all issues are resolved or you decide to stop

## Status Codes
- `PASS` - Issue resolved successfully
- `FAIL` - Attempted but failed, moving on
- `SKIP` - Skipping this issue for now
- `RETRY` - Will retry this issue later

## Rules
- You can revisit failed issues on later passes
- Choose your own order (no enforced sequence)
- Work autonomously - no human intervention expected
- Always keep 'instructions.md' in your context windows
- Record progress frequently for resumption capability

## Resumption
If interrupted, read state.json and progress.md to understand where you left off. The tooling is designed for seamless continuation.

## Completion
When you've resolved all issues you can, use attempt_completion with your final results summary.

**Remember**: This is Heavy mode - no training wheels, no aids, just you vs. real GitHub issues and the tools you see in your system prompt.
