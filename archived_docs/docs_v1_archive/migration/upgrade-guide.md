# Upgrade Guide

This project follows semantic versioning. Review the changelog for each release.

## Version Compatibility

- Python: >=3.10 (tests run on 3.10–3.11)
- NEDC reference: v6.0.0 vendored for parity

## Upgrade Steps

1. Update your environment to the required Python version.
1. `uv pip install --system -e .[dev]` or rebuild containers.
1. Run `make lint typecheck test` and `python scripts/compare_parity.py`.
1. If using the API, rebuild images and restart.

## Breaking Changes

- 0.1.0: Minimum Python raised to 3.10; placeholder CLI entry removed.
