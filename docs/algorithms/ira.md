# IRA (Inter-Rater Agreement) Algorithm

## Overview

The IRA algorithm computes Cohen's Kappa to measure inter-rater reliability between reference and hypothesis annotations. It provides both per-label and multi-class kappa values, making it ideal for assessing annotation quality and consistency.

## Algorithm Description

### Core Concept
IRA measures agreement beyond chance:
- **Cohen's Kappa**: Statistical measure of inter-rater agreement
- **Epoch sampling**: Similar to Epoch algorithm's approach
- **Confusion matrix**: Full NxN matrix for all labels
- **Dual metrics**: Per-label and overall kappa values

### Key Features
1. **Kappa Values**: Float values between -1 and 1
2. **Statistical Significance**: Accounts for chance agreement
3. **Multi-class Support**: Handles any number of labels
4. **Background Augmentation**: Fills gaps like Epoch algorithm

## Cohen's Kappa Formula

### Basic Formula
```
κ = (P_o - P_e) / (1 - P_e)
```
Where:
- `P_o` = Observed agreement (accuracy)
- `P_e` = Expected agreement by chance

### Interpretation
- κ = 1.0: Perfect agreement
- κ = 0.0: Agreement equal to chance
- κ < 0.0: Agreement worse than chance
- κ > 0.8: Almost perfect agreement
- κ > 0.6: Substantial agreement
- κ > 0.4: Moderate agreement

## Implementation Details

### Processing Pipeline

1. **Event Mode**: Sample at epoch midpoints
2. **Label Mode**: Direct sequence comparison

```python
# Event mode processing
def score(ref_events, hyp_events, epoch_duration, file_duration):
    # 1. Augment with background
    ref_events = augment_events(ref_events, file_duration)
    hyp_events = augment_events(hyp_events, file_duration)

    # 2. Sample at midpoints
    # Inclusive boundary sampling (match NEDC/Epoch):
    t = epoch_duration / 2.0
    samples = []
    while t <= file_duration:
        samples.append(t)
        t += epoch_duration

    # 3. Build confusion matrix
    for t in samples:
        ref_label = get_label_at_time(ref_events, t)
        hyp_label = get_label_at_time(hyp_events, t)
        confusion[ref_label][hyp_label] += 1

    # 4. Compute kappa values
    per_label_kappa = compute_per_label_kappa(confusion)
    multi_class_kappa = compute_multi_class_kappa(confusion)
```

### Per-Label Kappa (2x2 Matrix)

For each label, create a 2x2 confusion matrix:

```python
def compute_label_kappa(confusion, label):
    # Build 2x2 matrix
    a = confusion[label][label]           # True positive
    b = sum(confusion[label][other] for other in labels if other != label)  # False negative
    c = sum(confusion[other][label] for other in labels if other != label)  # False positive
    d = sum(confusion[o1][o2]
            for o1 in labels for o2 in labels
            if label not in {o1, o2})  # True negative

    # Total observations
    n = a + b + c + d

    # Observed agreement
    p_o = (a + d) / n

    # Expected agreement
    p_yes = ((a + b) / n) * ((a + c) / n)
    p_no = ((c + d) / n) * ((b + d) / n)
    p_e = p_yes + p_no

    # Kappa
    kappa = (p_o - p_e) / (1 - p_e)
    return kappa
```

### Multi-Class Kappa (NxN Matrix)

```python
def compute_multi_class_kappa(confusion, labels):
    # Row and column sums
    row_sums = {r: sum(confusion[r][c] for c in labels) for r in labels}
    col_sums = {c: sum(confusion[r][c] for r in labels) for c in labels}

    # Diagonal sum (correct predictions)
    diagonal = sum(confusion[l][l] for l in labels)

    # Total count
    n = sum(row_sums.values())
    if n == 0:
        return 0.0

    # Sum of products of marginals
    sum_products = sum(row_sums[l] * col_sums[l] for l in labels)

    # Kappa calculation
    numerator = n * diagonal - sum_products
    denominator = n * n - sum_products
    return (numerator / denominator) if denominator != 0 else (1.0 if numerator == 0 else 0.0)
```

## Usage Example

```python
from nedc_bench.algorithms.ira import IRAScorer
from nedc_bench.models.annotations import EventAnnotation

# Create scorer
scorer = IRAScorer()

# Event mode
reference = [
    EventAnnotation(
        channel="TERM",
        start_time=0.0,
        stop_time=10.0,
        label="seiz",
        confidence=1.0
    )
]

hypothesis = [
    EventAnnotation(
        channel="TERM",
        start_time=2.0,
        stop_time=8.0,
        label="seiz",
        confidence=0.9
    )
]

result = scorer.score(
    reference,
    hypothesis,
    epoch_duration=1.0,
    file_duration=20.0
)

print(f"Per-label kappa: {result.per_label_kappa}")
print(f"Multi-class kappa: {result.multi_class_kappa:.4f}")

# Label mode (direct sequences)
ref_labels = ["seiz", "seiz", "null", "bckg"]
hyp_labels = ["seiz", "null", "null", "bckg"]

result = scorer.score(ref_labels, hyp_labels)
print(f"Kappa: {result.multi_class_kappa:.4f}")  # 0.5000
```

## Bug History: Kappa Calculation Fix

The original implementation had incorrect kappa computation:

```python
# WRONG (original)
kappa = (sum_m - sum_gc) / (sum_n - sum_gc)

# CORRECT (fixed)
kappa = (sum_n * sum_m - sum_gc) / (sum_n * sum_n - sum_gc)
```

This fix aligns the multi-class kappa formula exactly with NEDC; see docs/archive/bugs/IRA_KAPPA_FIX.md.

## Performance Characteristics

- **Time Complexity**: O(n × e) for sampling, O(L²) for kappa
- **Space Complexity**: O(L²) for confusion matrix
- **Typical Runtime**: <200ms for 24-hour recordings

## When to Use IRA

### Recommended for:
- Assessing annotation quality
- Comparing multiple annotators
- Statistical significance testing
- Research publications requiring kappa

### Not recommended for:
- Real-time scoring
- Simple hit/miss evaluation
- Systems without fixed epochs
- Single-label binary classification

## Validation

- Parity: Beta matches NEDC v6.0.0 IRA exactly on the SSOT parity set (multi-class and per-label kappa). See docs/archive/bugs/FINAL_PARITY_RESULTS.md.

## Kappa Interpretation Guidelines

| Kappa Range | Agreement Level | Clinical Interpretation |
|-------------|----------------|-------------------------|
| < 0.00 | Poor | Worse than random chance |
| 0.00-0.20 | Slight | Negligible agreement |
| 0.21-0.40 | Fair | Weak agreement |
| 0.41-0.60 | Moderate | Acceptable for research |
| 0.61-0.80 | Substantial | Good clinical agreement |
| 0.81-1.00 | Almost Perfect | Excellent agreement |

## Related Documentation
- [Algorithm Overview](overview.md) - Comparison of all algorithms
- [Epoch Algorithm](epoch.md) - Similar sampling approach
- Source: `nedc_bench/algorithms/ira.py`
- NEDC Reference: `nedc_eeg_eval_ira.py` (v6.0.0):
  - Per-label kappa (lines ~499–540)
  - Multi-class kappa (lines ~569–583)
  - Sampling loop (inclusive boundary) in `compute` (lines ~395–417)
