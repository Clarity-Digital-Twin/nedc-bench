# TRUE ALPHA vs BETA SCORES
## Single Source of Truth - No Hardcoded Values

**Dataset:** csv_bi_parity/csv_bi_export_clean (1832 file pairs)
**Source:** SeizureTransformer on TUSZ DEV set
**Date:** September 15, 2025

## Test Execution Plan

Running each algorithm separately in tmux to avoid timeout:

```bash
tmux new-session -d -s taes 'python scripts/run_single_algo_parity.py taes'
tmux new-session -d -s epoch 'python scripts/run_single_algo_parity.py epoch'
tmux new-session -d -s ovlp 'python scripts/run_single_algo_parity.py ovlp'
tmux new-session -d -s dp 'python scripts/run_single_algo_parity.py dp'
```

## TRUE SCORES - BETA COMPLETE!

### TAES Algorithm
- **Status:** ✅ Beta Complete, Alpha TBD
- **Alpha (NEDC v6.0.0):**
  - TP: TBD (need to run NEDC properly)
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Beta (Our Implementation):**
  - TP: 133.84
  - FP: 552.77
  - FN: 941.16
  - Sensitivity: 12.45%
  - FA/24h: 30.46
- **Parity:** TBD (waiting for Alpha)

### EPOCH Algorithm
- **Status:** ✅ Beta Complete, Alpha TBD
- **Alpha (NEDC v6.0.0):**
  - TP: TBD (need to run NEDC properly)
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Beta (Our Implementation):**
  - TP: 33713.00
  - FP: 18829.00
  - FN: 250450.00
  - Sensitivity: 11.86%
  - FA/24h: 259.40
- **Parity:** TBD (waiting for Alpha)

### OVERLAP Algorithm
- **Status:** ✅ Beta Complete, Alpha TBD
- **Alpha (NEDC v6.0.0):**
  - TP: TBD (need to run NEDC properly)
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Beta (Our Implementation):**
  - TP: 253.00
  - FP: 536.00
  - FN: 822.00
  - Sensitivity: 23.53%
  - FA/24h: 29.54
- **Parity:** TBD (waiting for Alpha)

### DP ALIGNMENT Algorithm
- **Status:** ✅ Beta Complete, Alpha TBD
- **Alpha (NEDC v6.0.0):**
  - TP: TBD (need to run NEDC properly)
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Beta (Our Implementation):**
  - TP: 328.00
  - FP: 966.00
  - FN: 747.00
  - Sensitivity: 30.51%
  - FA/24h: 53.23
- **Parity:** TBD (waiting for Alpha)

## COMPARISON WITH HARDCODED VALUES

The hardcoded values in `ultimate_parity_test.py` were:
```python
"taes": AlgorithmResult(133.84, 552.77, 941.16, 12.4504, 30.4617, "TAES"),
"dp": AlgorithmResult(328.00, 966.00, 747.00, 30.5116, 53.2338, "DP Alignment"),
"epoch": AlgorithmResult(33704.00, 18816.00, 250459.00, 11.8608, 259.2257, "Epoch"),
"ovlp": AlgorithmResult(253.00, 536.00, 822.00, 23.5349, 29.5376, "Overlap"),
```

**These will be compared with TRUE scores once available.**

## KEY FINDINGS SO FAR

### Beta Results Match the Hardcoded Values!
Our Beta implementation produces:
- TAES: 133.84 TP (matches hardcoded 133.84)
- EPOCH: 33713 TP (close to hardcoded 33704)
- OVERLAP: 253 TP (matches hardcoded 253)
- DP: 328 TP (matches hardcoded 328)

This means the hardcoded values WERE from this dataset, but we still need Alpha to confirm parity!

## NEXT STEPS

1. **Fix NEDC tool execution** - Need to get Alpha running properly
2. **Compare Alpha vs Beta** - Once we have true Alpha scores
3. **Investigate Epoch difference** - 9 TP difference (33713 vs 33704)