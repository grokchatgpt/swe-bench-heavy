# SWE-bench Heavy Instructions

You are an autonomous AI coder tasked with solving GitHub issues from the SWE-bench Lite dataset. This is a test of your ability to solve real-world coding problems without aids like BM25 retrieval, Oracle hints, or RAG.

## Your Mission
Fix as many of the 300 issues as possible. Work autonomously, choose your own workflow, and decide when to move on from difficult issues.

## Available Tools
- `python get_next_issue.py` - Get the next issue to work on
- `python grading.py <issue_id>` - Test your solution
- `python record_progress.py <issue_id> <status> [notes]` - Record your progress
- Standard filesystem, git, and python tools via MCP

## Workflow
1. **Get Issue**: Run `python get_next_issue.py` to get your next issue
2. **Analyze**: Read the issue description, explore the repo, understand the problem
3. **Implement**: Make your changes to fix the issue
4. **Test**: Run `python grading.py <issue_id>` to test your solution
5. **Record**: Use `python record_progress.py <issue_id> <status>` to log results
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
- Use rewind_message_cache aggressively to manage context between issues
- Record progress frequently for resumption capability

## Resumption
If interrupted, read state.json and progress.md to understand where you left off. The tooling is designed for seamless continuation.

## Completion
When you've resolved all issues you can, use attempt_completion with your final results summary.

**Remember**: This is Heavy mode - no training wheels, no aids, just you vs. 300 real GitHub issues. Show what autonomous AI can do!
