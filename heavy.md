# SWE-bench Heavy

## Goal
Provide a benchmark testing autonomous AI conversation coherence by adapting the SWE-bench data set in a different test administration. The Heavy administration of this test is designed to mimic human-like issue resolution without aids and solving multiple issues in the same session.

## Description
Leverage SWE-bench Lite (300 GitHub issue-PR pairs from 11 Python projects) to test a bot’s ability to solve issues autonomously, mimicking a human coder. Remove all "cheats/aids" (BM25 retrieval, Oracle hints, RAG, separate sessions). Isolate the environment (tools and data). Allow the bot to choose its workflow, tackling one issue at a time, with freedom to revisit failed issues on later passes. This test is essentially: "hey, we have 300 bugs in 12 differenent code bases - go fix them all". There is no advanced configuration required for humans to deploy for the bot to solve these issues. Any set of problems can be substituted in this benchmark workflow and it should not affect the bot's ability to solve the issues. 

**Why "Heavy"**: Inference aids like RAG, Oracle, BM25, etc. are very powerful tools - however they all require setup in advance and maintainance. Those requirements make them less than ideal solutions for general AI Agent tasks. The 300 issues in the Lite dataset make for perfect adaptation material to be administered in a workflow without inference aids. The Authors of SWE-bench selected the 300 issues because they are all verified and chosen to minimize the cost of testing. 

## Scoring
Heavy is intended to measure the bot's correctness and cost over the span of issues. Correctness is measured by the number of issues he resolves out of the data set. Cost is measured by cache efficiency & total input/output tokens. Cost is automatically tracked in coding tools like Cline and Cursor. Correctness is already tracked by existing tooling in the SWE-bench.

## Environment
- Pre-configure all tools: Git, Python, MCP (filesystem & shell-command-server), and permissions.
- Ensure bot has access to repos and test specs.
- test tooling: get issue; tests solution; records result; tracks progress and provides bot with way to automatically record progress incrementally; tracks state for easy continuation; 
- tooling also includes script to download and install all repos ahead of time; ensure all issues have standard input files and test cases; a script is available to clean results and solutions from the repos and reset test state for new test runs; the get next issue tool is preconfigured based on your test config params: 'ALL' - 300; SIZE - first N issues; RANGE - issue index M to N;

## Data
Use SWE-bench Lite dataset (`swe_bench_lite.jsonl`). Evaluation via unit tests, using post-PR behavior as reference, administered in a self-directed, human-like style without BM25 or Oracle aids.

## Administration
This test is designed to be 100% self administered. You configure how many and which problems are used for the test. See install.md for how to configure and prepare a run and how to reset and clean up after runs. The test is designed so bots even w/o context can continue where they left off in test runs if the run is interrupted. It is up to you to configure the tests and observe testing. There are no fail-safes in this test around confused/looping bots. 

## Evaluation Flow
0. **Start**: run setup.py (ranges are 0 based and inclusive); in vscode Cline/Cursor tell the bot: "read instructions.md and attempt completion when all issues are resolved"
1. **Input**:
   - Bot receives: issue text, repo URL, commit hash, test specs.
   - No BM25 retrieval or Oracle hints.
2. **Bot Workflow**:
   - gets the next issue to work on from tooling. 
   - Autonomously analyzes issue, explores repo, edits files, and runs tests (`grading_fast.py`).
   - Decides to pass, retry, or quit. Can revisit failed issues later.
   - Tooling records progress and state so if session is interrupted, the bot can continue where he left off without repeating workflow.
   - Chooses next issue freely (no enforced order).
3. **Evaluation**:
   - Modified `run_evaluation.py` to disable BM25 and Oracle.
4. **Toolchain**:
   - Filesystem mcp, Shellserver mcp, Git for cloning, Python for tests, heavy tool chain self-administration.
   - Ensure bot has full access to tools and repos.
5. **Failure Handling**:
   - Bot retries or quits at discretion, logging attempts.
   - Failed issues can be revisited on later passes.

## Rules
1. No modifications to test tooling
2. Any interruptions must resume using same conversation context window - Test results are only valid in the same session.
3. No additional tools beyond filesystem, shell-command-server, and whatever context window management you choose (Cline/Cursor/etc all have their own implementations).
4. Do not add any inference aids as they defeat the purpose of this benchmark.

## Expected Results
Tests will reveal how many issues the bot was able to resolve out of the number of issues he attempted. Tests will reveal the exact cost of the effort.
