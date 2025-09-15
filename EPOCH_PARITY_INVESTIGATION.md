# EPOCH PARITY INVESTIGATION
## The 99.97% Question: Why Not 100%?

**Date:** September 15, 2025
**Issue:** Epoch algorithm shows 99.97% parity (9 TP difference out of 33,713) while all other algorithms achieve 100% parity

## The Fundamental Question

Both NEDC v6.0.0 and our nedc-bench implementation are written in Python. Both use:
- Same epoch duration (0.25 seconds)
- Same null class ("bckg")
- Same label normalization
- Same file duration values from CSV_BI headers
- Same numpy/scipy libraries

**So why isn't parity exactly 100.0000%?**

## Current Results from 1832 File Pairs

```
Algorithm    | TP Diff | FP Diff | FN Diff | Parity %
-------------|---------|---------|---------|----------
TAES         | 0.01    | 0.04    | 0.01    | 100.00%
DP Alignment | 0.00    | 0.00    | 0.00    | 100.00%
Overlap      | 0.00    | 0.00    | 0.00    | 100.00%
Epoch        | 9.00    | 13.00   | 9.00    | 99.97%
```

## Hypotheses to Investigate

### 1. Floating-Point Precision at Boundaries
**Question:** Are we handling file duration boundaries differently?
- NEDC uses: `t > file_duration + 1e-10` (line 484 of nedc_eeg_eval_epoch.py)
- We use: `t > file_duration + 1e-12`
- **Investigation needed:** Check exact epsilon value in NEDC source

### 2. Sample Time Generation
**Question:** Is the midpoint calculation exactly identical?
- NEDC: `half_epoch = epoch_duration / 2.0`
- Ours: `half = self.epoch_duration / 2.0`
- **Investigation needed:** Trace exact loop construction

### 3. Event Boundary Comparison
**Question:** Are we using identical comparison operators?
- Inclusive vs exclusive boundaries: `>=` vs `>`, `<=` vs `<`
- **Investigation needed:** Check _time_to_index implementation

### 4. Compression Algorithm
**Question:** Is joint compression implemented identically?
- Sentinel handling with leading/trailing nulls
- Duplicate detection logic
- **Investigation needed:** Line-by-line comparison

### 5. File Duration Parsing
**Question:** Are we reading duration from CSV_BI headers identically?
- Float parsing precision
- Rounding behavior
- **Investigation needed:** Check AnnotationFile.from_csv_bi

### 6. Label Mapping Timing
**Question:** When do we normalize labels?
- Before or after epochization?
- Case sensitivity handling
- **Investigation needed:** Check orchestration flow

## Investigation Plan

1. **Extract exact NEDC epoch implementation**
   - [ ] Copy exact epsilon value (1e-10 vs 1e-12)
   - [ ] Copy exact comparison operators
   - [ ] Copy exact loop structure

2. **Add debug logging**
   - [ ] Log sample times for problematic files
   - [ ] Log event boundaries
   - [ ] Log compression steps

3. **Identify specific files with differences**
   - [ ] Run file-by-file comparison
   - [ ] Find which files contribute to the 9 TP difference
   - [ ] Analyze those specific cases

4. **Test boundary conditions**
   - [ ] Files where duration is exact multiple of epoch_duration
   - [ ] Files with events ending exactly at file_duration
   - [ ] Files with very short durations

## Key Code Locations

### NEDC Source (Alpha)
- Main epoch: `nedc_eeg_eval/v6.0.0/src/nedc_eeg_eval_epoch.py`
- Time sampling: Lines 482-492
- Compression: Lines 600-610
- Confusion matrix: Lines 690-723

### Our Implementation (Beta)
- Main epoch: `nedc_bench/algorithms/epoch.py`
- Time sampling: `_sample_times()` method (lines 179-190)
- Compression: `_compress_joint()` method (lines 199-209)
- Confusion matrix: `score()` method (lines 107-177)

## The Answer Will Be One Of:

1. **Different epsilon in boundary check** (most likely)
2. **Different operator in time_to_index** (likely)
3. **Different float parsing precision** (possible)
4. **Different order of operations causing rounding** (possible)
5. **Bug in one implementation** (unlikely but possible)

## Next Steps

We need to:
1. Compare line-by-line with NEDC source
2. Add detailed logging to both implementations
3. Run on a small subset to identify exact divergence point
4. Fix the difference to achieve 100.0000% parity

---

**Note:** 99.97% parity might seem "good enough" but if both implementations are Python, we should be able to achieve EXACT parity. The 0.03% difference represents a subtle implementation detail that we need to identify and fix.