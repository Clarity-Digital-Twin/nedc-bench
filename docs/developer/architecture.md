# Architecture Guide

## Overview

- Dual-pipeline EEG evaluation platform that preserves NEDC v6.0.0 behavior while adding a modern API and tooling.
- Two pipelines run side-by-side (or individually) and a validator checks parity across all algorithms.

## Dual-Pipeline Design

- Alpha (legacy): vendored NEDC code in `nedc_eeg_eval/v6.0.0/` (unchanged); used as the reference implementation.
- Beta (modern): reimplementation in `src/nedc_bench/algorithms/` with NEDC-exact semantics and integer/float rules.
- Orchestration (`src/nedc_bench/orchestration/`): coordinates Alpha/Beta execution and parity reporting.

## Components

- Algorithms (`src/nedc_bench/algorithms/`): `taes.py`, `epoch.py`, `dp_alignment.py`, `overlap.py`, `ira.py`.
- Orchestration (`src/nedc_bench/orchestration/`): `dual_pipeline.py`, `parallel.py`; `validation/` for parity.
- API (`src/nedc_bench/api/`):
  - `main.py`: FastAPI app; sets `NEDC_NFC` default and spawns a job worker in lifespan.
  - `endpoints/`: `evaluation.py`, `health.py`, `websocket.py`, `metrics.py`.
  - `services/`: `job_manager.py`, `processor.py`, `websocket_manager.py`, `cache.py`.
  - `middleware/`: error handler, rate limit.
- Alpha wrapper (`src/alpha/`): container and helpers to execute the original tool.

## Clean Architecture Roadmap

Highlights extracted from the archived proposals
(`docs/archive/bulid_implementation/ARCHITECTURE_PROPOSAL.md`,
`ARCHITECTURE_COMPARISON.md`):

- **Target layering** — Domain entities and use cases will eventually sit in a
  `domain/` + `application/` structure, with adapters (API, CLI, batch) above
  them. The current codebase already resides under `src/`, so future extraction
  work can proceed incrementally.
- **Interface boundaries** — Define clear orchestrator interfaces to decouple
  algorithm execution from transport/IO concerns. The new router pattern is the
  first step in that direction.
- **Phased approach** — The historical `PHASE_1`–`PHASE_5` documents describe a
  vertical slice strategy (environment setup → algorithm parity → API → ops).
  Consolidate those notes under `docs/implementation/` as work continues.

## Refactor Risk & Completion Summary

The completed `src/` migration and associated hardening are chronicled in
`docs/archive/bulid_implementation/REFACTOR_RISK_ANALYSIS.md` and
`REFACTOR_COMPLETION_REPORT.md`. Key assurances to retain:

- Packaging now relies on Hatch with `packages = ["src/nedc_bench", "src/alpha"]`
  and data files are force-included where necessary.
- Docker images copy from `src/` and maintain parity with development installs.
- Tooling updates (Makefile, MyPy, Ruff) all target the new source layout.

## Router Pattern (2025 Architecture Upgrade)

Key elements extracted from the 2025 bug hunt:

```python
# src/nedc_bench/orchestration/router.py
class OrchestratorRouter:
    def __init__(self) -> None:
        self._dual_orch: DualPipelineOrchestrator | None = None
        self.beta_orch = BetaPipelineOrchestrator()

    def get_orchestrator(self, pipeline: str) -> Orchestrator:
        if pipeline == "beta":
            return self.beta_orch
        if pipeline in {"dual", "alpha"}:
            return self.dual_orch  # Lazy-load; requires NEDC_NFC
        raise ValueError(f"Unsupported pipeline: {pipeline}")
```

- **BetaPipelineOrchestrator** runs pure-beta evaluations without touching the
  legacy wrapper. Its constructor no longer mutates environment variables.
- Example:

  ```python
  class BetaPipelineOrchestrator:
      def __init__(self) -> None:
          self.beta = BetaPipeline()

      def evaluate(self, ref: Path, hyp: Path, algorithm: str) -> Any:
          return self.beta.evaluate(ref, hyp, algorithm)
  ```

- **Lazy loading** defers creation of `DualPipelineOrchestrator` until a dual or
  alpha request arrives. If `NEDC_NFC` is missing, the router raises a friendly
  error instead of mutating the environment.
- **Startup logging** clarifies when legacy assets are required. `main.py`
  auto-detects the vendored NEDC directory for development but logs a warning if
  it is absent—beta remains available either way:

  ```python
  nedc_root = os.environ.get("NEDC_NFC")
  if nedc_root:
      logger.info("NEDC_NFC set to: %s", nedc_root)
  else:
      logger.warning(
          "NEDC_NFC not set; beta pipeline available, dual/alpha disabled.",
      )
  ```

- **Result** — Beta can run with zero legacy dependencies; dual/alpha requests
  only succeed when the operator provides `NEDC_NFC`.

See `docs/developer/bug_fixes_2025.md#p1-1-betaalpha-decoupling` for the full
context and verification evidence.

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
