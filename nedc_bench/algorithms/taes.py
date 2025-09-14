"""
Time-Aligned Event Scoring (TAES) Algorithm
Based on NEDC v6.0.0 implementation

CRITICAL: NEDC TAES uses FRACTIONAL scoring, not binary matching!
- hit = overlap_duration / ref_duration
- fa = non_overlap_duration / ref_duration
- miss = 1 - hit (for unmatched refs)
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
    Matches NEDC v6.0.0 fractional scoring behavior
    """

    def __init__(self):
        """Initialize TAES scorer"""
        pass

    def score(
        self, reference: list[EventAnnotation], hypothesis: list[EventAnnotation]
    ) -> TAESResult:
        """
        Score hypothesis against reference using TAES fractional algorithm

        NEDC v6.0.0 uses FRACTIONAL scoring:
        - hit = overlap_duration / ref_duration
        - fa = non_overlap_duration / ref_duration
        - miss = 1 - hit

        Args:
            reference: Ground truth events
            hypothesis: Predicted events

        Returns:
            TAESResult with scoring metrics
        """
        # Initialize fractional counters
        total_hit = 0.0
        total_miss = 0.0
        total_fa = 0.0

        # Track which events have been processed
        ref_flags = [True] * len(reference)
        hyp_flags = [True] * len(hypothesis)

        # Process each reference event
        for r_idx, ref_event in enumerate(reference):
            if not ref_flags[r_idx]:
                continue

            # Find all overlapping hypothesis events with same label
            for h_idx, hyp_event in enumerate(hypothesis):
                if not hyp_flags[h_idx]:
                    continue

                if ref_event.label != hyp_event.label:
                    continue

                # Check for overlap
                overlap_start = max(ref_event.start_time, hyp_event.start_time)
                overlap_end = min(ref_event.stop_time, hyp_event.stop_time)

                if overlap_end > overlap_start:
                    # Calculate fractional hit/fa
                    hit, fa = self._calc_hf(ref_event, hyp_event)
                    total_hit += hit
                    total_fa += fa

                    # Mark events as processed
                    ref_flags[r_idx] = False
                    hyp_flags[h_idx] = False
                    break  # Move to next ref event after first match

        # Count unmatched events as absolute misses/FAs
        # Only count events with same label that weren't matched
        for i, flag in enumerate(ref_flags):
            if flag:
                total_miss += 1.0

        for i, flag in enumerate(hyp_flags):
            if flag:
                total_fa += 1.0

        # Convert fractional to integer counts (rounding)
        true_positives = int(round(total_hit))
        false_negatives = int(round(total_miss))
        false_positives = int(round(total_fa))

        return TAESResult(
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
        )

    def _calc_hf(self, ref: EventAnnotation, hyp: EventAnnotation) -> tuple[float, float]:
        """
        Calculate fractional hit and false alarm between two events.
        Based on NEDC v6.0.0 calc_hf method.

        Args:
            ref: Reference event
            hyp: Hypothesis event

        Returns:
            (hit, fa) as fractional values
        """
        start_r = ref.start_time
        stop_r = ref.stop_time
        start_h = hyp.start_time
        stop_h = hyp.stop_time

        ref_dur = stop_r - start_r
        if ref_dur <= 0:
            return (0.0, 0.0)

        hit = 0.0
        fa = 0.0

        # Case 1: Pre-prediction (hyp starts before ref)
        #     ref:         <--------------------->\
        #     hyp:   <---------------->\
        if start_h <= start_r and stop_h <= stop_r:
            hit = (stop_h - start_r) / ref_dur
            fa_duration = start_r - start_h
            fa = min(1.0, fa_duration / ref_dur)

        # Case 2: Post-prediction (hyp ends after ref)
        #     ref:         <--------------------->\
        #     hyp:                  <-------------------->\
        elif start_h >= start_r and stop_h >= stop_r:
            hit = (stop_r - start_h) / ref_dur
            fa_duration = stop_h - stop_r
            fa = min(1.0, fa_duration / ref_dur)

        # Case 3: Over-prediction (hyp covers entire ref)
        #     ref:              <------->\
        #     hyp:        <------------------->\
        elif start_h < start_r and stop_h > stop_r:
            hit = 1.0
            fa_duration = (stop_h - stop_r) + (start_r - start_h)
            fa = min(1.0, fa_duration / ref_dur)

        # Case 4: Under-prediction (hyp entirely within ref)
        #     ref:        <--------------------->\
        #     hyp:            <------>\
        else:
            hit = (stop_h - start_h) / ref_dur
            fa = 0.0

        return (hit, fa)