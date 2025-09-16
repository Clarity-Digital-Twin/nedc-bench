# Testing Guide

## Running Tests

- Project unit tests with coverage: `make test`
- Parallel run: `make test-fast`
- Watch mode (if installed): `make test-watch`
- Markers available (see `pyproject.toml`): `integration`, `performance`, `slow`, `benchmark`, `gpu`.

## Writing Tests

- Place tests under `tests/`, named `test_*.py`.
- Follow existing patterns for algorithms and validation; prefer deterministic inputs and integer assertions for DP/Epoch/Overlap.
- For TAES, allow small float tolerances where necessary.

## Coverage

- Coverage is collected over `nedc_bench/` (see `[tool.coverage.*]`).
- CI uploads coverage to Codecov from Ubuntu/Python 3.11.

## CI/CD

- GitHub Actions matrix (Linux + Windows; Python 3.10, 3.11) runs lint, typecheck, and tests.
- Parity job runs after tests and validates Alpha vs Beta outputs (IRA kappa tolerance 1e-4).
- API CI verifies importability and Docker build.
