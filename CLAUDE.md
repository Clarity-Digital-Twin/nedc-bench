# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

NEDC-BENCH is a dual-architecture EEG benchmarking platform that wraps the original NEDC EEG Evaluation tool (v6.0.0) while building a modern Python implementation alongside it. The project maintains 100% algorithmic fidelity to the original Temple University NEDC algorithms while modernizing the infrastructure.

## Key Architecture Decisions

### Dual-Pipeline Strategy
- **Alpha Pipeline (Legacy)**: Wraps original NEDC code in `nedc_eeg_eval/v6.0.0/` - DO NOT modify these files
- **Beta Pipeline (Modern)**: New implementation in `nedc_bench/` using modern Python practices
- Both pipelines must produce identical results for validation

### Original NEDC Tool (`nedc_eeg_eval/v6.0.0/`)
- Research-grade software from Temple University, no explicit license
- Requires environment variables: `NEDC_NFC` (root dir) and `PYTHONPATH` (includes lib/)
- Python 3.9+ with numpy 2.0.2, scipy 1.14.1, lxml 5.3.0, tomli (for Python <3.11)
- 5 scoring algorithms: DP Alignment, Epoch-based, Overlap, TAES, IRA
- Input: CSV_BI annotation files (anonymized test data safe for public repo)
- Output: Text-based scoring reports in `output/` directory

### Modern Development Stack
- **UV** for package management (10-100x faster than pip)
- **Ruff** for linting/formatting (replaces Black, isort, flake8)
- **MyPy** for strict type checking
- **Pytest** with parallel execution and 80% coverage requirement
- **Pre-commit** hooks for code quality
- Python 3.11 default, supports 3.9+

## Essential Commands

### Development Setup
```bash
make dev          # Install dev dependencies + pre-commit hooks
make update       # Update all dependencies to latest versions
```

### Running Original NEDC Tool
```bash
# Direct wrapper script
./run_nedc.sh nedc_eeg_eval/v6.0.0/data/lists/ref.list \
              nedc_eeg_eval/v6.0.0/data/lists/hyp.list

# Via Makefile
make run-nedc     # Runs demo with test data
make nedc-help    # Shows NEDC tool help
```

### Testing
```bash
make test         # Run all tests with coverage
make test-fast    # Run tests in parallel
pytest tests/test_nedc_wrapper.py::TestNEDCWrapper::test_wrapper_help_command  # Single test
pytest -k "wrapper" -v  # Run tests matching pattern
```

### Code Quality
```bash
make lint         # Run ruff + mypy checks
make lint-fix     # Auto-fix linting issues and format
make format       # Format code with Ruff
make typecheck    # Run mypy type checking only
make pre-commit   # Run all pre-commit hooks manually
make ci           # Full CI pipeline locally (lint + typecheck + test)
```

### Utilities
```bash
make clean        # Clean build artifacts and caches
make tree         # Show project structure (excludes vendor/cache)
make loc          # Count lines of code (excluding vendor)
make todo         # Find all TODOs in codebase
```

## Critical Implementation Notes

### When Working with NEDC Original Code
1. **NEVER modify files in `nedc_eeg_eval/`** - it's vendored code
2. The wrapper script `run_nedc.sh` uses relative paths for portability
3. One manual fix was applied: `nedc_file_tools.py` has tomllib/tomli compatibility patch
4. All scoring algorithms must maintain exact numerical equivalence

#### ⚠️ CRITICAL PATH RESOLUTION ISSUE (Constantly Trips Us Up!)
**The `run_nedc.sh` script changes directory to `nedc_eeg_eval/v6.0.0/` before running!**

This means:
- List file paths given to `run_nedc.sh` must be relative to where it WILL look (from NEDC dir)
- Contents of list files must use `../../data/...` to get back to project data
- Example: `./run_nedc.sh custom_lists/ref.list custom_lists/hyp.list`
  - These files must exist at: `nedc_eeg_eval/v6.0.0/custom_lists/*.list`
  - Their contents: `../../data/csv_bi_parity/csv_bi_export_clean/ref/file.csv_bi`

See `scripts/README.md` for detailed examples. This issue has wasted HOURS of debugging!

### CSV_BI Annotation Format
- Located in `nedc_eeg_eval/v6.0.0/data/csv/{ref,hyp}/`
- Contains: version, patient ID, session, channel, start/stop times, labels, confidence
- These are anonymized test annotations, safe for public repository
- No actual EEG signals or patient data included

### Testing Strategy
- Tests in `tests/` use pytest fixtures from `conftest.py`
- Fixtures auto-configure NEDC environment variables
- Golden outputs in `nedc_eeg_eval/v6.0.0/test/results/` for validation
- New implementations must match these outputs exactly

### Configuration Files
- `pyproject.toml`: All Python tool configs (UV, Ruff, MyPy, Pytest, coverage)
- `.pre-commit-config.yaml`: Git hooks for code quality
- `Makefile`: Developer commands with colored output
- `.python-version`: Set to 3.11 for UV

### Licensing
- New code (wrapper, modern implementation): Apache 2.0
- Original NEDC code: No explicit license, copyright Temple University
- Keep licensing clear in all new files

## Project Status Tracking

Current implementation phase from `NEDC_BENCH_IMPLEMENTATION_PLAN.md`:
- ✅ Repository initialized with vendored NEDC v6.0.0
- ✅ Basic wrapper script functional
- ✅ Modern Python development environment configured
- ⬜ Docker containerization (Phase 1.2)
- ⬜ Alpha pipeline wrapper class (Phase 1.2)
- ⬜ Beta pipeline implementation (Phase 2)
- ⬜ Validation framework (Phase 3)

## Important File Paths

Key analysis documents:
- `NEDC_EEG_EVAL_ANALYSIS.md`: Complete technical analysis of original tool
- `NEDC_BENCH_IMPLEMENTATION_PLAN.md`: 14-week implementation roadmap

Test data locations:
- Reference lists: `nedc_eeg_eval/v6.0.0/data/lists/{ref,hyp}.list`
- Annotation files: `nedc_eeg_eval/v6.0.0/data/csv/{ref,hyp}/*.csv_bi`
- Expected outputs: `nedc_eeg_eval/v6.0.0/test/results/*.txt`