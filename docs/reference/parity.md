# Parity Status & Verification

This page records the authoritative parity status between the modern
`nedc_bench` algorithms and the legacy NEDC v6.0.0 stack. It consolidates the
findings that previously lived in `docs/archive/status/CURRENT_STATUS.md` and
`docs/archive/bugs/FINAL_PARITY_RESULTS.md`.

## Current Status (2025-10-10)

| Algorithm | Parity Status | Alpha vs Beta Match | Notes |
| --- | --- | --- | --- |
| TAES | ✅ Exact | TP/FP/FN/Sens/FA match | Duration bug fixed; FA/24h aligns at 30.46. |
| Epoch | ✅ Exact | TP/FP/FN/Sens/FA match | Event augmentation + parameter loading resolved drift. |
| Overlap | ✅ Exact | TP/FP/FN/Sens/FA match | Boundary handling identical to NEDC. |
| DP Alignment | ✅ Exact | TP/FP/FN/Sens/FA match | Sequence expansion mirrors legacy implementation. |
| IRA | ✅ Exact | Kappa within tolerance | Stochastic tie-break handling validated. |

The metrics above are derived from the 1,832-file dataset in
`data/csv_bi_parity/csv_bi_export_clean/` and match the canonical values:

```
TAES:   TP=133.84,   FP=552.77,  FN=941.16,  FA/24h=30.46
Epoch:  TP=33704.00, FP=18816.00, FN=250459.00, FA/24h=259.23
Overlap: TP=253.00, FP=536.00,   FN=822.00
DP:     TP=328.00,   FP=966.00,  FN=747.00
IRA:    Kappa=0.1888 (matches legacy within rounding tolerance)
```

## How to Verify Parity

### 1. Run the automated parity tests

```bash
pytest tests/validation/test_integration_parity.py -xvs
```

These tests execute every algorithm against the parity fixtures and confirm the
metrics reported by the orchestration layer. They incorporate the methodology
captured in the former `PARITY_TESTING_SSOT.md` document.

### 2. Execute the full parity comparison script

```bash
PYTHONPATH=src python scripts/ultimate_parity_test.py
```

The script walks all 1,832 reference/hypothesis pairs and compares Beta against
the Alpha outputs that live in `data/csv_bi_parity/csv_bi_export_clean/`. Use
`--subset <N>` to spot-check a smaller batch.

### 3. Cross-check the cached results

The canonical parity snapshots (`SSOT_ALPHA.json` and `SSOT_BETA.json`) are kept
under version control. Review them when auditing regressions or preparing
release notes.

## Recent Fix History

Key remediation notes (originally documented across the archived bug reports):

- **TAES Duration (P0)** – `P0_CRITICAL_BUG_DURATION.md` → Duration now sums
  across recordings, yielding the correct FA/24h calculation.
- **Epoch Event Augmentation** – `EPOCH_BUG_FIXED.md` → Gap-filling matches
  NEDC behaviour, restoring TP counts.
- **DP Alignment Input Conversion** – `CRITICAL_BUGS_ALL_ALGORITHMS.md` →
  Sequence expansion rewrites to epoch labels rather than synthetic events.
- **Alpha Wrapper Boot Failures** – `ALPHA_WRAPPER_P0_BUG.md` → Environment
  setup guards now ensure vendored NEDC assets can be invoked on demand.

Each algorithm page in `docs/algorithms/` contains deeper troubleshooting notes
and links to the tests that enforce these fixes.

## Maintaining Parity

1. Update the table above whenever metrics change—include evidence from both the
   pytest suite and the parity script.
2. When altering algorithm implementations or orchestrators, add or adjust tests
   in `tests/validation/test_integration_parity.py` to cover the new behaviour.
3. Keep the snapshot JSON files current by re-running the parity script before
   releases; document changes in the release notes.
4. Archive legacy narratives (if needed) by referencing pull requests instead of
   duplicating long-form history in this page.
