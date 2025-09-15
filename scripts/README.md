# Scripts Directory

## 🚨 CRITICAL: NEDC Path Resolution Issues 🚨

### THE PROBLEM THAT KEEPS BITING US

The NEDC tool has confusing path requirements because `run_nedc.sh`:
1. **Changes directory** to `nedc_eeg_eval/v6.0.0/`
2. **THEN** looks for list files

This means:
- List file paths given to `run_nedc.sh` are relative to PROJECT ROOT
- But CONTENTS of list files need paths relative to NEDC directory

### THE SOLUTION

```bash
# CORRECT WAY TO RUN NEDC:

# 1. Create list files IN the NEDC directory structure
mkdir -p nedc_eeg_eval/v6.0.0/custom_lists/

# 2. List contents use ../../ to get back to project root
echo '../../data/csv_bi_parity/csv_bi_export_clean/ref/file.csv_bi' > \
     nedc_eeg_eval/v6.0.0/custom_lists/ref.list

# 3. Run from project root with path relative to NEDC dir
./run_nedc.sh custom_lists/ref.list custom_lists/hyp.list
```

### WRONG WAYS (THAT WILL FAIL)

```bash
# ❌ WRONG: Absolute paths in list files
echo '/mnt/c/Users/.../ref/file.csv_bi' > ref.list

# ❌ WRONG: List files in project root
./run_nedc.sh ref.list hyp.list  # Can't find from NEDC dir!

# ❌ WRONG: Using $NEDC_NFC in paths (doesn't expand in NEDC)
echo '$NEDC_NFC/data/ref/file.csv_bi' > ref.list
```

## Core Scripts

### Runtime Scripts (No Hardcoding!)

- **`create_runtime_lists.py`** - Creates list files programmatically from actual CSV_BI files
- **`run_beta_batch.py`** - Runs our Beta implementation on all files
- **`ultimate_parity_test.py`** - Main parity testing script (but has hardcoded Alpha values)
- **`test_parity_subset.py`** - Quick test on 10 files for development

### Deleted Slop Scripts

These were removed because they were broken or redundant:
- ~~run_alpha_batch.sh~~ - Tried to execute CSV files as bash commands 🤦
- ~~alpha_beta_totals.py~~ - Overcomplicated
- ~~run_single_algo_parity.py~~ - Redundant
- ~~run_true_parity_test.py~~ - Redundant

## How to Run Parity Tests

### 1. Run Beta (Our Implementation)
```bash
python scripts/run_beta_batch.py
# Creates: SSOT_BETA.json
```

### 2. Run Alpha (NEDC v6.0.0)
```bash
# First create proper list files
python scripts/create_nedc_lists.py  # TODO: Create this!

# Then run NEDC
./run_nedc.sh nedc_lists/ref.list nedc_lists/hyp.list
# Output: nedc_eeg_eval/v6.0.0/output/summary.txt
```

### 3. Compare Results
Check `TRUE_ALPHA_BETA_SCORES.md` for comparison.

## Common Issues

### "File not found" errors from NEDC
- Check path resolution (see top of this README)
- List files must be findable from `nedc_eeg_eval/v6.0.0/`
- Contents must use relative paths from that directory

### Module import errors
- Ensure `NEDC_NFC` and `PYTHONPATH` are set
- Run from project root, not from subdirectories

### Beta runs but no output
- Check `beta_output.log`
- Takes several minutes for 1832 files
- Use `ps aux | grep python` to check if still running