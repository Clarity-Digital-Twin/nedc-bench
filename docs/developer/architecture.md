# Architecture Guide

## Overview

- Dual-pipeline EEG evaluation platform that preserves NEDC v6.0.0 behavior while adding a modern API and tooling.
- Two pipelines run side-by-side (or individually) and a validator checks parity across all algorithms.

## Dual-Pipeline Design

- Alpha (legacy): vendored NEDC code in `nedc_eeg_eval/v6.0.0/` (unchanged); used as the reference implementation.
- Beta (modern): reimplementation in `nedc_bench/algorithms/` with NEDC-exact semantics and integer/float rules.
- Orchestration (`nedc_bench/orchestration/`): coordinates Alpha/Beta execution and parity reporting.

## Components

- Algorithms (`nedc_bench/algorithms/`): `taes.py`, `epoch.py`, `dp_alignment.py`, `overlap.py`, `ira.py`.
- Orchestration (`nedc_bench/orchestration/`): `dual_pipeline.py`, `parallel.py`; `validation/` for parity.
- API (`nedc_bench/api/`):
  - `main.py`: FastAPI app; sets `NEDC_NFC` default and spawns a job worker in lifespan.
  - `endpoints/`: `evaluation.py`, `health.py`, `websocket.py`, `metrics.py`.
  - `services/`: `job_manager.py`, `processor.py`, `websocket_manager.py`, `cache.py`.
  - `middleware/`: error handler, rate limit.
- Alpha wrapper (`alpha/`): container and helpers to execute the original tool.

## Data Flow (API)

1. Client POSTs to `POST /api/v1/evaluate` with `reference`/`hypothesis` files and form fields: `algorithms` (repeatable), `pipeline`.
1. Files saved to `/tmp`, job enqueued via `services/job_manager.py`.
1. Background worker (`main.py`) calls `services/processor.py` to run requested algorithms through the orchestrator.
1. `services/websocket_manager.py` broadcasts progress and completion on `ws://<host>/ws/{job_id}`.
1. `GET /api/v1/evaluate/{job_id}` returns single-algorithm convenience fields or a multi-algorithm result map.

## Environment & Dependencies

- `NEDC_NFC`: NEDC root path. On startup, defaults to `nedc_eeg_eval/v6.0.0` and sets `PYTHONPATH` to its `lib/`.
- Redis (optional): `services/cache.py` and readiness probe in `health.py` use Redis if available.
- Dev/tooling: `uv`, `ruff`, `mypy`, `pytest` defined in `pyproject.toml` and `Makefile`.
