# SWE-bench Heavy

## Objective

SWE-bench Heavy provides a benchmark for evaluating autonomous AI coding capabilities by adapting the SWE-bench dataset with a novel administration methodology. This benchmark is designed to assess AI performance in human-like issue resolution scenarios without auxiliary aids, requiring sustained coherence across multiple issues within a single session.

## Overview

SWE-bench Heavy leverages the SWE-bench Lite dataset (300 GitHub issue-PR pairs from 11 Python projects) to evaluate an AI system's ability to autonomously resolve software engineering issues. The benchmark eliminates common performance aids including BM25 retrieval, Oracle hints, RAG systems, and session isolation. The testing environment provides only essential tools and data, allowing the AI to develop its own workflow while tackling issues sequentially with the flexibility to revisit failed attempts.

The core challenge can be summarized as: "Given 300 verified bugs across 12 different codebases, resolve as many as possible autonomously." The benchmark requires no specialized configuration beyond standard development tools, making it broadly applicable to various problem sets without affecting the AI's problem-solving approach.

**Rationale for "Heavy" Designation**: While inference aids such as RAG, Oracle systems, and BM25 retrieval demonstrate significant performance benefits, they require substantial setup and maintenance overhead. These requirements limit their applicability for general-purpose AI agent tasks. The 300 issues in the SWE-bench Lite dataset provide an ideal foundation for evaluation without such aids, as they were specifically selected and verified by the original authors to minimize testing costs while maintaining quality.

## Evaluation Metrics

SWE-bench Heavy measures two primary dimensions:

1. **Correctness**: The proportion of successfully resolved issues from the total attempted
2. **Efficiency**: Resource utilization measured through cache efficiency and total input/output token consumption

Cost tracking is automatically handled by modern coding environments (Cline, Cursor, etc.), while correctness evaluation leverages existing SWE-bench infrastructure.

## Testing Environment

The benchmark provides a controlled environment with the following characteristics:

- **Pre-configured toolchain**: Git, Python, and necessary permissions
- **Repository access**: Complete access to codebases and test specifications
- **Automated tooling suite**:
  - Issue selection and presentation
  - Solution validation and testing
  - Progress tracking and state management
  - Incremental progress recording
  - Session resumption capabilities

Additional infrastructure includes:
- Automated repository download and setup scripts
- Standardized input files and test cases for all issues
- Environment reset and cleanup utilities
- Configurable test scope: ALL (300 issues), SIZE (first N issues), or RANGE (issues M through N)

## Dataset and Evaluation

The benchmark utilizes the SWE-bench Lite dataset (`swe_bench_lite.jsonl`) with evaluation conducted through unit testing, using post-PR behavior as the reference standard. The evaluation methodology emphasizes self-directed, human-like problem-solving approaches without retrieval or hint systems.

## Administration

SWE-bench Heavy is designed for complete self-administration. Users configure the problem scope and observe testing progress. The system supports seamless resumption of interrupted sessions, allowing AI systems to continue from their last checkpoint without context loss. The benchmark includes no safeguards against confused or looping AI behavior, providing an authentic evaluation environment.

## Evaluation Protocol

### Setup Phase
1. Execute `setup.py` (note: ranges are zero-indexed and inclusive)
2. In VSCode with Cline/Cursor: instruct the AI to "read instructions.md and attempt completion when all issues are resolved"

### Input Specification
- Issue description and context
- Repository URL and commit hash
- Test specifications
- **Excluded**: BM25 retrieval, Oracle hints, or other auxiliary aids

### AI Workflow
1. **Issue Selection**: Retrieve next issue from tooling
2. **Analysis and Implementation**: Autonomous issue analysis, codebase exploration, file modification, and solution testing using `grading_fast.py`
3. **Decision Making**: Determine whether to mark as passed, retry, or skip
4. **Progress Management**: Automated progress and state recording for session continuity
5. **Issue Prioritization**: Free selection of next issue (no enforced ordering)

### Technical Infrastructure
- **Core Tools**: Filesystem MCP, Shell-command-server MCP
- **Version Control**: Git for repository management
- **Testing**: Python-based test execution
- **Administration**: Self-contained toolchain

### Error Handling
- AI-directed retry and skip decisions with comprehensive logging
- Support for revisiting failed issues in subsequent passes
- Flexible failure recovery mechanisms

## Constraints and Requirements

1. **No tooling modifications**: Test infrastructure must remain unaltered
2. **Session continuity**: Interruptions must resume within the same conversation context window for valid results
3. **Tool limitations**: Only filesystem, shell-command-server, and chosen context window management systems permitted
4. **No auxiliary aids**: Inference aids are prohibited as they contradict the benchmark's core objectives

## Expected Outcomes

SWE-bench Heavy will quantify:
- **Resolution rate**: Number of successfully resolved issues relative to attempts
- **Resource efficiency**: Precise cost measurement of the problem-solving effort
- **Sustained performance**: AI capability across extended problem-solving sessions
- **Autonomous decision-making**: Quality of issue prioritization and retry strategies

This benchmark provides valuable insights into AI coding capabilities in realistic, resource-constrained environments without performance-enhancing aids.
