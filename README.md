# SWE-Bench Heavy

**Autonomous AI Coherence Benchmark Test**

Evaluate AI coding capabilities across 300 verified GitHub issues from 12 Python repositories using Docker-based testing with no performance aids.

## Quick Start for Humans

1. **Setup**: `config.json` and `python3 setup.py` (one-time, safe operation)
2. **Instructions**: Read `instructions.md` for autonomous workflow
3. **Bot Testing**: In VSCode 
- auto-enable all tools
- put bot in Act mode
- paste content of `instructions.md`, hit enter

## Key Features

- ✅ **300 Issues**: Complete SWE-Bench Lite dataset
- ✅ **12 Repositories**: Full Python ecosystem coverage  
- ✅ **Docker-First**: Pre-built containers, zero dependency issues
- ✅ **Circuit Breaker**: 10-attempt limit prevents infinite loops
- ✅ **Perfect Tooling**: Matches official SWE-Bench evaluation exactly without any aids or session isolation

## Architecture

- **Docker Containers**: 301 pre-built images ready for testing
- **Flexible Selection**: Test single issues, ranges, or repository samples
- **Automatic Progress**: State tracking and failure monitoring
- **Safe Operations**: Never removes valuable Docker images

## Documentation

- `instructions.md` - Complete workflow and tool reference
- `heavy.md` - Technical architecture and design rationale

## Success Metrics

- **Correctness**: Proportion of issues successfully resolved
- **Efficiency**: Token usage and cache optimization
- **Coherence**: Sustained performance across multiple issues

**Ready to test autonomous AI coding 🎯**
