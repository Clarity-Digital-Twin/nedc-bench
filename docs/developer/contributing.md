# Contributing Guide

We welcome contributions that improve correctness, performance, and developer experience.

## Getting Started
- Ensure Python 3.9–3.11 is available (CI runs across these versions).
- Install dev deps and hooks: `make dev`.
- Verify setup: `make test` and `make lint`.

## Code Standards
- Format with `ruff format` and lint with `ruff check` (see `make format`, `make lint`).
- Strict typing with MyPy (`make typecheck`).
- NumPy-style docstrings where appropriate.

## Pull Request Process
- Create a feature branch and open a PR to `main`.
- Keep changes focused; update docs and tests as needed.
- Ensure CI is green on Linux and Windows; avoid breaking parity.

## Testing Requirements
- Run `make test` locally (prints coverage to terminal).
- Add tests for new logic; mirror patterns under `tests/`.
- For algorithm changes, validate parity: `python scripts/compare_parity.py`.
