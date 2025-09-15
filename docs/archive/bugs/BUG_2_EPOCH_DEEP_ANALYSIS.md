# 🔬 BUG #2: EPOCH ALGORITHM - DEEP ANALYSIS & FIX

## Problem Statement

The Epoch algorithm test fails with:
```
'EpochResult' object has no attribute 'true_positives'
```

## Root Cause Analysis

### 1. What EpochResult Actually Contains

```python
@dataclass
class EpochResult:
    # Full NxN confusion matrix
    confusion_matrix: dict[str, dict[str, int]]

    # Per-label counts (NOT TP/FP/FN!)
    hits: dict[str, int]          # Correct classifications
    misses: dict[str, int]        # Missed classifications
    false_alarms: dict[str, int] # False classifications
    insertions: dict[str, int]    # From NULL_CLASS
    deletions: dict[str, int]    # To NULL_CLASS
```

### 2. What The Test Expects

```python
# Current test code (WRONG):
if "seiz" in result.true_positives:  # ❌ Doesn't exist!
    total_tp += result.true_positives["seiz"]
    total_fp += result.false_positives["seiz"]
    total_fn += result.false_negatives["seiz"]
```

### 3. How NEDC Calculates TP/FP/FN from Confusion Matrix

From NEDC v6.0.0 summary output:
```
NEDC Epoch Confusion Matrix
Ref/Hyp:    seiz         bckg
seiz:    33704.00     250459.00
bckg:    18816.00    5968398.00
```

The confusion matrix interpretation:
- `matrix[ref][hyp]` = count of epochs with reference label `ref` classified as `hyp`
- **True Positives (seiz)**: `matrix["seiz"]["seiz"]` = 33704
- **False Positives (seiz)**: `matrix["bckg"]["seiz"]` = 18816
- **False Negatives (seiz)**: `matrix["seiz"]["bckg"]` = 250459
- **True Negatives (seiz)**: `matrix["bckg"]["bckg"]` = 5968398

### 4. The Relationship Between Confusion Matrix and Hits/Misses/FA

In NEDC terminology:
- **Hits**: Correct classifications for a label = TP
- **Misses**: Reference events not detected = FN
- **False Alarms**: Hypothesis events with no reference = FP

But for epoch scoring, everything comes from the confusion matrix!

## Deep Investigation of Epoch Algorithm

### How Epoch Scoring Works

1. **Sampling**: Events are sampled at fixed intervals (epoch_duration)
2. **Classification**: Each epoch gets a label (seiz, bckg, null)
3. **Compression**: Consecutive duplicates are compressed
4. **Matrix Building**: Build confusion matrix from compressed sequences

### The Critical Insight

Epoch scoring is fundamentally different from event-based scoring:
- Events → Epochs → Labels → Confusion Matrix
- Not direct event-to-event comparison

## THE FIX

### Option 1: Add Properties to EpochResult (Simple)

```python
@dataclass
class EpochResult:
    # ... existing fields ...

    @property
    def true_positives(self) -> dict[str, int]:
        """Calculate TP for each label from confusion matrix"""
        tp = {}
        for label in self.confusion_matrix:
            if label in self.confusion_matrix.get(label, {}):
                tp[label] = self.confusion_matrix[label][label]
            else:
                tp[label] = 0
        return tp

    @property
    def false_positives(self) -> dict[str, int]:
        """Calculate FP for each label from confusion matrix"""
        fp = {}
        for label in self.confusion_matrix:
            fp[label] = 0
            for ref_label in self.confusion_matrix:
                if ref_label != label:
                    fp[label] += self.confusion_matrix.get(ref_label, {}).get(label, 0)
        return fp

    @property
    def false_negatives(self) -> dict[str, int]:
        """Calculate FN for each label from confusion matrix"""
        fn = {}
        for label in self.confusion_matrix:
            fn[label] = 0
            if label in self.confusion_matrix:
                for hyp_label in self.confusion_matrix[label]:
                    if hyp_label != label:
                        fn[label] += self.confusion_matrix[label][hyp_label]
        return fn
```

### Option 2: Fix the Test Code (More Correct)

```python
elif algo_name == "epoch":
    result = scorer.score(ref_ann.events, hyp_ann.events, ref_ann.duration)

    # Calculate from confusion matrix
    if "seiz" in result.confusion_matrix:
        # TP: seiz correctly classified as seiz
        total_tp += result.confusion_matrix.get("seiz", {}).get("seiz", 0)

        # FP: bckg incorrectly classified as seiz
        total_fp += result.confusion_matrix.get("bckg", {}).get("seiz", 0)

        # FN: seiz incorrectly classified as bckg
        total_fn += result.confusion_matrix.get("seiz", {}).get("bckg", 0)
```

## Expected Values from Alpha

From the NEDC output:
```
EPOCH SCORING:
- True Positives: 33704
- False Positives: 18816
- False Negatives: 250459
- Sensitivity: 11.8608%
- FA/24h: 259.2257
```

## Implementation Decision

I'll implement **Option 1** - add properties to EpochResult. This makes the interface consistent with other algorithms and easier to use.

## Test Plan

1. Add TP/FP/FN properties to EpochResult
2. Run single file test to verify calculation
3. Run full parity test
4. Verify matches Alpha exactly

## Code Changes Required

1. **File**: `nedc_bench/algorithms/epoch.py`
   - Add `@property` methods for true_positives, false_positives, false_negatives

2. **File**: `scripts/ultimate_parity_test.py`
   - Keep existing test code (will work with properties)

## Verification Metrics

Must match Alpha exactly:
- TP = 33704 (±0.01)
- FP = 18816 (±0.01)
- FN = 250459 (±0.01)
- Sensitivity = 11.8608% (±0.01%)
- FA/24h = 259.2257 (±0.01)
\n[Archived] See docs/FINAL_PARITY_RESULTS.md and docs/EPOCH_BUG_FIXED.md for current status.
