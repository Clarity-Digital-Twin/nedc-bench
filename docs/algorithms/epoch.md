# Epoch-Based Scoring Algorithm

## Overview

The Epoch algorithm divides continuous EEG recordings into fixed-width time windows (epochs) and evaluates classification accuracy at each window. It provides a comprehensive confusion matrix and is ideal for time-series classification tasks.

## Algorithm Description

### Core Concept
Epoch scoring evaluates agreement at fixed time intervals:
- **Fixed-width windows**: Typically 1-second epochs
- **Midpoint sampling**: Sample at epoch centers (0.5s, 1.5s, 2.5s...)
- **Background augmentation**: Fill gaps with "null" class
- **Compression step**: Remove consecutive duplicates

### Key Features
1. **Integer Counts**: All metrics are integers (e.g., TP, FP, FN)
2. **Full Confusion Matrix**: NxN matrix for all label pairs
3. **Compression**: Consecutive duplicate removal via joint compression
4. **Gap Filling**: Automatic background augmentation to cover full duration

## Implementation Details

### Processing Pipeline

1. **Augmentation Phase**:
   ```python
   # Original events with gaps
   events: [seiz: 0-10s] [gap] [seiz: 20-30s]

   # After augmentation
   augmented: [seiz: 0-10s] [null: 10-20s] [seiz: 20-30s]
   ```

2. **Sampling Phase**:
   ```python
   # Sample at midpoints with epoch_duration=1.0
   sample_times = [0.5, 1.5, 2.5, ..., duration-0.5]

   # For each sample time, find covering event
   labels = [event.label for t in sample_times]
   ```

3. **Compression Phase**:
   ```python
   # Raw sequence with duplicates
   raw: [null, seiz, seiz, seiz, null, null, bckg, bckg]

   # After compression (remove consecutive duplicates)
   compressed: [null, seiz, null, bckg]
   ```

### Critical Implementation Details

#### Background Augmentation (Bug Fix #1)
The most critical bug fix was adding background augmentation:

```python
def _augment_events(self, events, file_duration):
    """Fill all gaps with 'null' class events"""
    augmented = []
    curr_time = 0.0

    for event in sorted(events, key=lambda x: x.start_time):
        # Fill gap before event
        if curr_time < event.start_time:
            augmented.append(EventAnnotation(
                channel="TERM",
                start_time=curr_time,
                stop_time=event.start_time,
                label=self.null_class,
                confidence=1.0
            ))

        augmented.append(event)
        curr_time = event.stop_time

    # Fill gap at end
    if curr_time < file_duration:
        augmented.append(EventAnnotation(
            channel="TERM",
            start_time=curr_time,
            stop_time=file_duration,
            label=self.null_class,
            confidence=1.0
        ))

    return augmented
```

#### Inclusive Boundary Condition
NEDC uses `<=` for the stop boundary check:

```python
def _sample_times(self, file_duration):
    """Generate sample times with INCLUSIVE boundary"""
    samples = []
    half = self.epoch_duration / 2.0
    t = half

    # CRITICAL: Use <= not < for NEDC parity
    while t <= file_duration:
        samples.append(t)
        t += self.epoch_duration

    return samples
```

#### Joint Compression
Both reference and hypothesis must be compressed together:

```python
def _compress_joint(self, ref, hyp):
    """Compress BOTH sequences together"""
    compressed_ref = [ref[0]]
    compressed_hyp = [hyp[0]]

    for i in range(1, len(ref)):
        # Only keep if EITHER sequence changes
        if ref[i] != ref[i-1] or hyp[i] != hyp[i-1]:
            compressed_ref.append(ref[i])
            compressed_hyp.append(hyp[i])

    return compressed_ref, compressed_hyp
```

## Usage Example

```python
from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.models.annotations import EventAnnotation

# Create scorer with 1-second epochs
scorer = EpochScorer(epoch_duration=1.0, null_class="null")

# Define events
reference = [
    EventAnnotation(
        channel="TERM",
        start_time=10.0,
        stop_time=20.0,
        label="seiz",
        confidence=1.0
    )
]

hypothesis = [
    EventAnnotation(
        channel="TERM",
        start_time=12.0,
        stop_time=18.0,
        label="seiz",
        confidence=0.9
    )
]

# Score with file duration
result = scorer.score(reference, hypothesis, file_duration=30.0)

# Access results
print(f"Confusion Matrix: {result.confusion_matrix}")
print(f"TP (seiz): {result.true_positives['seiz']}")  # Integer count
print(f"Compressed ref: {result.compressed_ref}")
print(f"Compressed hyp: {result.compressed_hyp}")
```

## Confusion Matrix Structure

The epoch algorithm produces a full NxN confusion matrix:

```python
confusion_matrix = {
    "null": {"null": 15, "seiz": 2, "bckg": 0},
    "seiz": {"null": 1, "seiz": 8, "bckg": 1},
    "bckg": {"null": 0, "seiz": 0, "bckg": 5}
}

# Interpretation:
# confusion_matrix[ref][hyp] = count
# e.g., confusion_matrix["seiz"]["null"] = 1
#       means 1 epoch was "seiz" in ref but "null" in hyp
```

## Bug History

1. **Missing Background Augmentation** (9 TP difference):
   - Original: No gap filling → incorrect epoch alignment
   - Fixed: Fill all gaps with "null" class events

2. **Boundary Condition** (off-by-one errors):
   - Original: Used `<` for stop boundary
   - Fixed: Use `<=` to match NEDC inclusive boundary

3. **Compression Logic**:
   - Original: Compressed sequences independently
   - Fixed: Joint compression preserving alignment

## Performance Characteristics

- **Time Complexity**: O(n × e) where n=events, e=epochs
- **Space Complexity**: O(e) for sample arrays
- **Typical Runtime**: <500ms for 24-hour recordings

## When to Use Epoch Scoring

### Recommended for:
- Fixed-window classification evaluation
- Multi-class confusion matrix analysis
- Systems with regular sampling rates
- Comparing different epoch durations

### Not recommended for:
- Variable-duration event scoring
- Systems where exact boundaries matter
- Real-time streaming with irregular events
- Fractional scoring requirements

## Validation

- Parity: Beta matches NEDC v6.0.0 Epoch scoring exactly on the SSOT parity set. See docs/archive/bugs/FINAL_PARITY_RESULTS.md.
  - False alarm rate (FA/24h) uses epoch FP scaled by `epoch_duration` as described in docs/algorithms/metrics.md.

## Related Documentation
- [Algorithm Overview](overview.md) - Comparison of all algorithms
- [IRA Algorithm](ira.md) - Similar epoch-based approach
- [Metrics Calculation](metrics.md) - FA/24h computation
- Source: `nedc_bench/algorithms/epoch.py`
- NEDC Reference: `nedc_eeg_eval_epoch.py` (v6.0.0), see `compute` (lines ~528–610) and `compute_performance` (lines ~645–723)
