"""
EXACT NEDC TAES Algorithm Implementation for Perfect Parity

This implements the PRECISE multi-overlap sequencing logic from NEDC v6.0.0,
including ovlp_ref_seqs and ovlp_hyp_seqs behavior.
"""

from dataclasses import dataclass
from typing import List, Tuple

from nedc_bench.models.annotations import EventAnnotation


@dataclass
class TAESResult:
    """TAES scoring results with fractional counts"""
    true_positives: float
    false_positives: float
    false_negatives: float
    true_negatives: float = 0.0

    @property
    def sensitivity(self) -> float:
        """TPR = TP / (TP + FN)"""
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator > 0 else 0.0

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
    def specificity(self) -> float:
        """Not computed by TAES"""
        return 0.0

    @property
    def accuracy(self) -> float:
        """Not meaningful for TAES"""
        return 0.0


class TAESExactScorer:
    """
    EXACT NEDC TAES implementation with full multi-overlap sequencing
    """

    def __init__(self, target_label: str = "seiz"):
        """Initialize scorer for specific label"""
        self.target_label = target_label

    def score(
        self, reference: List[EventAnnotation], hypothesis: List[EventAnnotation]
    ) -> TAESResult:
        """
        Score using EXACT NEDC algorithm with multi-overlap sequencing

        This matches NEDC v6.0.0 behavior EXACTLY, including:
        - ovlp_ref_seqs: When hyp spans multiple refs
        - ovlp_hyp_seqs: When ref is hit by multiple hyps
        """
        # Filter to target label only
        refs = [r for r in reference if r.label == self.target_label]
        hyps = [h for h in hypothesis if h.label == self.target_label]

        if not refs and not hyps:
            return TAESResult(0.0, 0.0, 0.0)

        # Initialize tracking
        ref_flags = [True] * len(refs)
        hyp_flags = [True] * len(hyps)

        total_hit = 0.0
        total_miss = 0.0
        total_fa = 0.0

        # Main NEDC loop - process each reference
        for r_idx in range(len(refs)):
            if not ref_flags[r_idx]:
                continue

            # Find overlapping hypotheses
            for h_idx in range(len(hyps)):
                if not hyp_flags[h_idx]:
                    continue

                if not self._overlaps(refs[r_idx], hyps[h_idx]):
                    continue

                # Compute partial scores based on which extends beyond which
                hit, miss, fa = self._compute_partial(
                    refs, hyps, r_idx, h_idx, ref_flags, hyp_flags
                )

                total_hit += hit
                total_miss += miss
                total_fa += fa

        # Add penalties for unmatched events
        for i, flag in enumerate(ref_flags):
            if flag:  # Unmatched reference
                total_miss += 1.0

        for j, flag in enumerate(hyp_flags):
            if flag:  # Unmatched hypothesis
                total_fa += 1.0

        return TAESResult(
            true_positives=total_hit,
            false_positives=total_fa,
            false_negatives=total_miss,
        )

    def _compute_partial(
        self, refs: List[EventAnnotation], hyps: List[EventAnnotation],
        r_idx: int, h_idx: int,
        ref_flags: List[bool], hyp_flags: List[bool]
    ) -> Tuple[float, float, float]:
        """
        Compute partial scores for overlapping ref-hyp pair

        Implements NEDC's logic:
        - If hyp extends beyond ref: use ovlp_ref_seqs
        - If ref extends beyond hyp: use ovlp_hyp_seqs
        """
        ref = refs[r_idx]
        hyp = hyps[h_idx]

        if hyp.stop_time >= ref.stop_time:
            # Hypothesis extends beyond or equals reference
            return self._ovlp_ref_seqs(refs, hyps, r_idx, h_idx, ref_flags, hyp_flags)
        else:
            # Reference extends beyond hypothesis
            return self._ovlp_hyp_seqs(refs, hyps, r_idx, h_idx, ref_flags, hyp_flags)

    def _ovlp_ref_seqs(
        self, refs: List[EventAnnotation], hyps: List[EventAnnotation],
        r_idx: int, h_idx: int,
        ref_flags: List[bool], hyp_flags: List[bool]
    ) -> Tuple[float, float, float]:
        """
        Handle case where hypothesis spans multiple references

        CRITICAL: Each additional overlapped ref adds +1.0 to miss!
        """
        # Calculate scores for first reference
        hit, fa = self._calc_hf(refs[r_idx], hyps[h_idx])
        miss = 1.0 - hit

        # Mark as processed
        ref_flags[r_idx] = False
        hyp_flags[h_idx] = False

        # Check for additional overlapping references
        # THIS IS THE KEY: Each additional ref adds +1.0 miss!
        for i in range(r_idx + 1, len(refs)):
            if ref_flags[i] and self._overlaps(refs[i], hyps[h_idx]):
                miss += 1.0  # FULL PENALTY for each additional ref!
                ref_flags[i] = False

        return hit, miss, fa

    def _ovlp_hyp_seqs(
        self, refs: List[EventAnnotation], hyps: List[EventAnnotation],
        r_idx: int, h_idx: int,
        ref_flags: List[bool], hyp_flags: List[bool]
    ) -> Tuple[float, float, float]:
        """
        Handle case where reference is hit by multiple hypotheses

        Multiple hyps can contribute to hit and reduce miss
        """
        # Calculate scores for first hypothesis
        hit, fa = self._calc_hf(refs[r_idx], hyps[h_idx])
        miss = 1.0 - hit

        # Mark as processed
        ref_flags[r_idx] = False
        hyp_flags[h_idx] = False

        # Check for additional overlapping hypotheses
        for j in range(h_idx + 1, len(hyps)):
            if hyp_flags[j] and self._overlaps(refs[r_idx], hyps[j]):
                ovlp_hit, ovlp_fa = self._calc_hf(refs[r_idx], hyps[j])
                hit += ovlp_hit
                miss -= ovlp_hit  # Reduce miss!
                fa += ovlp_fa
                hyp_flags[j] = False

        return hit, miss, fa

    def _calc_hf(self, ref: EventAnnotation, hyp: EventAnnotation) -> Tuple[float, float]:
        """
        Calculate fractional hit and false alarm (EXACT NEDC calc_hf)
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
        if start_h <= start_r and stop_h <= stop_r:
            hit = (stop_h - start_r) / ref_dur
            fa_duration = start_r - start_h
            fa = min(1.0, fa_duration / ref_dur)

        # Case 2: Post-prediction (hyp ends after ref)
        elif start_h >= start_r and stop_h >= stop_r:
            hit = (stop_r - start_h) / ref_dur
            fa_duration = stop_h - stop_r
            fa = min(1.0, fa_duration / ref_dur)

        # Case 3: Over-prediction (hyp covers entire ref)
        elif start_h < start_r and stop_h > stop_r:
            hit = 1.0
            fa_duration = (stop_h - stop_r) + (start_r - start_h)
            fa = min(1.0, fa_duration / ref_dur)

        # Case 4: Under-prediction (hyp entirely within ref)
        else:
            hit = (stop_h - start_h) / ref_dur
            fa = 0.0

        return (hit, fa)

    def _overlaps(self, event1: EventAnnotation, event2: EventAnnotation) -> bool:
        """Check if two events overlap temporally"""
        return (
            event1.start_time < event2.stop_time and
            event2.start_time < event1.stop_time
        )