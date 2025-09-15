"""IRA (Inter-Rater Agreement) algorithm - NEDC-EXACT implementation

SOLID Principles:
- Single Responsibility: Kappa computation separate for per-label and multi-class
- Open/Closed: Extensible kappa formulas
- Liskov Substitution: Consistent result interface
- Interface Segregation: Focused methods for 2x2 and NxN matrices
- Dependency Inversion: Works with label sequences abstraction
"""

from dataclasses import dataclass
from typing import Dict, List

from nedc_bench.models.annotations import EventAnnotation


@dataclass
class IRAResult:
    """NEDC IRA results with INTEGER confusion, FLOAT kappa

    Per NEDC source:
    - Confusion matrix uses INTEGERS (counts)
    - Kappa values are FLOATS (agreement scores)
    """

    # Confusion matrix (INTEGERS)
    confusion_matrix: dict[str, dict[str, int]]

    # Per-label kappa (FLOATS)
    per_label_kappa: dict[str, float]

    # Multi-class kappa (FLOAT)
    multi_class_kappa: float

    # Labels
    labels: list[str]


class IRAScorer:
    """NEDC-exact inter-rater agreement

    Implements the IRA algorithm from nedc_eeg_eval_ira.py using epoch-based
    sampling to build an NxN confusion matrix at sample resolution, then
    computes Cohen's kappa per label and overall.
    """

    def _sample_times(self, epoch_duration: float, file_duration: float) -> List[float]:
        half = epoch_duration / 2.0
        t = half
        samples: List[float] = []
        while t <= file_duration + 1e-12:
            samples.append(t)
            t += epoch_duration
        return samples

    def _time_to_index(self, val: float, events: List[EventAnnotation]) -> int:
        for idx, ev in enumerate(events):
            if (val >= ev.start_time) and (val <= ev.stop_time):
                return idx
        return -1

    def score(
        self,
        ref_events: List[EventAnnotation],
        hyp_events: List[EventAnnotation],
        epoch_duration: float,
        file_duration: float,
        null_class: str = "null",
    ) -> IRAResult:
        """NEDC IRA using epoch-based sampling to build confusion matrix.

        Args:
            ref_events: Reference events
            hyp_events: Hypothesis events
            epoch_duration: Sampling epoch duration (seconds)
            file_duration: Total duration of the file
            null_class: Background/NULL class label

        Returns:
            IRAResult with integer confusion and kappa values.
        """
        # Determine labels
        labels = sorted({ev.label for ev in ref_events} | {ev.label for ev in hyp_events} | {null_class})
        confusion: Dict[str, Dict[str, int]] = {r: {c: 0 for c in labels} for r in labels}

        # Sample midpoints
        for t in self._sample_times(epoch_duration, file_duration):
            j = self._time_to_index(t, ref_events)
            k = self._time_to_index(t, hyp_events)
            rlab = ref_events[j].label if j >= 0 else null_class
            hlab = hyp_events[k].label if k >= 0 else null_class
            confusion[rlab][hlab] += 1

        # Compute per-label kappa (NEDC lines 499-540)
        per_label_kappa = {}
        for label in labels:
            kappa = self._compute_label_kappa(confusion, label, labels)
            per_label_kappa[label] = kappa

        # Compute multi-class kappa (NEDC lines 548-583)
        multi_kappa = self._compute_multi_class_kappa(confusion, labels)

        return IRAResult(confusion_matrix=confusion, per_label_kappa=per_label_kappa, multi_class_kappa=multi_kappa, labels=labels)

    def _compute_label_kappa(
        self, confusion: dict[str, dict[str, int]], label: str, labels: list[str]
    ) -> float:
        """Per-label kappa using 2x2 matrix (lines 499-540)

        Computes Cohen's kappa for a single label vs all others.

        Args:
            confusion: Full confusion matrix
            label: The label to compute kappa for
            labels: All labels

        Returns:
            Float kappa value for this label
        """
        # Build 2x2 matrix
        # a = true positive (both agree it's this label)
        a = float(confusion[label][label]) if label in confusion else 0.0

        # b = false positive (ref says label, hyp says other)
        b = (
            sum(confusion[label].get(l2, 0) for l2 in labels if l2 != label)
            if label in confusion
            else 0.0
        )

        # c = false negative (ref says other, hyp says label)
        c = sum(confusion.get(l2, {}).get(label, 0) for l2 in labels if l2 != label)

        # d = true negative (both agree it's not this label)
        d = sum(
            confusion.get(l2, {}).get(l3, 0)
            for l2 in labels
            for l3 in labels
            if label not in {l2, l3}
        )

        # Compute total
        denom = a + b + c + d
        if denom == 0:
            return 0.0

        # Compute observed agreement
        p_o = (a + d) / denom

        # Compute expected agreement
        p_yes = ((a + b) / denom) * ((a + c) / denom)
        p_no = ((c + d) / denom) * ((b + d) / denom)
        p_e = p_yes + p_no

        # Compute kappa
        if (1 - p_e) == 0:
            return 1.0 if p_o == p_e else 0.0

        return (p_o - p_e) / (1 - p_e)

    def _compute_multi_class_kappa(
        self, confusion: dict[str, dict[str, int]], labels: list[str]
    ) -> float:
        """Multi-class kappa (lines 548-583)

        Computes overall Cohen's kappa for all classes.

        Args:
            confusion: Full confusion matrix
            labels: All labels

        Returns:
            Float multi-class kappa value
        """
        # Handle empty case
        if not labels:
            return 0.0

        # Row and column sums
        sum_rows = {}
        sum_cols = {}

        for label in labels:
            # Row sum (sum across columns for this row)
            sum_rows[label] = sum(confusion.get(label, {}).get(l2, 0) for l2 in labels)
            # Column sum (sum across rows for this column)
            sum_cols[label] = sum(confusion.get(l2, {}).get(label, 0) for l2 in labels)

        # Diagonal sum (correct predictions)
        sum_m = sum(confusion.get(label, {}).get(label, 0) for label in labels)

        # Total count
        sum_n = sum(sum_rows.values())

        # Handle empty confusion matrix
        if sum_n == 0:
            return 0.0

        # Sum of products of marginals
        sum_gc = sum(sum_rows[label] * sum_cols[label] for label in labels)

        # Compute kappa
        num = sum_n * sum_m - sum_gc
        denom = sum_n * sum_n - sum_gc

        if denom == 0:
            return 1.0 if num == 0 else 0.0

        return float(num) / float(denom)
