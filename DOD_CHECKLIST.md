# Parity v6.0.0 Definition of Done (DoD)

A concise, auditable checklist to confirm exact parity with NEDC v6.0.0 across all five algorithms (TAES, Epoch, Overlap, DP Alignment, IRA), correct FA/24h computation, and robust tests/CI.

## Core Parity
- [ ] All five algorithms match NEDC on the sample dataset (per-file and aggregate).
- [ ] TAES parity confirmed (labels/expansion/mapping).
- [ ] Epoch parity confirmed (midpoint sampling, epoch compression, integer confusion).
- [ ] Overlap parity confirmed (any-overlap semantics, boundary behavior).
- [ ] DP Alignment parity confirmed (alignment assumptions, background expansion, label mapping).
- [ ] IRA parity confirmed (event vs label mode equivalence, kappa).

## Orchestration Behavior
- [ ] `nedc_bench/orchestration/dual_pipeline.py` restores background expansion via `_expand_with_null` for DP, Epoch, and Overlap.
- [ ] Uniform label mapping applied after expansion to mirror NEDC.
- [ ] DP and Overlap inputs align with NEDC assumptions (no unintended epochization; event-label sequences for DP).

## FA/24h Centralization
- [ ] FA/24h computed via shared helper `nedc_bench/utils/metrics.py::fa_per_24h` everywhere it’s reported.
- [ ] Epoch FA/24h uses epoch scaling; other algos use standard FA/24h.
- [ ] Printed FA/24h rounding/precision matches NEDC formatting.

## DP Parity Validation
- [ ] Parity validator compares insertions/deletions/substitutions (not TP/FP/FN) for DP.
- [ ] `DPAlignmentResult` includes per-file totals for `sum_true_positives`, `sum_false_positives`, `sum_false_negatives` (for summaries), with sensible defaults.

## Tests (Unit + Integration)
- [ ] `pytest -q` passes locally with no failures.
- [ ] Overlap boundaries: `tests/algorithms/test_overlap_boundaries.py`.
- [ ] Epoch sampling boundary: `tests/algorithms/test_epoch_sampling_boundary.py`.
- [ ] IRA equivalence (label vs event): `tests/algorithms/test_ira_equivalence.py`.
- [ ] DP summary mapping/validator: `tests/validation/test_dp_summary_mapping.py`.
- [ ] Integration parity: `tests/test_integration_parity.py` covers per-algorithm and sequential runs.
- [ ] Golden parity snapshot file exists and a test asserts no drift against it.

## Parity Run (Sample Dataset)
- [ ] Parity run executed on sample data and archived:
      `C:\\Users\\JJ\\Desktop\\Clarity-Digital-Twin\\nedc-bench\\data\\csv_bi_parity\\csv_bi_export_clean`.
- [ ] Report shows exact match for TAES, Epoch, Overlap, DP, IRA.
- [ ] DP report includes matching ins/del/sub counts per file and in totals.
- [ ] FA/24h values in the report match NEDC for all algos.

## Scripts & Utilities
- [ ] Parity script(s) use the shared FA/24h helper and correct input formats.
- [ ] Any other scripts that report FA/24h now import `fa_per_24h` to prevent drift.

## Reproducibility
- [ ] Python version and dependency pins recorded (e.g., `requirements.txt`/`pyproject.toml`).
- [ ] Parity report captures environment metadata (Python, OS, package versions).
- [ ] Verified on Ubuntu and Windows (path/CRLF safe).

## CI/CD
- [ ] GitHub Actions runs `pytest -q` and parity snapshot check on PRs and `main`.
- [ ] Dependency caching enabled; runs on Ubuntu and Windows runners.
- [ ] CI fails on parity drift or FA/24h logic changes.
- [ ] CI publishes parity report artifact for releases.

## Documentation
- [ ] README includes: how to run parity, expected inputs/outputs, and interpreting results.
- [ ] “Gotchas” documented: epoch duration, rounding/precision, label mapping, background expansion.
- [ ] CHANGELOG updated with the parity milestone and highlights.

## Quick Verify (Manual)
- [ ] Run tests: `pytest -q` (all green).
- [ ] Run parity on sample dataset; confirm “match” across all algorithms.
- [ ] Inspect FA/24h outputs; confirm centralized helper is used.

## Sign-off
- [ ] Engineer sign-off: ____________________  Date: __________
- [ ] Reviewer sign-off: ____________________  Date: __________
- [ ] Release tag created and notes include parity artifacts.

