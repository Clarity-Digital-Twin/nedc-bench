# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2025-10-10

### Added

- **Comprehensive Documentation Overhaul**
  - `docs/developer/bug_fixes_2025.md` (835 lines) - Complete technical reference for all 11 critical bug fixes with evidence, file paths, and completion grades
  - `docs/developer/beta_config.md` - Three-tier beta configuration architecture documentation
  - `docs/developer/beta_config_design.md` - First-principles validation and design rationale for beta config
  - `docs/reference/parity.md` - Complete parity testing documentation (100% on 1832 file pairs)
  - `docs/developer/archive_migration_plan.md` - Documentation extraction completion tracking

- **Algorithm Documentation Enhancements**
  - Enhanced `docs/algorithms/taes.md` with multi-overlap sequencing details
  - Enhanced `docs/algorithms/epoch.md` with sampling boundary documentation
  - Enhanced `docs/algorithms/ira.md` with kappa calculation internals
  - Enhanced `docs/algorithms/dp-alignment.md` with NULL sentinel design rationale

- **Testing Infrastructure**
  - pytest-xdist group markers (`@pytest.mark.xdist_group`) for test isolation
  - `xdist_group` configuration in pytest markers for shared resource management
  - Comprehensive test stability documentation in TESTING.md
  - Alternative solutions analysis for test parallelization

### Changed

- **Test Configuration Philosophy**
  - Moved `--dist=loadgroup` from pyproject.toml to Makefile (opt-in parallel execution)
  - Preserved developer ergonomics for sequential test runs (`pytest path/to/test.py` works normally)
  - Industry-standard approach using pytest-xdist groups for shared resources

- **Documentation Structure**
  - Extracted all technical content from `docs/archive_v2/` into main documentation
  - 100% detail preservation (no summarization loss) - e.g., BUG_HUNT_REPORT.md: 807 lines → bug_fixes_2025.md: 835 lines
  - Moved data directory from `docs/data/` back to root `data/` (proper .gitignore handling)
  - All cross-references verified and working

- **Architecture Documentation**
  - Updated `docs/developer/architecture.md` with router pattern details
  - Beta/Alpha decoupling design documented (P1-1 bug fix)
  - Clean architecture roadmap integrated from archived proposals

### Fixed

- **11 Critical Bugs Documented** (see bug_fixes_2025.md for complete details):
  1. P1-1: Beta/Alpha decoupling (router pattern) - Grade A+
  2. P1-2: BetaPipelineOrchestrator NULL mutation - Grade A
  3. P1-3: Beta config loading (three-tier architecture) - Grade A+
  4. P1-4: DP NULL_CLASS separation - Grade A+
  5. P1-5: TAES count rounding - Grade A
  6. P1-6: Overlap penalty caps - Grade A
  7. P1-7: Epoch time boundaries - Grade A
  8. P1-8: IRA class handling - Grade B+
  9. P2-1: Integration test stability - Grade A+
  10. P2-2: Parity validator imports - Grade A
  11. P2-3: DP summary mapping - Grade A+

- **Test Stability Issues**
  - AsyncIO event loop binding in JobManager (documented in TESTING.md)
  - Race conditions in integration tests with shared resources
  - Proper use of pytest-xdist groups vs. forced serialization

- **Configuration Issues**
  - Beta params.toml packaging via Hatch force-include
  - NULL_CLASS collision prevention (dp_alignment.NULL_CLASS = "null" vs config.NULL_CLASS = "bckg")
  - Test configuration breaking sequential runs

### Deprecated

- `docs/archive/` and `docs/archive_v2/` directories (all valuable content extracted to main docs)
  - Archives remain as historical development record only
  - All current technical truth is in main documentation with verified cross-references

### Documentation

- **Complete Cross-Reference Verification** - All internal markdown links validated and working
- **Version Sync** - Fixed version mismatch between pyproject.toml (1.0.0) and __init__.py (0.1.0)
- **Evidence Preservation** - All bug fixes include file paths, line numbers, code examples, and verification evidence

## [1.0.0] - 2025-09-15

### Added

- Complete test suite reorganization mirroring source structure
- Comprehensive validation tests for Alpha-Beta pipeline parity
- Golden tests for edge cases and perfect match scenarios
- Multi-match TAES scenario tests
- Release management documentation (CHANGELOG.md, RELEASE.md)
- Release helper script (scripts/release.sh)

### Changed

- Test directory structure now parallels nedc_bench/ source tree
- Moved algorithm tests to tests/algorithms/
- Moved model tests to tests/models/
- Moved orchestration tests to tests/orchestration/
- Moved validation tests to tests/validation/
- **Version 1.0.0** - Production stable release

### Fixed

- Import paths updated for new test structure
- Resolved naming conflict between tests/utils.py and tests/utils/ directory

## [0.1.0] - 2024-12-15

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

## \[0.0.1\] - 2024-12-01

### Added

- Initial repository structure
- Vendored NEDC EEG Evaluation v6.0.0
- Basic wrapper script (run_nedc.sh)
- Modern Python development environment (UV, Ruff, MyPy, Pytest)
- Pre-commit hooks for code quality
- Makefile with developer commands
- Technical analysis documentation (NEDC_EEG_EVAL_ANALYSIS.md)
- Implementation roadmap (NEDC_BENCH_IMPLEMENTATION_PLAN.md)

[0.1.0]: https://github.com/Clarity-Digital-Twin/nedc-bench/releases/tag/v0.1.0
[1.0.0]: https://github.com/Clarity-Digital-Twin/nedc-bench/compare/v0.1.0...v1.0.0
[1.1.0]: https://github.com/Clarity-Digital-Twin/nedc-bench/compare/v1.0.0...v1.1.0
[unreleased]: https://github.com/Clarity-Digital-Twin/nedc-bench/compare/v1.1.0...HEAD
