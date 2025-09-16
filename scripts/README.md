# NEDC-BENCH Scripts

Essential scripts for running and validating the dual-pipeline EEG evaluation platform.

## 🚀 Quick Start

```bash
# Run complete parity validation (all algorithms)
python scripts/ultimate_parity_test.py

# Test on subset (faster for development)
python scripts/ultimate_parity_test.py --subset 10

# Run individual pipelines
python scripts/run_alpha_complete.py  # NEDC v6.0.0
python scripts/run_beta_batch.py       # Our implementation
```

## 📁 Script Inventory

### Core Validation Scripts

#### `ultimate_parity_test.py`

**Purpose:** Comprehensive parity validation of all 5 algorithms
**Usage:**

```bash
python scripts/ultimate_parity_test.py [--subset N] [--verbose]
```

**Output:** Shows exact differences between Alpha and Beta for each algorithm

#### `compare_parity.py`

**Purpose:** Simple comparison of pre-computed SSOT JSON files
**Usage:**

```bash
# First generate the JSON files
python scripts/run_alpha_complete.py  # Creates SSOT_ALPHA.json
python scripts/run_beta_batch.py      # Creates SSOT_BETA.json

# Then compare
python scripts/compare_parity.py
```

### Pipeline Execution Scripts

#### `run_alpha_complete.py`

**Purpose:** Execute NEDC v6.0.0 on full dataset
**Details:**

- Runs all 5 algorithms via the original NEDC tool
- Generates text output in `output/` directory
- Creates `SSOT_ALPHA.json` via parse_alpha_results.py

#### `run_beta_batch.py`

**Purpose:** Execute our Beta implementation on full dataset
**Details:**

- Runs all 5 algorithms using our Python implementation
- Directly outputs `SSOT_BETA.json`
- Much faster than Alpha (~10x speedup)

### Utility Scripts

#### `parse_alpha_results.py`

**Purpose:** Parse NEDC text output into structured JSON
**Usage:** Automatically called by `run_alpha_complete.py`
**Input:** Text files in `output/` directory
**Output:** `SSOT_ALPHA.json`

#### `create_file_lists.py`

**Purpose:** Generate list files for batch processing
**Usage:**

```bash
# Create standard lists
python scripts/create_file_lists.py

# Create subset for testing
python scripts/create_file_lists.py --subset 10

# Create with custom paths for NEDC
python scripts/create_file_lists.py --prefix "../../data/csv_bi_parity/csv_bi_export_clean"
```

## 🎯 Common Workflows

### 1. Full Parity Validation

```bash
# Complete test to verify 100% parity
python scripts/ultimate_parity_test.py
```

### 2. Quick Development Test

```bash
# Test on 10 files for rapid iteration
python scripts/ultimate_parity_test.py --subset 10
```

### 3. Debug Single Algorithm

```bash
# Run only Beta to check specific algorithm
python -c "
from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.models.annotations import AnnotationFile
from pathlib import Path

ref = AnnotationFile.from_csv_bi(Path('data/csv_bi_parity/csv_bi_export_clean/ref/aaaaaajy_s001_t000.csv_bi'))
hyp = AnnotationFile.from_csv_bi(Path('data/csv_bi_parity/csv_bi_export_clean/hyp/aaaaaajy_s001_t000.csv_bi'))

scorer = TAESScorer(target_label='seiz')
result = scorer.score(ref.events, hyp.events)
print(f'TP: {result.true_positives}, FP: {result.false_positives}, FN: {result.false_negatives}')
"
```

### 4. Regenerate Test Data

```bash
# If you need to regenerate Alpha results
python scripts/run_alpha_complete.py

# Parse the output
python scripts/parse_alpha_results.py

# Compare with Beta
python scripts/run_beta_batch.py
python scripts/compare_parity.py
```

## 📊 Expected Output

When running `ultimate_parity_test.py`, you should see:

```
================================================================================
🚀 ULTIMATE PARITY TEST - ALL 5 NEDC ALGORITHMS
================================================================================

Loading Alpha results...
Running Beta algorithms...
Processing 1832 file pairs for each algorithm...

TAES:
  Diff:  TP=0.0000, FP=0.0000, FN=0.0000
  ✅ PERFECT PARITY ACHIEVED!

Epoch:
  Diff:  TP=0.0000, FP=0.0000, FN=0.0000
  ✅ PERFECT PARITY ACHIEVED!

Overlap:
  Diff:  TP=0.0000, FP=0.0000, FN=0.0000
  ✅ PERFECT PARITY ACHIEVED!

DP:
  Diff:  TP=0.0000, FP=0.0000, FN=0.0000
  ✅ PERFECT PARITY ACHIEVED!

IRA:
  Diff:  Δkappa=0.0000
  ✅ PERFECT PARITY ACHIEVED!

🎉🎉🎉 100% PERFECT PARITY ACHIEVED! 🎉🎉🎉
```

## ⚠️ Important Notes

1. **Path Resolution**: The NEDC tool changes directory, so list files must use relative paths from `nedc_eeg_eval/v6.0.0/`

1. **Performance**:

   - Alpha pipeline: ~3-5 minutes for full dataset
   - Beta pipeline: ~20-30 seconds for full dataset

1. **Data Location**: All scripts expect test data in `data/csv_bi_parity/csv_bi_export_clean/`

1. **Environment**: Scripts automatically set NEDC environment variables (`NEDC_NFC`, `PYTHONPATH`)

## 🐛 Troubleshooting

### "File not found" errors

- Check path resolution (paths must be relative to `nedc_eeg_eval/v6.0.0/`)
- Use `create_file_lists.py` with appropriate `--prefix`

### Different results between Alpha and Beta

- Ensure you're using the latest code
- Check that `parity_snapshot.json` has exact values (not rounded)
- Run `ultimate_parity_test.py` for comprehensive validation

### Performance issues

- Use `--subset` flag for development
- Beta pipeline is ~10x faster, use it when possible
- Consider running algorithms individually for debugging
