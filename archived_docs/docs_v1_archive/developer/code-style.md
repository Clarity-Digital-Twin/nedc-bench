# Code Style Guide

## Python

- Formatter: `ruff format` (see `make format`).
- Lint: `ruff check` with rules enabled for pycodestyle, pyflakes, bugbear, naming, pyupgrade, performance; line length 100.
- Target: minimum Python is 3.10; CI runs 3.10–3.11; Ruff `target-version` is `py310`.

## Type Hints

- `mypy` in strict mode; see `[tool.mypy]` in `pyproject.toml` (disallow untyped defs, no implicit optional, etc.).
- `python_version = "3.10"` in mypy config; third‑party libs like numpy/scipy/lxml are `ignore_missing_imports`.
- Run with `make typecheck`.

## Pre-commit

- Install hooks: `make dev` (runs `pre-commit install`).
- Hooks: trailing whitespace, EOF fixer, JSON/YAML checks, Ruff (lint+format), MyPy, Bandit, mdformat, Prettier for YAML/JSON, detect-secrets.

## Docstrings

- Convention: NumPy style (`[tool.ruff.lint.pydocstyle] convention = "numpy"`).
- Keep examples runnable and short; prefer type hints over docstring types.
