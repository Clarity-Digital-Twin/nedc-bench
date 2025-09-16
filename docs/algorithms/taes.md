# TAES (Time-Aligned Event Scoring) Algorithm

## Overview

TAES is the most clinically relevant scoring algorithm in the NEDC suite, designed specifically for evaluating seizure detection systems. It provides fractional credit for partial temporal overlaps between predicted and actual seizure events.

## Algorithm Description

### Core Concept

TAES evaluates event-level agreement using fractional scoring:

- **Partial credit** for events that partially overlap in time
- **Multi-overlap sequencing** for complex overlap scenarios
- **Fractional penalties** based on duration ratios

### Key Features

1. **Fractional Scoring**: Returns float values (e.g., TP=133.84)
1. **Duration-Aware**: Penalties proportional to event durations
1. **Clinical Focus**: Optimized for seizure detection evaluation
1. **No Confusion Matrix**: Direct hit/miss/FA calculation only

## Implementation Details

### Multi-Overlap Sequencing

The critical innovation of TAES is handling multiple overlapping events:

```python
# Scenario 1: One hypothesis spans multiple references
refs: <--> <--> <--> <-->  # 4 separate seizures
hyp:  <----------------->  # 1 long detection

# Result:
# - First ref: fractional hit (e.g., 0.8)
# - Refs 2-4: Each adds +1.0 to miss penalty!
# - Total: hit=0.8, miss=3.2, fa=fractional
```

### Processing Logic

1. **For each reference event**:

   - Find all overlapping hypotheses with matching label
   - Determine overlap type (hyp extends vs ref extends)
   - Apply appropriate scoring function

1. **Two overlap cases**:

   **Case A: `ovlp_ref_seqs` (hypothesis extends beyond reference)**

   ```
   ref:     <----->
   hyp:  <----------->
   ```

   - Calculate fractional hit/FA for primary overlap
   - Add +1.0 miss for each additional ref overlapped

   **Case B: `ovlp_hyp_seqs` (reference extends beyond hypothesis)**

   ```
   ref:  <----------->
   hyp:     <----->
   ```

   - Multiple hyps can contribute to single ref
   - Each hyp adds to hit and reduces miss

1. **Unmatched events**:

   - Any reference event with no overlapping hypothesis adds +1.0 to miss
   - Any hypothesis event with no overlapping reference adds +1.0 to false alarms

### Fractional Scoring Formula (`calc_hf`)

The core scoring calculation for overlapping events:

```python
def calc_hf(ref, hyp):
    ref_dur = ref.stop - ref.start

    # Case 1: Pre-prediction (hyp starts before ref)
    if hyp.start <= ref.start and hyp.stop <= ref.stop:
        hit = (hyp.stop - ref.start) / ref_dur
        fa = min(1.0, (ref.start - hyp.start) / ref_dur)

    # Case 2: Post-prediction (hyp ends after ref)
    elif hyp.start >= ref.start and hyp.stop >= ref.stop:
        hit = (ref.stop - hyp.start) / ref_dur
        fa = min(1.0, (hyp.stop - ref.stop) / ref_dur)

    # Case 3: Over-prediction (hyp covers entire ref)
    elif hyp.start < ref.start and hyp.stop > ref.stop:
        hit = 1.0
        fa = min(1.0, ((hyp.stop - ref.stop) + (ref.start - hyp.start)) / ref_dur)

    # Case 4: Under-prediction (hyp entirely within ref)
    else:
        hit = (hyp.stop - hyp.start) / ref_dur
        fa = 0.0

    return hit, fa
```

## Usage Example

```python
from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.models.annotations import EventAnnotation

# Create scorer
scorer = TAESScorer(target_label="seiz")

# Define events
reference = [
    EventAnnotation(
        channel="TERM", start_time=100.0, stop_time=120.0, label="seiz", confidence=1.0
    )
]

hypothesis = [
    EventAnnotation(
        channel="TERM", start_time=105.0, stop_time=125.0, label="seiz", confidence=0.9
    )
]

# Score
result = scorer.score(reference, hypothesis)
print(f"TP: {result.true_positives:.2f}")  # TP: 0.75
print(f"FP: {result.false_positives:.2f}")  # FP: 0.25
print(f"FN: {result.false_negatives:.2f}")  # FN: 0.25
```

## Critical Implementation Notes

### Bug History

1. **Multi-overlap penalty**: Initially missed the +1.0 penalty for each additional reference
1. **Flag tracking**: Proper boolean flag management for processed events
1. **Fractional boundaries**: Exact NEDC calc_hf formula matching

### Performance Characteristics

- **Time Complexity**: O(n × m) where n=refs, m=hyps
- **Space Complexity**: O(n + m) for flag arrays
- **Typical Runtime**: \<100ms for clinical datasets

## When to Use TAES

### Recommended for:

- Clinical seizure detection evaluation
- Variable-duration event scoring
- Systems where partial detection has value
- FDA submission and regulatory compliance

### Not recommended for:

- Fixed-window classification tasks
- Multi-class confusion analysis
- Systems requiring integer counts
- Real-time streaming evaluation

## Validation

- Parity: Beta matches NEDC v6.0.0 TAES exactly on the SSOT parity set. See docs/archive/bugs/FINAL_PARITY_RESULTS.md.
  - False alarm rate (FA/24h) uses event FP counts directly (no epoch scaling). See docs/algorithms/metrics.md.

## Related Documentation

- [Algorithm Overview](overview.md) - Comparison of all algorithms
- [Metrics Calculation](metrics.md) - FA/24h computation
- Source: `nedc_bench/algorithms/taes.py`
- NEDC Reference: `nedc_eeg_eval_taes.py` (v6.0.0):
  - `ovlp_ref_seqs` (lines ~669–736)
  - `ovlp_hyp_seqs` (lines ~740–891)
  - `calc_hf` (lines ~926–1006)
