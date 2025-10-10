# Beta Configuration Architecture

This document consolidates the beta configuration design work that was
previously captured in `docs/archive_v2/BETA_CONFIG_DEBT.md`. It explains why
beta must bundle its own configuration, the implementation tiers that delivered
full independence from legacy assets, and the success criteria that keep the
system in parity with NEDC v6.0.0.

## Overview

- **Status**: ✅ Fully implemented (2025-10-10)
- **Priority**: P0 at the time of work; blocks “beta-only” deployment claims
- **Goal**: Allow beta algorithms to run without requiring `nedc_eeg_eval/`
  assets while remaining backward compatible with the dual pipeline.

## Three-Tier Implementation Plan

### Tier 1 — Ship Beta Configuration with the Package

- Bundle `src/nedc_bench/config/beta_params.toml` inside the wheel.
- Update Hatch configuration (pyproject.toml) with
  `[tool.hatch.build.targets.wheel.force-include]` so the TOML is present in
  installations.
- Load order cascade (see below) ensures beta prefers its bundled config but can
  still consume the original NEDC TOML when required.
- Outcome: Beta algorithms no longer need the `nedc_eeg_eval` directory for
  standard operation.

### Tier 2 — Correct Algorithm Defaults

- Fix `EpochScorer` and `IRAScorer` defaults to match TOML values:
  `epoch_duration=0.25`, `null_class="bckg"`.
- Update docstrings and tests to reflect the canonical defaults.
- Ensure orchestrator code passes the corrected defaults when pulling from the
  bundle.

### Tier 3 — Centralize Algorithm Constants

- Introduce `src/nedc_bench/config/constants.py` to declare:
  - `EPOCH_DURATION = 0.25`
  - `NULL_CLASS = "bckg"` (semantic background label)
  - `DP_PENALTY_DEL/INS/SUB = 1.0`
  - `OVERLAP_GUARD_WIDTH`, `MIN_PRECISION`, etc.
- Re-export shared constants such as `DEFAULT_CHANNEL`.
- Maintain the intentional exception: `dp_alignment.py` keeps its internal
  `NULL_CLASS = "null"` sentinel (explained below).

## Configuration Load Order

`load_nedc_params()` now resolves configuration using a five-step priority
cascade:

1. `BETA_CONFIG_PATH` environment variable (user-supplied override).
2. Bundled `beta_params.toml` shipped with the package.
3. `NEDC_NFC` environment variable (backward compatibility for dual/alpha).
4. In-repo NEDC TOML (development convenience).
5. Hardcoded defaults defined in `config.constants`.

This ordering keeps beta self-contained while preserving dual-pipeline parity.

## Key Design Decisions

- **Bundled vs external config** — Shipping the TOML with the wheel guarantees
  beta works out of the box, avoiding accidental dependence on the legacy repo.
- **Single source of truth** — Algorithm parameters now live in
  `config.constants`; consumers import from there instead of scattering magic
  numbers.
- **NULL_CLASS sentinel exception** — Documented here and in the algorithm
  references: DP alignment requires its own `"null"` sentinel to avoid
  collisions with real `"bckg"` labels. All other algorithms use the centralized
  `NULL_CLASS`.
- **Testing & linting** — The changes passed `make lint`, `make typecheck`, and
  the full parity suites; coverage remained at ~88%.

## Success Criteria (Completed)

- ✅ All algorithm parameters imported from `config.constants`.
- ✅ No hard-coded algorithm defaults remain, except the intentional DP
  sentinel.
- ✅ Linting, type checking, and full parity tests pass with the new cascade.
- ✅ Documentation updated to note the sentinel exception.

## Related References

- [`docs/reference/configuration.md`](../reference/configuration.md) — Runtime
  configuration variables.
- [`docs/reference/parity.md`](../reference/parity.md) — Current parity status
  and verification commands.
- [`docs/algorithms/dp-alignment.md`](../algorithms/dp-alignment.md) — Sentinel
  rationale for DP alignment.
- Historical source: `docs/archive_v2/BETA_CONFIG_DEBT.md`.
