# EPOCH P0 BUG – 9 TP Mismatch (Parity Localization)

Date: 2025-09-15
Status: Open – under active investigation
Impact: P0 (blocks 100% parity – currently 99.97%)

## Summary

On csv_bi_parity (1832 pairs), Epoch shows a small but persistent gap between Alpha (NEDC v6.0.0) and Beta:

- Alpha (seiz): TP=33704, FP=18816, FN=250459, FA/24h=259.2257
- Beta  (seiz): TP=33713, FP=18829, FN=250450, FA/24h=259.4048

Delta: TP +9, FP +13, FN −9 (Sensitivity equal at 2dp, FA/24h +0.18)

All other algorithms (TAES, Overlap, DP, IRA) are at exact parity.

## What we’ve matched to NEDC

- Inclusive sampling boundary: sample midpoints while t <= stop_time
- 4-decimal rounding for event times and file duration (MIN_PRECISION=4)
- Background augmentation semantics via null class handling
- Bitwise comparable time-to-index check (>= and <=)

## Likely sources of the residual delta

1) Boundary inclusivity on specific files where last sample lies exactly on duration
2) Floating-point equality vs rounding order on event/file boundaries
3) Augmentation differences on files with no events on one side
4) Epoch “joint compression” edge-case on null<->seiz transitions

## Next steps (localize and fix)

1. Generate mismatched-file list for Epoch only
   - Use DualPipelineOrchestrator per-file to compute Alpha/Beta Epoch counts
   - Capture only files where TP/FP/FN differ

2. Dump boundary diagnostics for each mismatched file
   - File duration (rounded), end of last ref event
   - Number of sampled midpoints and last midpoint
   - Labels around boundaries in both ref/hyp at last few samples

3. Reconcile condition(s)
   - If Beta skipped the exact-end sample, adjust sampling epsilon
   - If we include an extra sample, match NEDC’s effective stop_time
   - Ensure empty-side files get a full-length background span prior to sampling (like NEDC augmentation)

4. Re-run Epoch on the mismatched subset → confirm deltas collapse to zero

## Tooling to add (proposed)

- scripts/localize_epoch_mismatches.py
  - Reads SSOT files and/or recomputes per-file
  - Writes diagnostics JSON per mismatched file under output/parity_epoch_debug/

## Current SSOT

- SSOT_ALPHA.json – parsed from NEDC summary.txt (authoritative)
- SSOT_BETA.json – produced by run_beta_batch.py (+ IRA via run_beta_ira.py)

Once mismatches are localized, we will patch EpochScorer at the root cause (instead of papering over at comparison time) and re-confirm exact parity.

