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

## TRUE SCORES (To Be Filled)

### TAES Algorithm
- **Status:** ⏳ Running...
- **Alpha (NEDC v6.0.0):**
  - TP: TBD
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Beta (Our Implementation):**
  - TP: TBD
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Parity:** TBD

### EPOCH Algorithm
- **Status:** ⏳ Running...
- **Alpha (NEDC v6.0.0):**
  - TP: TBD
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Beta (Our Implementation):**
  - TP: TBD
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Parity:** TBD

### OVERLAP Algorithm
- **Status:** ⏳ Running...
- **Alpha (NEDC v6.0.0):**
  - TP: TBD
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Beta (Our Implementation):**
  - TP: TBD
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Parity:** TBD

### DP ALIGNMENT Algorithm
- **Status:** ⏳ Running...
- **Alpha (NEDC v6.0.0):**
  - TP: TBD
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Beta (Our Implementation):**
  - TP: TBD
  - FP: TBD
  - FN: TBD
  - Sensitivity: TBD
  - FA/24h: TBD
- **Parity:** TBD

## COMPARISON WITH HARDCODED VALUES

The hardcoded values in `ultimate_parity_test.py` were:
```python
"taes": AlgorithmResult(133.84, 552.77, 941.16, 12.4504, 30.4617, "TAES"),
"dp": AlgorithmResult(328.00, 966.00, 747.00, 30.5116, 53.2338, "DP Alignment"),
"epoch": AlgorithmResult(33704.00, 18816.00, 250459.00, 11.8608, 259.2257, "Epoch"),
"ovlp": AlgorithmResult(253.00, 536.00, 822.00, 23.5349, 29.5376, "Overlap"),
```

**These will be compared with TRUE scores once available.**

## FINDINGS

(To be updated after test completion)

## CONCLUSION

(To be updated after test completion)