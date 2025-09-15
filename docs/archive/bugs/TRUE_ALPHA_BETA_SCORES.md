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

## TRUE SCORES – ALPHA AND BETA COMPLETE

### TAES Algorithm
- Alpha: TP=133.84, FP=552.77, FN=941.16, Sens=12.45%, FA/24h=30.46
- Beta:  TP=133.84, FP=552.77, FN=941.16, Sens=12.45%, FA/24h=30.46
- Parity: ✅ Exact

### EPOCH Algorithm
- Alpha: TP=33704.00, FP=18816.00, FN=250459.00, Sens=11.8608%, FA/24h=259.2257
- Beta:  TP=33713.00, FP=18829.00, FN=250450.00, Sens=11.8640%, FA/24h=259.4048
- Parity: ⚠️ Near (ΔTP=+9, ΔFP=+13, ΔFN=−9)

### OVERLAP Algorithm
- Alpha: TP=253.00, FP=536.00, FN=822.00, Sens=23.5349%, FA/24h=29.5376
- Beta:  TP=253.00, FP=536.00, FN=822.00, Sens=23.5349%, FA/24h=29.5376
- Parity: ✅ Exact

### DP ALIGNMENT Algorithm
- Alpha: TP=328.00, FP=966.00, FN=747.00, Sens=30.5116%, FA/24h=53.2338
- Beta:  TP=328.00, FP=966.00, FN=747.00, Sens=30.5116%, FA/24h=53.2338
- Parity: ✅ Exact

### IRA (Inter‑Rater Agreement)
- Alpha: Multi‑Class Kappa=0.1887, per‑label kappa(seiz/bckg)=0.1887
- Beta:  Multi‑Class Kappa=0.1888, per‑label kappa(seiz/bckg)=0.1888
- Parity: ✅ Exact (≤ 1e‑4 tolerance)

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

### Hardcoded values vs true SSOT
The hardcoded Alpha values in `ultimate_parity_test.py` happen to match this dataset for most algorithms,
but we no longer trust or use them. The SSOT is derived from running the real NEDC tool and our Beta on
the same input lists and is stored in `SSOT_ALPHA.json` and `SSOT_BETA.json`.

## NEXT STEPS

1. ✅ Fix NEDC tool execution (path resolution)
2. ✅ Compare Alpha vs Beta using SSOT files
3. 🔎 Investigate Epoch difference – see EPOCH_P0_BUG.md
