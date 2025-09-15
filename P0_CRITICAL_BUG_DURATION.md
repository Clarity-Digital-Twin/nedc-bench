# 🚨 P0 CRITICAL BUG: Duration Calculation Mismatch

## Executive Summary

**SEVERITY: P0 - CRITICAL**
**IMPACT: False Alarm Rate (FA/24h) calculations are off by 5.67x**
**STATUS: Algorithm parity CONFIRMED, Duration calculation BROKEN**
**DISCOVERED: 2025-09-15 during transformer data parity testing**

## The Bug

### What's Working ✅
The core TAES algorithm achieves **PERFECT PARITY** with NEDC v6.0.0:
- True Positives: 133.84 (exact match)
- False Positives: 552.77 (exact match)
- False Negatives: 941.16 (exact match)
- Sensitivity: 12.4504% (exact match)

### What's Broken ❌
Duration calculation for FA/24h metric is completely wrong:
- **Alpha (Correct)**: 1,567,844.73 seconds total duration → FA/24h = 30.46
- **Beta (Wrong)**: 276,519.05 seconds total duration → FA/24h = 172.72
- **Error Factor**: 5.67x overestimation of false alarm rate!

## Root Cause Analysis

### The Problem
Beta pipeline is incorrectly calculating file duration as:
```python
# WRONG - Current Beta implementation
file_duration = max(e.stop_time for e in ref_ann.events)
```

### The Correct Approach
Alpha (NEDC v6.0.0) properly calculates duration as:
```python
# CORRECT - What Alpha does
# For each file: duration = last_event_end - first_event_start
# OR uses file metadata duration if available
# Then SUMS all file durations for total
```

### Why This Matters
1. **Clinical Impact**: FA/24h is a PRIMARY metric for seizure detection systems
2. **Research Validity**: Papers report FA/24h as key performance indicator
3. **Production Risk**: 5.67x error makes system appear to have unacceptable false alarm rates
4. **Regulatory Compliance**: FDA submissions require accurate FA/24h reporting

## Evidence

From actual test run on 1832 SeizureTransformer output files:

```
ALPHA RESULTS (NEDC v6.0.0):
- Total Duration: 1,567,844.73 seconds
- False Alarms: 552.77 events
- FA/24h: 30.46 (CORRECT)

BETA RESULTS (Current Implementation):
- Total Duration: 276,519.05 seconds (WRONG!)
- False Alarms: 552.77 events (correct)
- FA/24h: 172.72 (WRONG by 5.67x!)
```

## Fix Plan

### Phase 1: Immediate Fix
1. **Update duration calculation in Beta pipeline**
   - Read CSV_BI file headers for duration metadata
   - If not available, use (last_event.stop - first_event.start)
   - Properly aggregate across all files

2. **Location to fix**:
   - `nedc_bench/models/annotations.py` - Add duration property
   - `nedc_bench/algorithms/base.py` - Add duration tracking
   - Parity test scripts - Use proper duration aggregation

### Phase 2: Test Coverage
Create comprehensive tests for duration calculation:

```python
def test_duration_single_file():
    """Test duration calc for single CSV_BI file"""
    # Should use file metadata OR event span

def test_duration_aggregation():
    """Test duration summation across multiple files"""
    # Must sum, not max!

def test_fa_rate_calculation():
    """Test FA/24h calculation matches NEDC exactly"""
    # FA/24h = (false_alarms / total_duration_seconds) * 86400

def test_empty_file_duration():
    """Test handling of files with no events"""
    # Should still contribute file duration to total
```

### Phase 3: Validation
1. Re-run parity test after fix
2. Verify FA/24h matches within 0.01%
3. Test on multiple datasets (not just transformer outputs)
4. Add regression test to CI pipeline

## Implementation Priority

**THIS MUST BE FIXED BEFORE ANY PRODUCTION USE!**

The false alarm rate is reported in:
- Research papers
- Clinical evaluations
- FDA submissions
- Performance benchmarks

A 5.67x error is absolutely unacceptable and would invalidate any results.

## Test Data for Verification

We have perfect test data from the SeizureTransformer outputs:
- 1832 reference files + 1832 hypothesis files
- Known correct output: FA/24h = 30.46
- Can verify fix immediately

## Code Locations Affected

1. **Primary Fix Needed**:
   - `/nedc_bench/models/annotations.py:AnnotationFile` - Add duration property
   - `/nedc_bench/algorithms/taes.py:TAESScorer` - Track duration
   - `/nedc_bench/validation/parity.py` - Duration validation

2. **Test Files to Create**:
   - `/tests/test_duration_calculation.py` - New test file
   - `/tests/test_fa_rate.py` - New test file
   - `/tests/test_parity_metrics.py` - Update existing

3. **Documentation Updates**:
   - This file (P0_CRITICAL_BUG_DURATION.md)
   - CHANGELOG.md - Document the fix
   - API docs - Clarify duration calculation

## Lessons Learned

1. **Always validate derived metrics**, not just raw counts
2. **Duration handling is complex** - needs explicit testing
3. **Parity testing with real data is essential** - synthetic data missed this
4. **FA/24h is too important to get wrong** - needs special attention

## Action Items

- [ ] Fix duration calculation in Beta pipeline
- [ ] Add comprehensive duration tests
- [ ] Verify parity after fix
- [ ] Update documentation
- [ ] Add regression test to CI
- [ ] Consider adding duration validation to API responses

---

**Note**: While the core algorithm has perfect parity (TP/FP/FN match exactly), this duration bug is CRITICAL because it directly affects the reported false alarm rate, making the system appear 5.67x worse than it actually is. This MUST be fixed before any production deployment or research publication.