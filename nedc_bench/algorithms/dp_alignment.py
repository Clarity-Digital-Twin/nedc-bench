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
        # Add NULL_CLASS sentinels (NEDC lines 578-586)
        ref_padded = [NULL_CLASS, *ref, NULL_CLASS]
        hyp_padded = [NULL_CLASS, *hyp, NULL_CLASS]

        # Run DP alignment
        aligned_ref, aligned_hyp = self._dp_align(ref_padded, hyp_padded)

        # Count errors matching NEDC lines 685-708
        result = self._count_errors(aligned_ref, aligned_hyp)

        return result

    def _dp_align(self, ref: list[str], hyp: list[str]) -> tuple[list[str], list[str]]:
        """Core DP alignment with backtracking

        Implements NEDC lines 587-680: matrix construction and backtrack.
        """
        n_ref = len(ref)
        n_hyp = len(hyp)

        # Initialize DP matrix
        dp = np.zeros((n_ref + 1, n_hyp + 1))

        # Initialize first row (all insertions)
        for j in range(1, n_hyp + 1):
            dp[0][j] = dp[0][j - 1] + self.penalty_ins

        # Initialize first column (all deletions)
        for i in range(1, n_ref + 1):
            dp[i][0] = dp[i - 1][0] + self.penalty_del

        # Fill DP matrix
        for i in range(1, n_ref + 1):
            for j in range(1, n_hyp + 1):
                # Match/substitution cost
                if ref[i - 1] == hyp[j - 1]:
                    match_cost = dp[i - 1][j - 1]  # No penalty for match
                else:
                    match_cost = dp[i - 1][j - 1] + self.penalty_sub

                # Deletion cost
                del_cost = dp[i - 1][j] + self.penalty_del

                # Insertion cost
                ins_cost = dp[i][j - 1] + self.penalty_ins

                # Take minimum
                dp[i][j] = min(match_cost, del_cost, ins_cost)

        # Backtrack to get alignment
        aligned_ref = []
        aligned_hyp = []
        i, j = n_ref, n_hyp

        while i > 0 or j > 0:
            if i == 0:
                # Only insertions left
                aligned_ref.append("_GAP_")
                aligned_hyp.append(hyp[j - 1])
                j -= 1
            elif j == 0:
                # Only deletions left
                aligned_ref.append(ref[i - 1])
                aligned_hyp.append("_GAP_")
                i -= 1
            else:
                # Check which operation was used
                current = dp[i][j]

                # Check match/substitution
                if ref[i - 1] == hyp[j - 1]:
                    match_cost = dp[i - 1][j - 1]
                else:
                    match_cost = dp[i - 1][j - 1] + self.penalty_sub

                if current == match_cost:
                    # Match or substitution
                    aligned_ref.append(ref[i - 1])
                    aligned_hyp.append(hyp[j - 1])
                    i -= 1
                    j -= 1
                elif current == dp[i - 1][j] + self.penalty_del:
                    # Deletion
                    aligned_ref.append(ref[i - 1])
                    aligned_hyp.append("_GAP_")
                    i -= 1
                else:
                    # Insertion
                    aligned_ref.append("_GAP_")
                    aligned_hyp.append(hyp[j - 1])
                    j -= 1

        # Reverse to get correct order
        aligned_ref.reverse()
        aligned_hyp.reverse()

        return aligned_ref, aligned_hyp

    def _count_errors(self, aligned_ref: list[str], aligned_hyp: list[str]) -> DPAlignmentResult:
        """Count alignment errors matching NEDC lines 685-708

        Implements the dual counting system: hit/miss/false_alarm AND del/ins/sub.
        All counts are INTEGERS per NEDC.
        """
        hits = 0
        substitutions: dict[str, dict[str, int]] = {}
        insertions: dict[str, int] = {}
        deletions: dict[str, int] = {}

        for ref_label, hyp_label in zip(aligned_ref, aligned_hyp):
            # Skip NULL_CLASS sentinels from counting
            if ref_label == NULL_CLASS and hyp_label == NULL_CLASS:
                continue

            if ref_label == "_GAP_":
                # Insertion
                if hyp_label not in insertions:
                    insertions[hyp_label] = 0
                insertions[hyp_label] += 1  # INTEGER increment
            elif hyp_label == "_GAP_":
                # Deletion
                if ref_label not in deletions:
                    deletions[ref_label] = 0
                deletions[ref_label] += 1  # INTEGER increment
            elif ref_label == hyp_label:
                # Hit (exact match) - but not for NULL_CLASS
                if ref_label != NULL_CLASS:
                    hits += 1  # INTEGER increment
            else:
                # Substitution
                if ref_label not in substitutions:
                    substitutions[ref_label] = {}
                if hyp_label not in substitutions[ref_label]:
                    substitutions[ref_label][hyp_label] = 0
                substitutions[ref_label][hyp_label] += 1  # INTEGER increment

        # Calculate totals (all integers)
        total_insertions = sum(insertions.values())
        total_deletions = sum(deletions.values())
        total_substitutions = sum(
            count for ref_label in substitutions for count in substitutions[ref_label].values()
        )

        # NEDC mapping to standard metrics
        true_positives = hits
        false_positives = total_insertions
        false_negatives = total_deletions + total_substitutions

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
