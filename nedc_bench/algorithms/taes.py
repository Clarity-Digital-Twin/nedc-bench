"""
Time-Aligned Event Scoring (TAES) Algorithm
Based on NEDC v6.0.0 implementation
"""

from dataclasses import dataclass

from nedc_bench.models.annotations import EventAnnotation


@dataclass
class TAESResult:
    """TAES scoring results matching NEDC output format"""

    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int = 0  # TAES doesn't compute TN

    @property
    def sensitivity(self) -> float:
        """TPR = TP / (TP + FN)"""
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator > 0 else 0.0

    @property
    def specificity(self) -> float:
        """TNR = TN / (TN + FP) - Not computed by TAES"""
        return 0.0  # TAES doesn't compute specificity

    @property
    def precision(self) -> float:
        """PPV = TP / (TP + FP)"""
        denominator = self.true_positives + self.false_positives
        return self.true_positives / denominator if denominator > 0 else 0.0

    @property
    def f1_score(self) -> float:
        """F1 = 2 * (precision * sensitivity) / (precision + sensitivity)"""
        if self.precision + self.sensitivity == 0:
            return 0.0
        return 2 * (self.precision * self.sensitivity) / (self.precision + self.sensitivity)

    @property
    def accuracy(self) -> float:
        """(TP + TN) / (TP + TN + FP + FN) - Not meaningful for TAES"""
        return 0.0


class TAESScorer:
    """
    Time-Aligned Event Scoring implementation
    Matches NEDC v6.0.0 behavior exactly
    """

    def __init__(self, overlap_threshold: float = 0.0):
        """
        Initialize TAES scorer

        Args:
            overlap_threshold: Minimum overlap fraction (0.0 = any overlap counts)
                              NEDC uses 0.0 by default
        """
        self.overlap_threshold = overlap_threshold

    def score(
        self, reference: list[EventAnnotation], hypothesis: list[EventAnnotation]
    ) -> TAESResult:
        """
        Score hypothesis against reference using TAES algorithm

        Args:
            reference: Ground truth events
            hypothesis: Predicted events

        Returns:
            TAESResult with scoring metrics
        """
        # Track which events have been matched
        ref_matched: set[int] = set()
        hyp_matched: set[int] = set()

        # Check each hypothesis against each reference
        for h_idx, hyp_event in enumerate(hypothesis):
            for r_idx, ref_event in enumerate(reference):
                if self._events_overlap(ref_event, hyp_event):
                    ref_matched.add(r_idx)
                    hyp_matched.add(h_idx)

        # Count metrics
        true_positives = len(ref_matched)  # Reference events that were detected
        false_negatives = len(reference) - len(ref_matched)  # Missed events
        false_positives = len(hypothesis) - len(hyp_matched)  # Extra detections

        return TAESResult(
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
        )

    def _events_overlap(self, event1: EventAnnotation, event2: EventAnnotation) -> bool:
        """
        Check if two events overlap

        NEDC v6.0.0 behavior: ANY overlap counts as a match
        """
        # Events must have same label
        if event1.label != event2.label:
            return False

        # Check temporal overlap
        overlap_start = max(event1.start_time, event2.start_time)
        overlap_end = min(event1.stop_time, event2.stop_time)

        # Any overlap counts (NEDC default behavior)
        if overlap_end > overlap_start:
            if self.overlap_threshold == 0.0:
                return True

            # Optional: require minimum overlap fraction
            overlap_duration = overlap_end - overlap_start
            event1_duration = event1.duration
            overlap_fraction = overlap_duration / event1_duration
            return overlap_fraction >= self.overlap_threshold

        return False
