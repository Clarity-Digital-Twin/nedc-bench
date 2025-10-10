# PARITY TESTING: SINGLE SOURCE OF TRUTH

## The Baseline Problem and Solution

**Created:** September 15, 2025
**Purpose:** Define the CORRECT way to test Alpha (NEDC v6.0.0) vs Beta (our implementation) parity

## THE PROBLEM

We have **WRONG HARDCODED BASELINE VALUES** in `scripts/ultimate_parity_test.py`:

```python
def get_alpha_metrics() -> dict[str, AlgorithmResult]:
    """Extract Alpha results from the summary file"""
    return {
        "taes": AlgorithmResult(133.84, 552.77, 941.16, 12.4504, 30.4617, "TAES"),
        "dp": AlgorithmResult(328.00, 966.00, 747.00, 30.5116, 53.2338, "DP Alignment"),
        "epoch": AlgorithmResult(
            33704.00, 18816.00, 250459.00, 11.8608, 259.2257, "Epoch"
        ),
        "ovlp": AlgorithmResult(253.00, 536.00, 822.00, 23.5349, 29.5376, "Overlap"),
    }
```

These values show **11.86% sensitivity for Epoch** but the README for our actual test data says:

- **Expected:** Sensitivity: 45.63%, FA/24h: 100.06
- **Hardcoded:** Sensitivity: 11.86%, FA/24h: 259.23

**THESE ARE FROM A DIFFERENT DATASET!**

## THE DATA WE HAVE

### Location: `/data/csv_bi_parity/csv_bi_export_clean/`

- **1832 CSV_BI file pairs** from SeizureTransformer (Wu et al. 2025)
- **Source:** Temple University Hospital EEG Seizure Corpus (TUSZ) DEV set
- **Configuration:** DEFAULT (BASELINE) - NO PARAMETER TUNING

### File Structure:

```
csv_bi_export_clean/
├── ref/          # 1832 reference (ground truth) CSV_BI files
├── hyp/          # 1832 hypothesis (model output) CSV_BI files
├── lists/
│   ├── ref.list  # Points to SeizureTransformer location (WRONG!)
│   └── hyp.list  # Points to SeizureTransformer location (WRONG!)
└── README.txt    # Documents expected metrics
```

### CRITICAL ISSUE: List Files Point to Wrong Location!

The list files point to:

```
/mnt/c/Users/JJ/Desktop/Clarity-Digital-Twin/SeizureTransformer/experiments/dev/baseline/nedc_results/
```

But our actual data is in:

```
/mnt/c/Users/JJ/Desktop/Clarity-Digital-Twin/nedc-bench/data/csv_bi_parity/csv_bi_export_clean/
```

## THE SOLUTION: PROPER ALPHA/BETA TESTING

### Step 1: Fix the List Files

Create runtime list files that point to our actual data within this repo.

### Step 2: Run NEDC v6.0.0 (Alpha Pipeline)

```bash
# Create runtime lists (reuse csv_bi_export_clean/lists/*.list names)
python scripts/create_runtime_lists.py

# Run actual NEDC v6.0.0 on our data (from project root)
./run_nedc.sh runtime_lists/ref_complete.list runtime_lists/hyp_complete.list

# Parse results to SSOT_ALPHA.json (also includes IRA kappa)
python scripts/parse_alpha_results.py
```

### Step 3: Run Our Implementation (Beta Pipeline)

```bash
# Run all four count-based algorithms (TAES, EPOCH, OVLP, DP)
python scripts/run_beta_batch.py

# Add IRA (kappa) to SSOT_BETA.json
python scripts/run_beta_ira.py
```

### Step 4: Compare ACTUAL Results

- Alpha results: From NEDC v6.0.0 output on THIS dataset
- Beta results: From our implementation on THIS dataset
- NOT hardcoded values from unknown dataset!

## EXPECTED OUTCOMES

Based on README.txt, we SHOULD see (for binary scoring):

- Sensitivity: ~45.63%
- False Alarms/24h: ~100.06

If we see ~11.86% sensitivity, we're using the WRONG dataset or configuration.

## ACTION ITEMS

1. ✅ STOP using hardcoded baseline values
1. ✅ CREATE runtime list files programmatically
1. ✅ RUN actual NEDC v6.0.0 on csv_bi_parity
1. ✅ CAPTURE those results as SSOT_ALPHA.json (with IRA)
1. ✅ CAPTURE Beta totals as SSOT_BETA.json (with IRA)
1. ✅ COMPARE via scripts/compare_parity.py
1. ⬜ Optional: Update ultimate_parity_test.py to source SSOT files dynamically

## THE REAL PARITY TEST

```python
# Pseudocode for correct testing
def test_parity():
    # 1. Run NEDC v6.0.0 on dataset
    alpha_results = run_nedc_tool(ref_files, hyp_files)

    # 2. Run our implementation on SAME dataset
    beta_results = run_our_implementation(ref_files, hyp_files)

    # 3. Compare ACTUAL results
    for algo in ["taes", "epoch", "ovlp", "dp"]:
        diff = abs(alpha_results[algo] - beta_results[algo])
        assert diff < 0.001, f"Parity failed for {algo}"
```

## CONCLUSION

We've been comparing our results against **WRONG BASELINE VALUES** from a different dataset.
To achieve true parity testing, we must:

1. Use the SAME dataset for both Alpha and Beta
1. Run ACTUAL NEDC v6.0.0 to get true baseline
1. Compare against those REAL results, not hardcoded values

The 99.97% "parity" on Epoch is meaningless if we're comparing against wrong baseline.
We need to establish the TRUE baseline first!
