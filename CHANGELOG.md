# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete test suite reorganization mirroring source structure
- Comprehensive validation tests for Alpha-Beta pipeline parity
- Golden tests for edge cases and perfect match scenarios
- Multi-match TAES scenario tests

### Changed
- Test directory structure now parallels nedc_bench/ source tree
- Moved algorithm tests to tests/algorithms/
- Moved model tests to tests/models/
- Moved orchestration tests to tests/orchestration/
- Moved validation tests to tests/validation/

### Fixed
- Import paths updated for new test structure
- Resolved naming conflict between tests/utils.py and tests/utils/ directory

## [0.1.0] - 2025-01-15

### Added
- Initial alpha release of NEDC-BENCH dual-pipeline architecture
- Alpha Pipeline: NEDCAlphaWrapper for NEDC v6.0.0 integration
- Beta Pipeline: Modern Python implementation foundation
- Comprehensive test suite with 80%+ coverage requirement
- Docker support for containerized execution
- API server with FastAPI for programmatic access
- Batch processing scripts for large-scale evaluation
- Parity validation framework for Alpha-Beta consistency

### Changed
- Minimum Python version set to 3.10 (scipy>=1.14.1 requirement)
- Ruff target-version updated to py310
- MyPy python_version set to 3.10
- Pre-commit default language version updated to python3.10

### Removed
- Non-functional CLI entry point (nedc-bench command)
- CLI_DEBT.md tracking file (investigation complete)

### Fixed
- Python version inconsistencies across configuration files
- Import compatibility for tomllib/tomli across Python versions
- Path resolution issues in run_nedc.sh wrapper script

## [0.0.1] - 2024-12-01

### Added
- Initial repository structure
- Vendored NEDC EEG Evaluation v6.0.0
- Basic wrapper script (run_nedc.sh)
- Modern Python development environment (UV, Ruff, MyPy, Pytest)
- Pre-commit hooks for code quality
- Makefile with developer commands
- Technical analysis documentation (NEDC_EEG_EVAL_ANALYSIS.md)
- Implementation roadmap (NEDC_BENCH_IMPLEMENTATION_PLAN.md)

[Unreleased]: https://github.com/Clarity-Digital-Twin/nedc-bench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Clarity-Digital-Twin/nedc-bench/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/Clarity-Digital-Twin/nedc-bench/releases/tag/v0.0.1