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

### Alpha (NEDC v6.0.0)
```json
{
  "tp": 133.84137545872733,
  "fp": 552.7689020231412,
  "fn": 941.1586245412731,
  "sensitivity": 12.450360507788584,
  "fa_per_24h": 30.461710971183077
}
```

### Beta (Our Implementation)
```json
{
  "tp": 133.84137545872733,  // Exact match
  "fp": 552.7689020231412,   // Exact match
  "fn": 941.1586245412731,   // Exact match
  "sensitivity": 12.450360507788584,  // Exact match
  "fa_per_24h": 30.461710971183077   // Exact match
}
```

### Observation
Looking at the actual values, they appear to be **exactly identical**! The 0.000039% difference might be:
1. A display/rounding artifact in the comparison script
2. Coming from intermediate calculations not shown in final output
3. Related to how we're computing the percentage difference

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

## Conclusion

*To be completed after investigation*