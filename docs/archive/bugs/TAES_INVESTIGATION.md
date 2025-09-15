# TAES Algorithm Investigation

## Issue Summary
The TAES algorithm shows a tiny numerical difference between Alpha (NEDC v6.0.0) and Beta (our implementation):
- **Difference**: 0.000039%
- **Status**: Within floating-point precision tolerance but worth investigating
- **Impact**: Negligible for practical purposes but understanding the source improves confidence

## Current Parity Status
```
Algorithm  | Difference | Status
-----------|------------|------------------
TAES       | 0.000039%  | ✅ PERFECT PARITY
Epoch      | 0.0000%    | ✅ PERFECT PARITY
Overlap    | 0.0000%    | ✅ PERFECT PARITY
DP         | 0.0000%    | ✅ PERFECT PARITY
IRA        | 0.0000%    | ✅ PERFECT MATCH
```

## TAES Metrics Comparison

### Actual Test Output
```
TAES:
  Alpha: TP=133.84, FP=552.77, FN=941.16
  Beta:  TP=133.84, FP=552.77, FN=941.16
  Diff:  TP=0.0014, FP=0.0011, FN=0.0014  <-- REAL DIFFERENCES!

  Alpha: Sensitivity=12.4504%, FA/24h=30.4617
  Beta:  Sensitivity=12.4504%, FA/24h=30.4617
  Diff:  Sens=0.000039%, FA=0.000011
```

### Key Finding: ACTUAL NUMERICAL DIFFERENCES EXIST
- **TP difference: 0.0014** (small but non-zero!)
- **FP difference: 0.0011** (small but non-zero!)
- **FN difference: 0.0014** (small but non-zero!)
- **Sensitivity difference: 0.000039%**
- **FA/24h difference: 0.000011**

### This is NOT acceptable!
Since NEDC is pure Python (no compiled code, no BLAS/LAPACK variations), we should achieve **EXACT** numerical match. Any difference indicates:
1. Different mathematical operations
2. Different order of operations
3. Bug in our implementation
4. Different handling of edge cases

## Investigation Plan

### 1. Verify Comparison Calculation
- [ ] Check `scripts/compare_parity.py` for how it calculates differences
- [ ] Look for any rounding or precision issues in percentage calculation
- [ ] Verify if difference is real or a comparison artifact

### 2. Deep Dive into TAES Implementation
- [ ] Review `nedc_bench/algorithms/taes.py`
- [ ] Compare with NEDC's `nedc_eeg_eval/v6.0.0/lib/nedc_eval_tools.py`
- [ ] Check floating-point operations order (can affect precision)

### 3. Trace Individual File Processing
- [ ] Run TAES on single files to isolate where difference occurs
- [ ] Compare intermediate calculations, not just final sums
- [ ] Check for any files with edge cases

### 4. Floating-Point Considerations
- [ ] Order of operations (addition is not associative in floating-point)
- [ ] Different NumPy/SciPy versions between environments
- [ ] CPU architecture differences (unlikely but possible)

## Code Locations

### Beta Implementation
- Main: `nedc_bench/algorithms/taes.py`
- Tests: `tests/algorithms/test_taes_algorithm.py`
- Integration: `nedc_bench/orchestration/dual_pipeline.py`

### Alpha Implementation
- NEDC: `nedc_eeg_eval/v6.0.0/lib/nedc_eval_tools.py` (taes scoring)
- Wrapper: `nedc_bench/alpha/wrapper/nedc_alpha_wrapper.py`

### Comparison Scripts
- `scripts/ultimate_parity_test.py` - Main parity test
- `scripts/compare_parity.py` - Detailed comparison
- `parity_snapshot.json` - Stored results

## Hypothesis

Given that all displayed values are **exactly identical**, the most likely explanation is:

1. **Display Artifact**: The 0.000039% might come from how we calculate the percentage difference when values are extremely close to machine epsilon.

2. **Intermediate Precision**: Some intermediate calculation (perhaps in duration or time calculations) has a tiny difference that gets averaged out in the final sum.

3. **False Positive**: The difference calculation itself might have a bug when dealing with numbers this close.

## Next Steps

1. **Immediate**: Check if the 0.000039% is even real by examining the comparison code
2. **Short-term**: If real, trace through single file to find where it originates
3. **Long-term**: Document as "within machine precision" if difference is genuinely this small

## Resolution Criteria

This investigation can be closed when:
- [ ] Source of the 0.000039% difference is identified
- [ ] Confirmed whether it's real or an artifact
- [ ] Documented the finding for future reference
- [ ] Updated comparison scripts if needed

## Notes

- Even 0.000039% difference is well within acceptable tolerance for scientific computing
- IEEE 754 double precision has ~15-17 decimal digits of precision
- For medical/scientific purposes, this difference is completely negligible
- All other algorithms show perfect 0.0000% match, suggesting our implementation is solid

## Investigation Results

### Root Cause Identified! ✅

The "difference" was **not in our implementation** but in the test script itself!

#### The Problem
The `ultimate_parity_test.py` script had hardcoded **rounded** Alpha values:
```python
# BEFORE (incorrect):
"taes": AlgorithmResult(133.84, 552.77, 941.16, 12.4504, 30.4617, "TAES")
```

But the actual Alpha values have more precision:
```python
# ACTUAL values:
"taes": AlgorithmResult(133.84137545872733, 552.7689020231412, 941.1586245412731, ...)
```

When Beta calculated exact values and compared them to the rounded hardcoded values, we got differences like:
- TP difference: 0.00137545872732... ≈ 0.0014
- FP difference: 0.00109797685877... ≈ 0.0011
- FN difference: 0.00137545872689... ≈ 0.0014

#### The Solution
Fixed `ultimate_parity_test.py` to use exact values from `parity_snapshot.json`:
```python
# AFTER (correct):
"taes": AlgorithmResult(
    133.84137545872733, 552.7689020231412, 941.1586245412731,
    12.450360507788584, 30.461710971183077, "TAES"
)
```

### Verification
After the fix:
```
TAES:
  Alpha: TP=133.84, FP=552.77, FN=941.16
  Beta:  TP=133.84, FP=552.77, FN=941.16
  Diff:  TP=0.0000, FP=0.0000, FN=0.0000  <-- EXACTLY ZERO!

  ✅ PERFECT PARITY ACHIEVED!
```

## Conclusion

**There was never a mathematical difference in the TAES implementation!**

Our Beta implementation produces **exactly identical** results to NEDC v6.0.0 Alpha. The perceived difference was purely a testing artifact from using rounded hardcoded values instead of exact values.

### Key Lessons
1. **Always use exact values** in test comparisons, not rounded approximations
2. **Pure Python implementations should achieve exact parity** - any difference indicates a bug (either in implementation or testing)
3. **Floating-point precision matters** - even small rounding in test data can create false positives

### Status
- ✅ TAES has **100% exact parity** with NEDC v6.0.0
- ✅ All 5 algorithms now show perfect 0.0000 differences
- ✅ Investigation complete - no fixes needed to the actual algorithm implementations

The fix has been applied to `scripts/ultimate_parity_test.py` and all algorithms now show perfect parity.