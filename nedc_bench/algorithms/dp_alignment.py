"""DP Alignment algorithm - NEDC-EXACT implementation

SOLID Principles:
- Single Responsibility: Each class/method has one clear purpose
- Open/Closed: Extensible via inheritance, closed for modification
- Liskov Substitution: Interfaces are consistent
- Interface Segregation: Minimal, focused interfaces
- Dependency Inversion: Depend on abstractions (Result dataclass)
"""

from dataclasses import dataclass

import numpy as np

NULL_CLASS = "null"


@dataclass
class DPAlignmentResult:
    """NEDC DP alignment results with INTEGER counts

    All counts are integers per NEDC source lines 685-708.
    """

    # Primary counts (all integers per NEDC)
    hits: int
    substitutions: dict[str, dict[str, int]]
    insertions: dict[str, int]
    deletions: dict[str, int]

    # Aggregate counts
    total_insertions: int
    total_deletions: int
    total_substitutions: int

    # For parity validation
    true_positives: int
    false_positives: int
    false_negatives: int

    # Aligned sequences for debugging
    aligned_ref: list[str]
    aligned_hyp: list[str]


class DPAligner:
    """NEDC-exact Dynamic Programming alignment

    Implements the DP alignment algorithm from nedc_eeg_eval_dpalign.py
    with NULL_CLASS sentinel handling and integer counting.
    """

    def __init__(
        self, penalty_del: float = 1.0, penalty_ins: float = 1.0, penalty_sub: float = 1.0
    ):
        """Initialize with alignment penalties

        Args:
            penalty_del: Deletion penalty (default 1.0)
            penalty_ins: Insertion penalty (default 1.0)
            penalty_sub: Substitution penalty (default 1.0)
        """
        self.penalty_del = penalty_del
        self.penalty_ins = penalty_ins
        self.penalty_sub = penalty_sub

    def align(self, ref: list[str], hyp: list[str]) -> DPAlignmentResult:
        """NEDC-exact DP alignment matching lines 550-711

        Args:
            ref: Reference label sequence
            hyp: Hypothesis label sequence

        Returns:
            DPAlignmentResult with integer counts and aligned sequences
        """
        # Run DP alignment on raw sequences; padding is handled inside
        # _dp_align to ensure a single pair of NULL sentinels.
        aligned_ref, aligned_hyp = self._dp_align(ref, hyp)

        # Count errors matching NEDC lines 685-708
        result = self._count_errors(aligned_ref, aligned_hyp)

        return result

    def _dp_align(self, ref: list[str], hyp: list[str]) -> tuple[list[str], list[str]]:
        """Core DP alignment with backtracking (NEDC-exact)

        Mirrors nedc_eeg_eval_dpalign.py (lines ~560-712):
        - Pad sequences with NULL_CLASS at start/end
        - Build cost matrix and backpointers
        - Backtrack to produce aligned sequences with NULL_CLASS gaps
        """
        # Extract labels and pad with NULL_CLASS at both ends
        refi = [NULL_CLASS, *ref, NULL_CLASS]
        hypi = [NULL_CLASS, *hyp, NULL_CLASS]

        m = len(refi)
        n = len(hypi)

        # Cost and backpointer matrices
        d = np.zeros((m, n), dtype=float)
        etypes = np.full((m, n), fill_value=-1, dtype=int)  # -1 = null

        # Initialize borders
        for j in range(1, n):
            d[0, j] = d[0, j - 1] + self.penalty_ins
            etypes[0, j] = 1  # INS

        for i in range(1, m):
            d[i, 0] = d[i - 1, 0] + self.penalty_del
            etypes[i, 0] = 0  # DEL

        etypes[0, 0] = 2  # treat as SUB/MATCH for start

        # Fill interior
        for j in range(1, n):
            for i in range(1, m):
                d_del = d[i - 1, j] + self.penalty_del
                d_ins = d[i, j - 1] + self.penalty_ins
                d_sub = d[i - 1, j - 1]
                if refi[i] != hypi[j]:
                    d_sub += self.penalty_sub

                # Choose min and set error type: 0=DEL,1=INS,2=SUB/MATCH
                min_dist = d_sub
                et = 2
                if d_ins < min_dist:
                    min_dist = d_ins
                    et = 1
                if d_del < min_dist:
                    min_dist = d_del
                    et = 0
                d[i, j] = min_dist
                etypes[i, j] = et

        # Backtrack from (m-1,n-1) to (0,0)
        i = m - 1
        j = n - 1
        reft: list[str] = []
        hypt: list[str] = []

        while True:
            et = etypes[i, j]
            if et == 0:  # DEL
                reft.append(refi[i])
                hypt.append(NULL_CLASS)
                i -= 1
            elif et == 1:  # INS
                reft.append(NULL_CLASS)
                hypt.append(hypi[j])
                j -= 1
            elif et == 2:  # SUB/MATCH
                reft.append(refi[i])
                hypt.append(hypi[j])
                i -= 1
                j -= 1
            else:
                # Should not happen if matrices are set correctly
                reft.append(refi[i])
                hypt.append(hypi[j])
                i -= 1
                j -= 1

            if (i < 0) and (j < 0):
                break

        # Reverse to correct order
        refo = reft[::-1]
        hypo = hypt[::-1]
        return refo, hypo

    def _count_errors(self, aligned_ref: list[str], aligned_hyp: list[str]) -> DPAlignmentResult:
        """Count alignment errors matching NEDC lines 685-708

        Implements the dual counting system: hit/miss/false_alarm AND del/ins/sub.
        All counts are INTEGERS per NEDC.
        """
        hits = 0
        hits_per_label: dict[str, int] = {}
        substitutions: dict[str, dict[str, int]] = {}
        insertions: dict[str, int] = {}
        deletions: dict[str, int] = {}

        # Ignore first and last items (dummy nodes)
        for idx in range(1, len(aligned_ref) - 1):
            ref_label = aligned_ref[idx]
            hyp_label = aligned_hyp[idx]

            # Track insertions/deletions/substitutions (targets tracked on ref side)
            if ref_label == NULL_CLASS and hyp_label != NULL_CLASS:
                insertions[hyp_label] = insertions.get(hyp_label, 0) + 1
            elif hyp_label == NULL_CLASS and ref_label != NULL_CLASS:
                deletions[ref_label] = deletions.get(ref_label, 0) + 1
            elif ref_label != hyp_label:
                # Substitution matrix by ref->hyp when both not null
                substitutions.setdefault(ref_label, {})
                substitutions[ref_label][hyp_label] = substitutions[ref_label].get(hyp_label, 0) + 1

            # Track hits/misses/false alarms as in NEDC
            if ref_label == NULL_CLASS:
                # false alarm (not stored in result directly)
                pass
            elif hyp_label == NULL_CLASS:
                # miss
                pass
            elif ref_label == hyp_label:
                hits += 1
                # Track hits per label for NEDC-style TP calculation
                hits_per_label[ref_label] = hits_per_label.get(ref_label, 0) + 1
            else:
                # miss
                pass

        # Calculate totals (all integers)
        total_insertions = sum(insertions.values())
        total_deletions = sum(deletions.values())
        total_substitutions = sum(
            count for ref_label in substitutions for count in substitutions[ref_label].values()
        )

        # NEDC mapping to standard metrics
        # In NEDC convention for EEG, "seiz" is the positive class
        # True Positives = hits for positive class (seiz) only
        # False Negatives = deletions + substitutions for positive class
        positive_class = "seiz"
        true_positives = hits_per_label.get(positive_class, 0)

        # False positives = insertions of positive class
        false_positives = insertions.get(positive_class, 0)

        # False negatives = deletions + substitutions FROM positive class
        pos_deletions = deletions.get(positive_class, 0)
        pos_substitutions = sum(substitutions.get(positive_class, {}).values()) if positive_class in substitutions else 0
        false_negatives = pos_deletions + pos_substitutions

        return DPAlignmentResult(
            hits=hits,
            substitutions=substitutions,
            insertions=insertions,
            deletions=deletions,
            total_insertions=total_insertions,
            total_deletions=total_deletions,
            total_substitutions=total_substitutions,
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            aligned_ref=aligned_ref,
            aligned_hyp=aligned_hyp,
        )
