# 🚨 CRITICAL BUGS - ALL ALGORITHMS PARITY TESTING

## Executive Summary

**DATE**: 2025-09-15
**STATUS**: 1 of 5 algorithms working (TAES only)
**SEVERITY**: P0 - CRITICAL for production deployment

We discovered multiple critical bugs during comprehensive parity testing against NEDC v6.0.0 using 1832 SeizureTransformer output files.

## Bug Status Overview

| Algorithm | Status | Parity | Bug Type |
|-----------|--------|--------|----------|
| TAES | ✅ FIXED | 100% PERFECT | Duration bug fixed |
| Epoch | ❌ BROKEN | 0% | Attribute access error |
| Overlap | ❌ BROKEN | ~30% | Logic error (wrong FP/FN) |
| DP Alignment | ❌ BROKEN | 0% | Input format mismatch |
| IRA | ❌ NOT TESTED | 0% | Not integrated |

---

## BUG #1: ✅ FIXED - Duration Calculation (TAES)

### Status: RESOLVED
### Severity: P0
### Impact: FA/24h metric off by 5.67x

### Root Cause
```python
# WRONG - What Beta was doing
total_duration = max(e.stop_time for e in events)  # 276,519 seconds

# CORRECT - What it should do
total_duration = sum(file.duration for file in files)  # 1,567,844 seconds
```

### Evidence
- Alpha FA/24h: 30.4617 ✅
- Beta FA/24h (before fix): 172.7159 ❌
- Beta FA/24h (after fix): 30.4617 ✅

### Fix Applied
Use `ref_ann.duration` from CSV_BI metadata instead of event max stop time.

---

## BUG #2: ❌ ACTIVE - Epoch Algorithm Attribute Errors

### Status: BROKEN
### Severity: P0
### Impact: Complete failure - 0% of files process

### Error Message
```
Error in epoch for aaaaaajy_s001_t000.csv_bi: 'EpochResult' object has no attribute 'true_positives'
```

### Root Cause Analysis

1. **EpochResult Structure Mismatch**:
```python
# What the test expects:
result.true_positives["seiz"]  # Dictionary access

# What EpochResult actually has (from epoch.py):
@dataclass
class EpochResult:
    confusion_matrix: dict[str, dict[str, int]]
    hits: dict[str, int]           # NOT true_positives!
    misses: dict[str, int]          # NOT false_negatives!
    false_alarms: dict[str, int]   # NOT false_positives!
```

2. **Metric Calculation Issue**:
The Epoch algorithm doesn't directly provide TP/FP/FN. Instead it provides:
- hits (correct classifications)
- misses (missed events)
- false_alarms (incorrect classifications)
- confusion_matrix (full NxN matrix)

### Required Fix
```python
# Need to calculate TP/FP/FN from confusion matrix:
tp = result.confusion_matrix["seiz"]["seiz"]  # Correct seiz predictions
fp = result.confusion_matrix["bckg"]["seiz"]  # bckg wrongly called seiz
fn = result.confusion_matrix["seiz"]["bckg"]  # seiz wrongly called bckg
```

### Test Results
- Files processed: 1832
- Successful: 0
- Failed: 1832 (100% failure rate)

---

## BUG #3: ❌ ACTIVE - Overlap Algorithm Logic Error

### Status: BROKEN
### Severity: P0
### Impact: Wrong results - sensitivity 87.54% instead of 23.53%

### Evidence of Error
```
ALPHA (CORRECT):
  TP=253.00, FP=536.00, FN=822.00
  Sensitivity=23.5349%, FA/24h=29.5376

BETA (WRONG):
  TP=253.00, FP=174.00, FN=36.00  # FP and FN completely wrong!
  Sensitivity=87.5433%, FA/24h=0.0000
```

### Root Cause Analysis

1. **TP Matches but FP/FN Wrong**:
   - True Positives match (253) suggesting overlap detection works
   - False Positives way too low (174 vs 536)
   - False Negatives way too low (36 vs 822)

2. **Possible Issues**:
   - Not all events being processed
   - Wrong filtering of events by label
   - Incorrect overlap condition
   - Missing events in hypothesis files

3. **Key Observation**:
   - Sensitivity 87.54% is suspiciously high for seizure detection
   - FA/24h = 0.0000 is impossible (should be 29.54)
   - Duration calculation might be 0 or inf

### Required Investigation
```python
# Check overlap condition
def overlaps(ref, hyp):
    # NEDC exact condition:
    return (hyp.stop_time > ref.start_time) and (hyp.start_time < ref.stop_time)
```

### Files With Errors
Many files report: `Error in ovlp for [filename]: 'seiz'`
This suggests the issue is with accessing 'seiz' key in results dictionary when it doesn't exist.

---

## BUG #4: ❌ ACTIVE - DP Alignment Input Format

### Status: NOT INTEGRATED
### Severity: P0
### Impact: Algorithm cannot run - needs different input

### Issue
```python
# DP Aligner expects:
def align(self, ref: list[str], hyp: list[str])  # Label sequences

# But we're providing:
ref_ann.events  # List of EventAnnotation objects
```

### Root Cause
DP Alignment works on label sequences at sample resolution, not event annotations.

### Required Transformation
```python
# Need to convert events to label sequences:
def events_to_labels(events, duration, sample_rate=1.0):
    """Convert events to sample-level label sequence"""
    num_samples = int(duration * sample_rate)
    labels = ["bckg"] * num_samples  # Initialize with background

    for event in events:
        start_idx = int(event.start_time * sample_rate)
        stop_idx = int(event.stop_time * sample_rate)
        for i in range(start_idx, min(stop_idx, num_samples)):
            labels[i] = event.label

    return labels
```

### Expected Results (from Alpha)
```
DP ALIGNMENT:
  TP=328.00, FP=966.00, FN=747.00
  Sensitivity=30.5116%, FA/24h=53.2338
```

---

## BUG #5: ❌ ACTIVE - IRA Not Tested

### Status: NOT TESTED
### Severity: P1
### Impact: Missing algorithm for complete parity

### Issue
IRA (Inter-Rater Agreement) calculates Kappa statistic, not TP/FP/FN.

### Expected Output (from Alpha)
```
INTER-RATER AGREEMENT:
  Multi-Class Kappa: 0.1887
```

### Implementation Status
- Class exists: `nedc_bench/algorithms/ira.py`
- Not integrated in test script
- Returns different metrics (Kappa vs TP/FP/FN)

---

## Fix Priority Order

1. **🔥 Epoch (P0)**: Fix attribute access - simple fix, high impact
2. **🔥 Overlap (P0)**: Debug logic error - critical for parity
3. **🔥 DP Alignment (P0)**: Add input transformation - needs label sequences
4. **IRA (P1)**: Integrate Kappa calculation - different metric type

---

## Testing Configuration

### Data Used
- **Dataset**: SeizureTransformer outputs (Wu et al. 2025)
- **Files**: 1832 reference + 1832 hypothesis CSV_BI files
- **Duration**: 1,567,844.73 seconds total
- **Source**: TUSZ DEV set predictions

### Environment
- Python 3.10
- NEDC v6.0.0 (vendored)
- nedc-bench Beta implementation

---

## Action Items

- [ ] Fix Epoch attribute access (use hits/misses/false_alarms)
- [ ] Debug Overlap logic error (check event filtering)
- [ ] Add label sequence converter for DP Alignment
- [ ] Integrate IRA with Kappa metrics
- [ ] Re-run comprehensive parity test
- [ ] Verify 100% parity for all 5 algorithms
- [ ] Update CI/CD with full parity tests

---

## Success Criteria

All 5 algorithms must achieve:
- TP difference < 0.01
- FP difference < 0.01
- FN difference < 0.01
- Sensitivity difference < 0.01%
- FA/24h difference < 0.01

Only TAES currently meets these criteria.

---

## Lessons Learned

1. **Different Result Structures**: Each algorithm returns different result objects
2. **Input Format Matters**: DP needs sequences, others need events
3. **Metric Types Vary**: Most use TP/FP/FN, IRA uses Kappa
4. **Duration Is Critical**: Must aggregate properly for FA/24h
5. **Test Everything**: Even attribute names can break parity

---

**Critical Note**: We CANNOT deploy to production until ALL algorithms achieve parity. The current 20% success rate (1 of 5) is unacceptable for clinical use.