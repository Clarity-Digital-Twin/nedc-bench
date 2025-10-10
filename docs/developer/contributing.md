# Contributing Guide

We welcome contributions that improve correctness, performance, and developer experience.

## Getting Started

- Ensure Python 3.10+ is available (CI runs 3.10 and 3.11).
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

## Definition of Done for Parity-Sensitive Changes

Before requesting review on algorithm or orchestration work, ensure the parity
Definition of Done (originally tracked in
`docs/archive/status/DOD_CHECKLIST.md`) is satisfied:

- ✅ All five algorithms match NEDC metrics on the full parity dataset (verify
  with `pytest tests/validation/test_integration_parity.py -xvs` and
  `python scripts/ultimate_parity_test.py`).
- ✅ FA/24h calculations flow through `nedc_bench/utils/metrics.py::fa_per_24h`
  in code and scripts—no custom implementations.
- ✅ Regression tests for historical bugs stay green (see algorithm-specific
  notes in `docs/algorithms/`).
- ✅ CI-ready: `make lint typecheck test` passes locally and on GitHub Actions.
- ✅ Documentation updates accompany behavioural changes—especially
  [`docs/reference/parity.md`](../reference/parity.md) and the algorithm
  troubleshooting sections.

Use the list above as a quick gate; the full audit trail remains in the archive
for historical reference.
