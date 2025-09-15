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

### Runtime Scripts (No hardcoding)

- `create_runtime_lists.py` – Create list files under `runtime_lists/` from repo data
- `run_beta_batch.py` – Run Beta (TAES, EPOCH, OVLP, DP) and write SSOT_BETA.json
- `run_beta_ira.py` – Append IRA (kappa) to SSOT_BETA.json
- `parse_alpha_results.py` – Parse NEDC summary.txt → SSOT_ALPHA.json (incl. IRA)
- `compare_parity.py` – Compare SSOT_ALPHA.json vs SSOT_BETA.json (handles IRA)
- `ultimate_parity_test.py` – Legacy harness with hardcoded Alpha (ok for Beta aggregation only)
- `test_parity_subset.py` – Quick subset harness for development

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
# Create runtime lists (paths are relative to the NEDC dir)
python scripts/create_runtime_lists.py

# Run NEDC on the same lists
./run_nedc.sh runtime_lists/ref_complete.list runtime_lists/hyp_complete.list
# Output is written under nedc_eeg_eval/v6.0.0/output/

# Parse into SSOT_ALPHA.json (also captures IRA)
python scripts/parse_alpha_results.py
```

### 3. Compare Results
```bash
python scripts/compare_parity.py
```
See also: `FINAL_PARITY_RESULTS.md` for current status.

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
