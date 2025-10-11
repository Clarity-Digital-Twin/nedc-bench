# Git Data Management Strategy

**Date**: 2025-10-10
**Status**: ✅ Implemented
**Purpose**: Selective data management for OSS contributors

---

## Overview

This document explains what data is committed to git vs ignored, and why.

## What's COMMITTED to Git ✅

### 1. Validation Golden References (data/validation/)

**Files committed:**
- ✅ `SSOT_ALPHA.json` (670 bytes)
- ✅ `SSOT_BETA.json` (880 bytes)
- ✅ `parity_snapshot.json` (1.5 KB)
- ✅ `README.md` (3.4 KB)
- ✅ `.gitkeep` (0 bytes)

**Why committed:**
- **Tiny files** - Total < 7 KB
- **Critical dependencies** - Scripts reference these for parity validation
- **Regression baselines** - Prevent algorithm drift
- **OSS friendly** - Contributors can run parity tests immediately

**Scripts that depend on these:**
- `scripts/compare_parity.py` - Compares Alpha vs Beta
- `scripts/parse_alpha_results.py` - Generates Alpha golden data
- `scripts/run_alpha_complete.py` - Full Alpha pipeline
- `scripts/run_beta_batch.py` - Full Beta pipeline
- `scripts/ultimate_parity_test.py` - Comprehensive validation

---

## What's IGNORED from Git ❌

### 2. Parity Testing Data (data/csv_bi_parity/)

**Size**: 2.3 MB (1832 file pairs)
**Status**: ❌ Ignored via `.gitignore:141`

**Why ignored:**
- Too large for git (2.3 MB of CSV files)
- User-specific test data
- Can be regenerated or replaced with user's own data

**Directory structure preserved:**
- ✅ `.gitkeep` committed to maintain directory structure
- Users can download their own datasets

### 3. External Dataset (data/siena_scalp/)

**Size**: 14 GB (!!)
**Status**: ❌ Ignored via `.gitignore:143`

**Why ignored:**
- Massive external dataset (14 GB zip file)
- Not part of core functionality
- Users download separately from original source

**Users should:**
1. Download from: https://physionet.org/content/siena-scalp-eeg/1.0.0/
2. Place in `data/siena_scalp/` if needed
3. Not required for core parity validation

---

## Directory Structure

```
data/
├── csv_bi_parity/          # ❌ IGNORED (2.3 MB)
│   └── .gitkeep            # ✅ COMMITTED (preserves structure)
├── siena_scalp/            # ❌ IGNORED (14 GB)
│   └── [user downloads]
└── validation/             # ✅ FULLY COMMITTED
    ├── .gitkeep
    ├── README.md           # Documentation
    ├── SSOT_ALPHA.json     # Alpha golden reference
    ├── SSOT_BETA.json      # Beta golden reference
    └── parity_snapshot.json # Historical snapshot
```

---

## .gitignore Configuration

### Current Rules (lines 139-147)

```gitignore
# Data directory - selective inclusion
# Ignore large datasets but keep validation artifacts
data/csv_bi_parity/
!data/csv_bi_parity/.gitkeep
data/siena_scalp/

# EXPLICITLY KEEP (small, critical for scripts):
# - data/validation/*.json (parity golden references)
# - data/validation/README.md (documentation)
```

### How It Works

1. **Ignore large directories** - `data/csv_bi_parity/` and `data/siena_scalp/`
2. **Exception for structure** - `!data/csv_bi_parity/.gitkeep` preserves directory
3. **Default include** - `data/validation/` NOT in ignore list, so all files committed

---

## OSS Contributor Workflow

### Clone Repository
```bash
git clone https://github.com/Clarity-Digital-Twin/nedc-bench.git
cd nedc-bench
```

### What They Get Immediately ✅
- ✅ All source code
- ✅ Validation golden references (`data/validation/*.json`)
- ✅ Directory structure (via `.gitkeep`)
- ✅ Documentation

### What They Need to Add (Optional)
- ❌ Test datasets (if running full parity validation)
- ❌ External datasets (if needed for research)

### Quick Validation Test
```bash
# Works immediately without downloading datasets
python scripts/compare_parity.py
# ✅ Uses committed golden references

# Full validation requires test data
python scripts/ultimate_parity_test.py
# ⚠️ Needs csv_bi_parity data (user provides)
```

---

## File Size Comparison

| Path | Size | Status | Justification |
|------|------|--------|---------------|
| `data/validation/*.json` | 7 KB | ✅ Committed | Critical dependencies |
| `data/csv_bi_parity/` | 2.3 MB | ❌ Ignored | Too large, user-specific |
| `data/siena_scalp/` | 14 GB | ❌ Ignored | External dataset |

**Git repo size impact**: +7 KB (negligible)

---

## Best Practices Followed

### ✅ What We Did Right

1. **Commit critical artifacts** - Golden references needed by scripts
2. **Ignore large datasets** - Keep repo lean (< 100 MB)
3. **Preserve directory structure** - `.gitkeep` maintains expected paths
4. **Document everything** - Clear README in validation directory
5. **OSS friendly** - Contributors can run basic validation immediately

### 📚 Industry Standards

This follows ML/research project conventions:
- ✅ Small reference data → commit
- ✅ Large datasets → ignore + document how to obtain
- ✅ Model checkpoints → ignore + provide download links
- ✅ Generated artifacts → ignore
- ✅ Directory structure → preserve with `.gitkeep`

---

## Verification

### Check What's Tracked
```bash
git ls-files data/
# Should show:
# data/csv_bi_parity/.gitkeep
# data/validation/.gitkeep
# data/validation/README.md
# data/validation/SSOT_ALPHA.json
# data/validation/SSOT_BETA.json
# data/validation/parity_snapshot.json
```

### Check What's Ignored
```bash
git check-ignore -v data/siena_scalp/ data/csv_bi_parity/csv_bi_export_clean/
# Should show both are ignored
```

### Verify File Sizes
```bash
git ls-files data/ -s | awk '{print $4, $2}' | numfmt --field=2 --to=iec
# All files should be < 10 KB
```

---

## Migration Notes

### For Existing Contributors

If you previously had `data/` untracked:

1. **Pull latest changes**:
   ```bash
   git pull origin development
   ```

2. **Your local large datasets are preserved**:
   - `data/csv_bi_parity/` - Still ignored, won't be committed
   - `data/siena_scalp/` - Now explicitly ignored

3. **New files appear**:
   - `data/validation/*.json` - Now tracked in git

### For New Contributors

1. **Clone gets you**:
   - ✅ Validation golden references
   - ✅ All documentation
   - ✅ Complete source code

2. **To run full parity tests**:
   ```bash
   # Option 1: Use your own test data
   mkdir -p data/csv_bi_parity/ref data/csv_bi_parity/hyp
   # Add your CSV_BI files

   # Option 2: Download TUH corpus (requires access)
   # See docs/reference/datasets.md
   ```

---

## Related Documentation

- `.gitignore` - Full ignore rules
- `data/validation/README.md` - Validation data documentation
- `ROOT_CLEANUP_SUMMARY.md` - Root directory cleanup notes
- `CODEBASE_AUDIT_2025.md` - Comprehensive audit findings

---

## Summary

✅ **Selective git management implemented**
✅ **Critical 7 KB committed, 16 GB ignored**
✅ **OSS contributors can validate immediately**
✅ **Repository stays lean and fast to clone**
✅ **Directory structure preserved**
✅ **All dependencies satisfied**

**Result**: Perfect balance between reproducibility and repository size.

---

**Maintained by**: NEDC-BENCH Development Team
**Last Updated**: 2025-10-10
**Git Strategy**: Selective inclusion, documented exclusions
