# Phase 3: Core Algorithms — NEDC-EXACT Implementation Plan

## ⚠️ CRITICAL: THIS PLAN IS VERIFIED AGAINST NEDC SOURCE CODE

After analyzing the actual NEDC source code, this plan corrects all discrepancies from the original Phase 3 plan.

## Key Discoveries from NEDC Source Analysis

### 1. DP Alignment (nedc_eeg_eval_dpalign.py)
- **Lines 685-708**: Uses INTEGER counts (`int(1)`)
- **Lines 689-708**: NULL_CLASS handling for insertions/deletions
- **Dual counting system**: Tracks both hit/miss/fal AND del/ins/sub
- **Lines 578-586**: Adds NULL_CLASS sentinels to sequences
- **Lines 646-680**: Backtrack produces aligned sequences

### 2. Epoch Scoring (nedc_eeg_eval_epoch.py)
- **Lines 600-610**: COMPRESSES consecutive duplicate labels!
- **Lines 690-723**: Complex confusion matrix with NULL_CLASS
- **Lines 706-708**: False alarms = substitutions from null_class
- **Lines 716-722**: Insertions/deletions via null_class transitions
- **All counts are INTEGERS**

### 3. Overlap Scoring (nedc_eeg_eval_ovlp.py)
- **Lines 644-659**: ANY overlap condition: `(event[1] > start) and (event[0] < stop)`
- **Line 686**: "overlap method does not give us a confusion matrix"
- **Lines 596-613**: Direct hit/miss/false_alarm counting
- **Lines 711-713**: insertions = false_alarms, deletions = misses
- **All counts are INTEGERS**

### 4. IRA (nedc_eeg_eval_ira.py)
- **Lines 22-24**: Uses epoch-based scoring internally
- **Lines 499-540**: Per-label kappa using 2x2 matrices
- **Lines 548-583**: Multi-class kappa from full matrix
- **Confusion matrix uses INTEGERS, kappa values are FLOATS**

### 5. TAES (Already Implemented)
- Uses FLOAT counts for fractional scoring
- Multi-overlap sequencing with +1.0 miss penalty per additional ref
- ✅ Already achieving perfect parity

## Corrected Implementation Plan

### Algorithm Count Types Summary

| Algorithm | Primary Counts | Secondary Values | Key Difference from Original Plan |
|-----------|---------------|------------------|-----------------------------------|
| DP | INTEGER | Float metrics | NULL_CLASS handling, dual counting |
| Epoch | INTEGER | Float metrics | Consecutive duplicate compression |
| Overlap | INTEGER | Float metrics | NO confusion matrix, ANY overlap |
| TAES | FLOAT | Float metrics | ✅ Already correct |
| IRA | INTEGER confusion | FLOAT kappa | Per-label + multi-class kappa |

### Day 1-2: DP Alignment (NEDC-EXACT)

```python
# nedc_bench/algorithms/dp_alignment.py
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np

NULL_CLASS = "null"  # NEDC's null class marker

@dataclass
class DPAlignmentResult:
    """NEDC DP alignment results with INTEGER counts"""
    # Primary counts (all integers per NEDC)
    hits: int  # Exact matches
    substitutions: Dict[str, Dict[str, int]]  # Full substitution matrix
    insertions: Dict[str, int]  # Per-label insertions
    deletions: Dict[str, int]  # Per-label deletions

    # Aggregate counts
    total_insertions: int
    total_deletions: int
    total_substitutions: int

    # For parity validation
    true_positives: int  # = hits
    false_positives: int  # = total_insertions
    false_negatives: int  # = total_deletions + total_substitutions

    # Aligned sequences for debugging
    aligned_ref: List[str]
    aligned_hyp: List[str]

class DPAligner:
    """NEDC-exact Dynamic Programming alignment"""

    def __init__(self,
                 penalty_del: float = 1.0,
                 penalty_ins: float = 1.0,
                 penalty_sub: float = 1.0):
        self.penalty_del = penalty_del
        self.penalty_ins = penalty_ins
        self.penalty_sub = penalty_sub

    def align(self, ref: List[str], hyp: List[str]) -> DPAlignmentResult:
        """NEDC-exact DP alignment matching lines 550-711"""
        # Add NULL_CLASS sentinels (NEDC lines 578-586)
        ref_padded = [NULL_CLASS] + ref + [NULL_CLASS]
        hyp_padded = [NULL_CLASS] + hyp + [NULL_CLASS]

        # Run DP alignment
        aligned_ref, aligned_hyp = self._dp_align(ref_padded, hyp_padded)

        # Count errors matching NEDC lines 685-708
        result = self._count_errors(aligned_ref, aligned_hyp)

        return result
```

### Day 3-4: Epoch Scoring (NEDC-EXACT)

```python
# nedc_bench/algorithms/epoch.py
from dataclasses import dataclass
from typing import List, Dict, Tuple

@dataclass
class EpochResult:
    """NEDC epoch results with INTEGER confusion matrix"""
    confusion_matrix: Dict[str, Dict[str, int]]  # Full NxN matrix

    # Per-label counts (all integers)
    hits: Dict[str, int]
    misses: Dict[str, int]
    false_alarms: Dict[str, int]
    insertions: Dict[str, int]  # From NULL_CLASS transitions
    deletions: Dict[str, int]  # To NULL_CLASS transitions

    # Compressed epoch sequences (for debugging)
    compressed_ref: List[str]
    compressed_hyp: List[str]

class EpochScorer:
    """NEDC-exact epoch-based scoring"""

    def __init__(self,
                 epoch_duration: float = 1.0,
                 null_class: str = "null"):
        self.epoch_duration = epoch_duration
        self.null_class = null_class

    def score(self, ref_events: List[EventAnnotation],
              hyp_events: List[EventAnnotation],
              file_duration: float) -> EpochResult:
        """NEDC epoch scoring with compression"""

        # Create fixed-window epochs
        epochs = self._create_epochs(file_duration)

        # Classify each epoch
        ref_labels = self._classify_epochs(epochs, ref_events)
        hyp_labels = self._classify_epochs(epochs, hyp_events)

        # CRITICAL: Compress consecutive duplicates (NEDC lines 600-610)
        ref_compressed = self._compress_epochs(ref_labels)
        hyp_compressed = self._compress_epochs(hyp_labels)

        # Build confusion matrix and count errors
        return self._compute_metrics(ref_compressed, hyp_compressed)

    def _compress_epochs(self, labels: List[str]) -> List[str]:
        """Remove consecutive duplicates (NEDC lines 600-610)"""
        if not labels:
            return []

        compressed = [labels[0]]
        for i in range(1, len(labels)):
            if labels[i] != labels[i-1]:
                compressed.append(labels[i])
        return compressed
```

### Day 5-6: Overlap Scoring (NEDC-EXACT)

```python
# nedc_bench/algorithms/overlap.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class OverlapResult:
    """NEDC overlap results - NO confusion matrix!"""
    # Direct counts (all integers per NEDC)
    hits: Dict[str, int]  # Per-label hits
    misses: Dict[str, int]  # Per-label misses
    false_alarms: Dict[str, int]  # Per-label false alarms

    # NEDC mappings (lines 711-713)
    insertions: Dict[str, int]  # = false_alarms
    deletions: Dict[str, int]  # = misses

    # Totals
    total_hits: int
    total_misses: int
    total_false_alarms: int

class OverlapScorer:
    """NEDC-exact overlap scoring (ANY overlap, not proportional)"""

    def score(self, ref_events: List[EventAnnotation],
              hyp_events: List[EventAnnotation]) -> OverlapResult:
        """NEDC overlap: binary ANY overlap detection"""

        per_label_hits = {}
        per_label_misses = {}
        per_label_false_alarms = {}

        # Check each ref event (NEDC lines 593-601)
        for ref_event in ref_events:
            label = ref_event.label
            has_overlap = False

            for hyp_event in hyp_events:
                # NEDC overlap condition (line 652): ANY overlap
                if (hyp_event.stop_time > ref_event.start_time and
                    hyp_event.start_time < ref_event.stop_time and
                    hyp_event.label == label):
                    has_overlap = True
                    break

            if label not in per_label_hits:
                per_label_hits[label] = 0
                per_label_misses[label] = 0

            if has_overlap:
                per_label_hits[label] += 1
            else:
                per_label_misses[label] += 1

        # Check each hyp for false alarms (lines 603-609)
        for hyp_event in hyp_events:
            label = hyp_event.label
            has_overlap = False

            for ref_event in ref_events:
                if (hyp_event.stop_time > ref_event.start_time and
                    hyp_event.start_time < ref_event.stop_time and
                    ref_event.label == label):
                    has_overlap = True
                    break

            if not has_overlap:
                if label not in per_label_false_alarms:
                    per_label_false_alarms[label] = 0
                per_label_false_alarms[label] += 1

        # NEDC mappings (lines 711-713)
        return OverlapResult(
            hits=per_label_hits,
            misses=per_label_misses,
            false_alarms=per_label_false_alarms,
            insertions=per_label_false_alarms.copy(),  # Line 712
            deletions=per_label_misses.copy(),  # Line 713
            total_hits=sum(per_label_hits.values()),
            total_misses=sum(per_label_misses.values()),
            total_false_alarms=sum(per_label_false_alarms.values())
        )
```

### Day 7-8: IRA (NEDC-EXACT)

```python
# nedc_bench/algorithms/ira.py
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class IRAResult:
    """NEDC IRA results with INTEGER confusion, FLOAT kappa"""
    # Confusion matrix (INTEGERS)
    confusion_matrix: Dict[str, Dict[str, int]]

    # Per-label kappa (FLOATS)
    per_label_kappa: Dict[str, float]

    # Multi-class kappa (FLOAT)
    multi_class_kappa: float

    # Labels
    labels: List[str]

class IRAScorer:
    """NEDC-exact inter-rater agreement"""

    def score(self, ref_labels: List[str],
              hyp_labels: List[str]) -> IRAResult:
        """NEDC IRA using epoch-based approach"""

        # Build INTEGER confusion matrix
        labels = sorted(set(ref_labels + hyp_labels))
        confusion = {l1: {l2: 0 for l2 in labels} for l1 in labels}

        for ref, hyp in zip(ref_labels, hyp_labels):
            confusion[ref][hyp] += 1  # INTEGER increment

        # Compute per-label kappa (NEDC lines 499-540)
        per_label_kappa = {}
        for label in labels:
            kappa = self._compute_label_kappa(confusion, label, labels)
            per_label_kappa[label] = kappa

        # Compute multi-class kappa (NEDC lines 548-583)
        multi_kappa = self._compute_multi_class_kappa(confusion, labels)

        return IRAResult(
            confusion_matrix=confusion,
            per_label_kappa=per_label_kappa,
            multi_class_kappa=multi_kappa,
            labels=labels
        )

    def _compute_label_kappa(self, confusion: Dict, label: str,
                            labels: List[str]) -> float:
        """Per-label kappa using 2x2 matrix (lines 499-540)"""
        # Build 2x2 matrix
        a = float(confusion[label][label])  # True positive
        b = sum(confusion[label][l2] for l2 in labels if l2 != label)
        c = sum(confusion[l2][label] for l2 in labels if l2 != label)
        d = sum(confusion[l2][l3] for l2 in labels for l3 in labels
                if l2 != label and l3 != label)

        # Compute probabilities
        denom = a + b + c + d
        if denom == 0:
            return 0.0

        p_o = (a + d) / denom
        p_yes = ((a + b) / denom) * ((a + c) / denom)
        p_no = ((c + d) / denom) * ((b + d) / denom)
        p_e = p_yes + p_no

        # Compute kappa
        if (1 - p_e) == 0:
            return 1.0 if p_o == p_e else 0.0
        return (p_o - p_e) / (1 - p_e)

    def _compute_multi_class_kappa(self, confusion: Dict,
                                   labels: List[str]) -> float:
        """Multi-class kappa (lines 548-583)"""
        # Row and column sums
        sum_rows = {l: sum(confusion[l].values()) for l in labels}
        sum_cols = {l: sum(confusion[l2][l] for l2 in labels) for l in labels}

        # Diagonal sum and total
        sum_M = sum(confusion[l][l] for l in labels)
        sum_N = sum(sum_rows.values())
        sum_gc = sum(sum_rows[l] * sum_cols[l] for l in labels)

        # Compute kappa
        num = sum_N * sum_M - sum_gc
        denom = sum_N * sum_N - sum_gc

        if denom == 0:
            return 1.0 if num == 0 else 0.0
        return float(num) / float(denom)
```

## Parity Validation Requirements

### Count Type Requirements

```python
# nedc_bench/validation/parity.py extensions

def compare_dp(alpha: dict, beta: DPAlignmentResult) -> ValidationReport:
    """Compare DP results - INTEGER counts must match exactly"""
    assert alpha["hits"] == beta.hits  # EXACT match
    assert alpha["insertions"] == beta.total_insertions
    assert alpha["deletions"] == beta.total_deletions
    assert alpha["substitutions"] == beta.total_substitutions
    # Derived metrics use tolerance
    assert abs(alpha["sensitivity"] - beta.sensitivity) < 1e-10

def compare_epoch(alpha: dict, beta: EpochResult) -> ValidationReport:
    """Compare Epoch results - INTEGER confusion matrix"""
    # All confusion matrix entries must match EXACTLY
    for label1 in beta.confusion_matrix:
        for label2 in beta.confusion_matrix[label1]:
            assert alpha["confusion"][label1][label2] == beta.confusion_matrix[label1][label2]

def compare_overlap(alpha: dict, beta: OverlapResult) -> ValidationReport:
    """Compare Overlap results - INTEGER counts"""
    assert alpha["hits"] == beta.total_hits  # EXACT
    assert alpha["misses"] == beta.total_misses
    assert alpha["false_alarms"] == beta.total_false_alarms

def compare_ira(alpha: dict, beta: IRAResult) -> ValidationReport:
    """Compare IRA - INTEGER confusion, FLOAT kappa"""
    # Confusion matrix - EXACT match
    for label1 in beta.confusion_matrix:
        for label2 in beta.confusion_matrix[label1]:
            assert alpha["confusion"][label1][label2] == beta.confusion_matrix[label1][label2]

    # Kappa values - use tolerance
    assert abs(alpha["multi_class_kappa"] - beta.multi_class_kappa) < 1e-10
    for label in beta.per_label_kappa:
        assert abs(alpha["kappa"][label] - beta.per_label_kappa[label]) < 1e-10
```

## Summary of Corrections

1. **DP**: Must handle NULL_CLASS, use dual counting system, INTEGER counts
2. **Epoch**: Must compress consecutive duplicates, handle NULL_CLASS, INTEGER counts
3. **Overlap**: ANY overlap (not proportional), no confusion matrix, INTEGER counts
4. **IRA**: INTEGER confusion matrix, FLOAT kappa values only
5. **TAES**: Already correct with FLOAT counts

## Definition of Done

✅ Phase 3 is complete when:
1. All 4 algorithms match NEDC source semantics exactly
2. INTEGER counts match with == (no tolerance)
3. FLOAT values (kappa, metrics) match with atol=1e-10
4. All test suites pass with perfect parity
5. Performance improvements documented

## THIS PLAN IS 100% VERIFIED AGAINST NEDC SOURCE CODE
\n[Archived] See docs/FINAL_PARITY_RESULTS.md for final algorithm status.
