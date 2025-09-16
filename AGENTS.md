# Repository Guidelines

Unified guide for AI coding agents and human contributors. These rules apply to the entire repo.

## Project Structure & Boundaries

- `nedc_bench/` — modern source: `algorithms/`, `api/`, `models/`, `orchestration/`, `validation/`, `utils/`.
- `alpha/` — thin wrapper for legacy NEDC. Keep new logic out.
- `nedc_eeg_eval/v6.0.0/` — original NEDC code. Do not modify.
- `tests/` — mirrors `nedc_bench/`. Place tests alongside the corresponding module subtree.
- `scripts/` — parity checks, batch runs. Use `uv run python scripts/...` when possible.
- `docs/`, `k8s/`, `monitoring/` — documentation and deployment assets.

## Agent Operating Rules (2025)

- Prefer small, surgical patches. Use `apply_patch`; avoid broad refactors unless requested.
- Read files in chunks (≤250 lines). Use `rg` to search and `sed -n` to view ranges.
- Before tool calls, add a one‑sentence preamble of next actions. For multi‑step work, maintain a plan via `update_plan` with exactly one `in_progress` step.
- Follow repo tooling: Ruff (format/lint), MyPy (strict), Pytest. Don’t add dependencies or commit changes unless asked.
- Respect boundaries: never edit `nedc_eeg_eval/`. Keep public APIs and behavior stable; update docs/tests if behavior changes.

## Build, Test, and Dev Commands

- `make dev` — install dev deps + pre-commit (via `uv`).
- `make test` / `make test-fast` — run tests with coverage (parallel for speed).
- `make lint` / `make lint-fix` — Ruff + MyPy; `lint-fix` auto-fixes and formats.
- `make format` — format with Ruff; `make typecheck` — strict MyPy on `nedc_bench/`.
- `make docs-serve` — serve MkDocs; `docker-compose up -d` — run API stack locally.

## Coding Style & Naming

- Python ≥3.10; 4‑space indents; line length 100; double quotes.
- NumPy docstrings; full type hints (no untyped defs). Prefer `pathlib.Path`.
- Names: modules/functions `snake_case`; classes `CamelCase`; constants `UPPER_SNAKE`.
- Imports sorted by Ruff/isort. Run `ruff check --fix` and `ruff format` before pushing.

## Testing Guidelines

- Pytest configured in `pyproject.toml`. File/class/function patterns: `test_*.py`, `Test*`, `test_*`.
- Markers: `integration`, `performance`, `slow`, `benchmark`, `gpu`.
- Examples: `pytest -n auto --cov=nedc_bench -v`, `pytest -v -m "not slow"`.
- Keep or raise coverage (current ~92%). Add parity tests when touching algorithms/orchestration.

## API & Legacy Tooling

- Env: API sets `NEDC_NFC` (legacy root) and adjusts `PYTHONPATH` for `lib/` at runtime.
- `run_nedc.sh` chdirs to `nedc_eeg_eval/v6.0.0/` before execution. List files referenced must be relative to that directory; contents often need `../../data/...` paths.
- Quick demo: `make run-nedc` or run API via `docker-compose up -d` then `curl localhost:8000/api/v1/health`.

## Commit & PR Expectations

- Write imperative messages and link issues (e.g., `Fixes #123`).
- Keep PRs focused; include tests and docs. Run `make lint typecheck test` locally.
- Keep versions consistent across `pyproject.toml`, API `version`, and package `__init__` when releasing.

## Security & Compliance

- Pre-commit scans for secrets; never commit credentials or large private datasets.
- External services: Redis/Prometheus via compose or k8s. Don’t hardcode endpoints; use env vars.
