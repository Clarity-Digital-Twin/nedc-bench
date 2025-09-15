# Metrics Calculation Reference

## Overview

This document details the computation of all metrics used in NEDC-BENCH, with special emphasis on the critical FA/24h (False Alarms per 24 hours) metric used in clinical evaluation.

## Core Metrics

### True Positives (TP)
- **Definition**: Correctly identified positive events
- **Computation**: Algorithm-specific
  - TAES: Fractional sum of overlaps
  - Epoch/DP/Overlap/IRA: Integer counts

### False Positives (FP)
- **Definition**: Incorrectly predicted positive events
- **Computation**: Algorithm-specific
  - TAES: Fractional false alarm portions
  - Epoch: Integer count from confusion matrix
  - Overlap: Unmatched hypothesis events

### False Negatives (FN)
- **Definition**: Missed positive events
- **Computation**: Algorithm-specific
  - TAES: 1.0 - hit + multi-overlap penalties
  - Epoch: Misses from compressed sequences
  - DP: Deletions + substitutions

## FA/24h (False Alarms per 24 hours)

### Critical Clinical Metric

FA/24h is the most important metric for clinical seizure detection systems:

```python
def fa_per_24h(false_positives, total_duration_seconds, epoch_duration=None):
    """
    Compute FA/24h according to NEDC definitions.

    Args:
        false_positives: FP count (float or int)
        total_duration_seconds: Total recording duration
        epoch_duration: For epoch-based algorithms only

    Returns:
        False alarms per 24 hours
    """
    if total_duration_seconds <= 0:
        return 0.0

    # For epoch-based algorithms, scale by epoch duration
    if epoch_duration is not None:
        numerator = false_positives * epoch_duration
    else:
        numerator = false_positives

    # Convert to 24-hour rate
    return (numerator / total_duration_seconds) * 86400.0
```

### Algorithm-Specific FA/24h

| Algorithm | FP Units | Epoch Scaling | Example |
|-----------|----------|---------------|---------|
| TAES | Fractional events | No | `134.20 / duration * 86400` |
| Epoch | Epoch counts | Yes | `31989 * 1.0 / duration * 86400` |
| DP Alignment | Event counts | No | `3 / duration * 86400` |
| Overlap | Event counts | No | `1 / duration * 86400` |
| IRA | N/A | N/A | Not computed |

## Standard Metrics

### Sensitivity (Recall, TPR)
```python
sensitivity = TP / (TP + FN)
```
- **Range**: 0.0 to 1.0
- **Interpretation**: Proportion of actual positives correctly identified
- **Clinical Target**: >0.90 for seizure detection

### Precision (PPV)
```python
precision = TP / (TP + FP)
```
- **Range**: 0.0 to 1.0
- **Interpretation**: Proportion of positive predictions that are correct
- **Trade-off**: Often inversely related to sensitivity

### F1 Score
```python
f1 = 2 * (precision * sensitivity) / (precision + sensitivity)
```
- **Range**: 0.0 to 1.0
- **Interpretation**: Harmonic mean of precision and sensitivity
- **Use**: Balanced metric for overall performance

### Specificity (TNR)
```python
specificity = TN / (TN + FP)
```
- **Note**: Not computed by most NEDC algorithms
- **Why**: TN is undefined for continuous EEG (infinite negatives)

## Algorithm-Specific Metrics

### TAES Metrics
- **Fractional TP/FP/FN**: Float values based on overlap durations
- **No TN**: True negatives not defined
- **Multi-overlap penalties**: Complex scoring for overlapping events

### Epoch Metrics
- **Confusion Matrix**: Full NxN matrix for all labels
- **Compressed Counts**: After consecutive duplicate removal
- **Insertions/Deletions**: NULL class transitions

### DP Alignment Metrics
- **Edit Operations**: Insertions, deletions, substitutions
- **Substitution Matrix**: Detailed label-to-label errors
- **Edit Distance**: Total cost of alignment

### Overlap Metrics
- **Binary Counts**: Integer hits/misses/false alarms
- **Simple Mappings**: insertions=FA, deletions=misses
- **No confusion matrix**: Direct counting only

### IRA Metrics
- **Cohen's Kappa**: Agreement beyond chance
- **Per-label κ**: Individual label agreement
- **Multi-class κ**: Overall agreement

## Duration Calculation

### Total Duration for FA/24h

```python
def get_total_duration(annotations):
    """Extract total recording duration from annotations"""
    if not annotations:
        return 0.0

    # Method 1: From file duration header
    if hasattr(annotations[0], 'file_duration'):
        return annotations[0].file_duration

    # Method 2: From max stop time
    max_time = max(event.stop_time for event in annotations)
    return max_time

    # Method 3: From explicit duration parameter
    # Passed separately to scoring functions
```

## Clinical Thresholds

### FDA/Clinical Standards

| Metric | Acceptable | Good | Excellent |
|--------|------------|------|-----------|
| Sensitivity | >0.85 | >0.90 | >0.95 |
| FA/24h | <10 | <5 | <1 |
| F1 Score | >0.70 | >0.80 | >0.90 |

### Research Standards

| Metric | Minimum | Target | State-of-Art |
|--------|---------|--------|--------------|
| Cohen's κ | >0.40 | >0.60 | >0.80 |
| Precision | >0.50 | >0.70 | >0.90 |
| Accuracy | >0.80 | >0.90 | >0.95 |

## Implementation Notes

### Floating Point Precision
- Use float64 for fractional metrics
- Round display to 2-4 decimal places
- Exact comparison for parity testing

### Edge Cases
- Empty annotations: Return 0.0 for all metrics
- Zero duration: Return 0.0 for FA/24h
- No positive class: Undefined sensitivity (return 0.0)

### Performance Optimization
- Cache duration calculations
- Vectorize confusion matrix operations
- Use numpy for large-scale computations

## Validation

- See docs/archive/bugs/FINAL_PARITY_RESULTS.md for parity-confirmed metrics across all algorithms.

## Related Documentation
- [Algorithm Overview](overview.md) - Algorithm comparison
- [TAES Algorithm](taes.md) - Fractional scoring
- [Epoch Algorithm](epoch.md) - Epoch-based metrics
- Source: `nedc_bench/utils/metrics.py`
- NEDC Reference: Metrics computed in each algorithm file
