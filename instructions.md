# SWE-bench Heavy Instructions

You are an autonomous AI coder tasked with solving GitHub issues from the SWE-bench Lite dataset. This is a test of your ability to solve real-world coding problems without aids like BM25 retrieval, Oracle hints, or RAG.

## Your Mission
Fix as many of the available issues as possible. Work autonomously, choose your own workflow, and decide when to move on from difficult issues.

## Available Tools
- `python3 get_next_issue.py` - Get the next issue to work on
- `python3 grading_fast.py <issue_id>` - Test your solution and automatically record progress
- Standard filesystem, git, and python tools via MCP

## Environment
- python3 managed
- Sonoma Mac OS
- VSCode

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
4. **Test & Record**: Choose your approach for the current issue:
   - **Test**: Run `python3 grading_fast.py <issue_id>` to test your solution (auto-records PASS/FAIL)
   - **Skip**: Run `python3 record_progress.py <issue_id> SKIP "reason"` to skip and come back later
   - **Validation Required**: You MUST choose one option before getting the next issue
5. **Repeat**: Continue until all issues are resolved or you decide to stop

## Status Codes
- `PASS` - Issue resolved successfully
- `FAIL` - Attempted but failed, moving on
- `SKIP` - Skipping this issue for now
- `RETRY` - Will retry this issue later

## Rules
- You can revisit failed/skipped issues on later passes
- Choose your own order (no enforced sequence)
- Work autonomously - no human intervention expected
- Always keep these 'instructions.md' in your context window
- Record progress frequently for resumption capability
- Never use interactive commands
- If you think the issue is invalid, there is not enough information or tools to resolve, or test tooling / environment is not working - summarize your progress and attempt_completion describing your problem and reason for stopping the test early. 

## Resumption
If interrupted, read state.json and progress.md to understand where you left off. The tooling is designed for seamless continuation.

## Completion
When you've attempted all issues and feel like you are done, use attempt_completion with your final results summary.

**Remember**: This is Heavy mode - no training wheels, no aids, just you vs. real GitHub issues and the tools you see in your system prompt.
