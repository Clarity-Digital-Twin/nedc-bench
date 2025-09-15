"""IRA (Inter-Rater Agreement) algorithm - NEDC-EXACT implementation

SOLID Principles:
- Single Responsibility: Kappa computation separate for per-label and multi-class
- Open/Closed: Extensible kappa formulas
- Liskov Substitution: Consistent result interface
- Interface Segregation: Focused methods for 2x2 and NxN matrices
- Dependency Inversion: Works with label sequences abstraction
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

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

    def _sample_times(self, epoch_duration: float, file_duration: float) -> list[float]:
        half = epoch_duration / 2.0
        t = half
        samples: list[float] = []
        # Match NEDC/Epoch inclusive boundary exactly (no epsilon)
        while t <= file_duration:
            samples.append(t)
            t += epoch_duration
        return samples

    def _time_to_index(self, val: float, events: list[EventAnnotation]) -> int:
        for idx, ev in enumerate(events):
            # Match NEDC exact boundary semantics using bitwise &
            if (val >= ev.start_time) & (val <= ev.stop_time):
                return idx
        return -1

    def score(
        self,
        ref: list[EventAnnotation] | list[str],
        hyp: list[EventAnnotation] | list[str],
        epoch_duration: float | None = None,
        file_duration: float | None = None,
        null_class: str = "null",
    ) -> IRAResult:
        """Compute IRA from labels or events.

        - Label mode: if `ref` contains strings, treat as epoch labels and build the confusion directly.
        - Event mode: if `ref` contains EventAnnotation, sample midpoints using epoch_duration and file_duration.
        """
        # Label mode
        if (not ref and not hyp) or (ref and isinstance(ref[0], str)):
            refs = cast(list[str], ref) if ref else []
            hyps = cast(list[str], hyp) if hyp else []
            labels: list[str] = sorted(set(refs + hyps)) if (refs or hyps) else []
            confusion: dict[str, dict[str, int]] = {r: {c: 0 for c in labels} for r in labels}
            for rlab, hlab in zip(refs, hyps):
                confusion[rlab][hlab] += 1
        else:
            # Event mode
            assert epoch_duration is not None and file_duration is not None, (
                "epoch_duration and file_duration required for event mode"
            )
            ref_events = cast(list[EventAnnotation], ref)
            hyp_events = cast(list[EventAnnotation], hyp)

            # Augment events to fill gaps with background, matching NEDC
            ref_events = self._augment_events(ref_events, file_duration, null_class)
            hyp_events = self._augment_events(hyp_events, file_duration, null_class)
            labels = sorted(
                {ev.label for ev in ref_events} | {ev.label for ev in hyp_events} | {null_class}
            )
            confusion = {r: {c: 0 for c in labels} for r in labels}
            for t in self._sample_times(epoch_duration, file_duration):
                j = self._time_to_index(t, ref_events)
                k = self._time_to_index(t, hyp_events)
                rlab = ref_events[j].label if j >= 0 else null_class
                hlab = hyp_events[k].label if k >= 0 else null_class
                confusion[rlab][hlab] += 1

        # Compute per-label kappa (NEDC lines 499-540)
        per_label_kappa: dict[str, float] = {}
        for label in labels:
            kappa = self._compute_label_kappa(confusion, label, labels)
            per_label_kappa[label] = kappa

        # Compute multi-class kappa (NEDC lines 548-583)
        multi_kappa = self._compute_multi_class_kappa(confusion, labels)

        return IRAResult(
            confusion_matrix=confusion,
            per_label_kappa=per_label_kappa,
            multi_class_kappa=multi_kappa,
            labels=labels,
        )

    def _augment_events(
        self,
        events: list[EventAnnotation],
        file_duration: float,
        null_class: str,
    ) -> list[EventAnnotation]:
        """Fill gaps between events with background to cover [0, duration].

        Mirrors NEDC ann augmentation used before IRA/Epoch sampling.
        """
        if not events:
            # If duration is non-positive, avoid creating zero-length background
            if file_duration <= 0.0:
                return []
            return [
                EventAnnotation(
                    channel="TERM",
                    start_time=0.0,
                    stop_time=file_duration,
                    label=null_class,
                    confidence=1.0,
                )
            ]

        augmented: list[EventAnnotation] = []
        curr = 0.0
        for ev in sorted(events, key=lambda e: e.start_time):
            if curr < ev.start_time:
                augmented.append(
                    EventAnnotation(
                        channel="TERM",
                        start_time=curr,
                        stop_time=ev.start_time,
                        label=null_class,
                        confidence=1.0,
                    )
                )
            augmented.append(ev)
            curr = ev.stop_time
        if curr < file_duration:
            augmented.append(
                EventAnnotation(
                    channel="TERM",
                    start_time=curr,
                    stop_time=file_duration,
                    label=null_class,
                    confidence=1.0,
                )
            )
        return augmented

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
        sum_rows: dict[str, int] = {}
        sum_cols: dict[str, int] = {}

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
