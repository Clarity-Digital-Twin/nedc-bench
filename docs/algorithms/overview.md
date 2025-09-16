# Algorithm Overview

## Introduction

NEDC-BENCH implements five EEG annotation scoring algorithms originally developed by Temple University's Neural Engineering Data Consortium (NEDC). These algorithms evaluate the agreement between reference (ground truth) and hypothesis (predicted) annotations for EEG seizure detection systems.

## Algorithm Comparison Table

| Algorithm        | Type           | Scoring Unit      | Confusion Matrix   | Key Metric      | Use Case                   |
| ---------------- | -------------- | ----------------- | ------------------ | --------------- | -------------------------- |
| **TAES**         | Event-based    | Fractional events | No                 | TP (fractional) | Clinical seizure detection |
| **Epoch**        | Sample-based   | Fixed epochs      | Yes (NxN)          | TP (integer)    | Time-series classification |
| **DP Alignment** | Sequence-based | Label sequences   | Yes (substitution) | Edit distance   | Sequence comparison        |
| **Overlap**      | Event-based    | Binary events     | No                 | Hits (integer)  | Simple event detection     |
| **IRA**          | Sample-based   | Epochs            | Yes (NxN)          | Cohen's Kappa   | Inter-rater agreement      |

## Core Concepts

### Event Annotations

All algorithms operate on event annotations with:

- **Channel**: EEG channel identifier (e.g., "TERM")
- **Start/Stop Time**: Temporal boundaries in seconds
- **Label**: Event classification (e.g., "seiz", "bckg", "null")
- **Confidence**: Prediction confidence score (0-1)

### Scoring Metrics

- **True Positives (TP)**: Correctly identified events
- **False Positives (FP)**: Incorrectly predicted events
- **False Negatives (FN)**: Missed events
- **FA/24h**: False alarms per 24 hours (critical clinical metric)

## Algorithm Selection Guide

### Choose TAES when:

- Clinical accuracy is paramount
- Events have variable durations
- Fractional credit for partial overlaps is needed
- Multi-overlap sequencing behavior is acceptable

### Choose Epoch when:

- Fixed-width time windows are natural
- Confusion matrix analysis is required
- Background augmentation is needed
- Integer counts are preferred

### Choose DP Alignment when:

- Sequence-level comparison is needed
- Edit operations (ins/del/sub) are meaningful
- Order of events matters
- Detailed error analysis is required

### Choose Overlap when:

- Simple binary hit/miss is sufficient
- ANY temporal overlap counts as detection
- Fast computation is needed
- Event boundaries are less critical

### Choose IRA when:

- Inter-rater reliability is the goal
- Cohen's Kappa is the standard metric
- Per-label and overall agreement needed
- Statistical significance testing required

## Implementation Architecture

```
nedc_bench/algorithms/
├── taes.py          # Time-Aligned Event Scoring
├── epoch.py         # Epoch-based scoring
├── dp_alignment.py  # Dynamic Programming alignment
├── overlap.py       # Binary overlap detection
└── ira.py          # Inter-Rater Agreement
```

### Design Principles

1. **Exact NEDC Parity**: Bit-for-bit matching of original algorithms
1. **SOLID Principles**: Clean, maintainable code architecture
1. **Type Safety**: Full MyPy type annotations
1. **Testability**: Comprehensive pytest coverage
1. **Documentation**: Inline references to NEDC source lines

## Critical Implementation Details

### Boundary Conditions

- **Inclusive boundaries**: NEDC uses `<=` for stop time comparisons
- **Bitwise operators**: Some algorithms use `&` for historical reasons
- **NULL_CLASS handling**: Special "null" label for gaps/sentinels

### Numerical Precision

- **TAES**: Returns float values for fractional scoring
- **Epoch/DP/Overlap**: Return integer counts
- **IRA**: Integer confusion matrix, float kappa values

### Performance Considerations

- All algorithms are O(n²) worst case for overlap detection
- Epoch/IRA benefit from pre-sorting events
- DP Alignment has O(m×n) dynamic programming complexity

## Validation Status

All algorithms achieve 100% parity with NEDC v6.0.0 on the SSOT parity set. See docs/archive/bugs/FINAL_PARITY_RESULTS.md for details.

## Related Documentation

- [TAES Algorithm](taes.md) - Fractional event scoring
- [Epoch Algorithm](epoch.md) - Fixed-width window scoring
- [DP Alignment](dp-alignment.md) - Sequence alignment
- [Overlap Algorithm](overlap.md) - Binary detection
- [IRA Algorithm](ira.md) - Inter-rater agreement
- [Metrics Calculation](metrics.md) - FA/24h and other metrics
