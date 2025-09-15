# Overlap Scoring Algorithm

## Overview

The Overlap algorithm provides the simplest event-based scoring in the NEDC suite. It uses binary ANY overlap detection - if events overlap at all temporally, it counts as a hit. No fractional scoring or duration weighting is applied.

## Algorithm Description

### Core Concept
Overlap scoring uses binary event detection:
- **ANY overlap**: Any temporal overlap counts as detection
- **Binary scoring**: Full credit (1) or no credit (0)
- **No confusion matrix**: Direct hit/miss/FA counting only
- **Label matching**: Events must have matching labels

### Key Features
1. **Integer Counts**: All metrics are integers
2. **Simple Logic**: Easiest algorithm to understand
3. **Fast Computation**: No complex calculations
4. **No Guard Width**: Strict temporal overlap checking

## Implementation Details

### Overlap Detection Condition

The critical condition for overlap detection:

```python
def overlaps(event1, event2):
    """ANY temporal overlap between events"""
    return (event1.stop_time > event2.start_time and
            event1.start_time < event2.stop_time)
```

Note: NEDC does NOT use guard widths or tolerance bands.

### Processing Logic

1. **Score Reference Events**:
   ```python
   for ref_event in reference_events:
       has_overlap = False

       for hyp_event in hypothesis_events:
           if overlaps(ref_event, hyp_event) and same_label:
               has_overlap = True
               break

       if has_overlap:
           hits[label] += 1
       else:
           misses[label] += 1
   ```

2. **Score False Alarms**:
   ```python
   for hyp_event in hypothesis_events:
       has_overlap = False

       for ref_event in reference_events:
           if overlaps(hyp_event, ref_event) and same_label:
               has_overlap = True
               break

       if not has_overlap:
           false_alarms[label] += 1
   ```

### NEDC Mappings

The algorithm provides simple mappings:

```python
# NEDC lines 711-713
insertions = false_alarms  # Direct copy
deletions = misses         # Direct copy
```

## Usage Example

```python
from nedc_bench.algorithms.overlap import OverlapScorer
from nedc_bench.models.annotations import EventAnnotation

# Create scorer
scorer = OverlapScorer()

# Define events
reference = [
    EventAnnotation(
        channel="TERM",
        start_time=100.0,
        stop_time=120.0,
        label="seiz",
        confidence=1.0
    ),
    EventAnnotation(
        channel="TERM",
        start_time=200.0,
        stop_time=220.0,
        label="seiz",
        confidence=1.0
    )
]

hypothesis = [
    EventAnnotation(
        channel="TERM",
        start_time=110.0,  # Overlaps first ref
        stop_time=130.0,
        label="seiz",
        confidence=0.9
    ),
    EventAnnotation(
        channel="TERM",
        start_time=250.0,  # No overlap
        stop_time=270.0,
        label="seiz",
        confidence=0.8
    )
]

# Score
result = scorer.score(reference, hypothesis)

# Results (all integers)
print(f"Hits: {result.hits}")              # {"seiz": 1}
print(f"Misses: {result.misses}")          # {"seiz": 1}
print(f"False Alarms: {result.false_alarms}")  # {"seiz": 1}
```

## Key Characteristics

### What Counts as a Hit

Any amount of temporal overlap:
```
ref:     |----------|
hyp1:         |--|        # Hit (partial overlap)
hyp2:    |------------|   # Hit (full overlap)
hyp3:              |--|   # Hit (minimal overlap)
hyp4:                  |--| # Miss (no overlap)
```

### Multiple Events
- One reference can overlap multiple hypotheses; it counts as a single hit for that reference event.
- One hypothesis can overlap multiple references; each overlapped reference can count its own hit.
- No fractional credit or duration weighting for multiple overlaps.

## Performance Characteristics

- **Time Complexity**: O(n × m) where n=refs, m=hyps
- **Space Complexity**: O(1) - no additional structures
- **Typical Runtime**: <10ms for clinical datasets

## When to Use Overlap Scoring

### Recommended for:
- Simple binary detection tasks
- Quick performance assessment
- Systems where exact boundaries don't matter
- Baseline comparison metric

### Not recommended for:
- Clinical evaluation requiring precision
- Systems with variable event durations
- Multi-class confusion analysis
- Detailed error analysis

## Comparison with Other Algorithms

| Aspect | Overlap | TAES | Epoch |
|--------|---------|------|-------|
| Scoring | Binary | Fractional | Sample-based |
| Counts | Integer | Float | Integer |
| Speed | Fastest | Medium | Slowest |
| Precision | Lowest | Highest | Medium |

## Validation

- Parity: Beta matches NEDC v6.0.0 Overlap scoring exactly on the SSOT parity set. See docs/archive/bugs/FINAL_PARITY_RESULTS.md.
  - False alarm rate (FA/24h) uses event FP counts directly (no epoch scaling). See docs/algorithms/metrics.md.

## Related Documentation
- [Algorithm Overview](overview.md) - Comparison of all algorithms
- [TAES Algorithm](taes.md) - Fractional overlap scoring
- Source: `nedc_bench/algorithms/overlap.py`
- NEDC Reference: `nedc_eeg_eval_ovlp.py` lines 593-613
