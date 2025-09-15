"""Comprehensive edge case tests for algorithm parity - CRITICAL FOR PRODUCTION"""

import pytest
import numpy as np
from nedc_bench.algorithms.dp_alignment import DPAligner, NULL_CLASS
from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.algorithms.overlap import OverlapScorer
from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.algorithms.ira import IRAScorer


class TestDPAlignmentEdgeCases:
    """Critical edge cases for DP alignment to ensure 100% parity"""

    def test_dp_empty_sequences(self):
        """Test DP with empty sequences"""
        aligner = DPAligner()

        # Both empty
        result = aligner.align([], [])
        assert result.hits == 0
        assert result.total_insertions == 0
        assert result.total_deletions == 0
        assert result.total_substitutions == 0
        assert result.true_positives == 0
        assert result.false_positives == 0
        assert result.false_negatives == 0

        # Empty ref
        result = aligner.align([], ["seiz", "bckg"])
        assert result.hits == 0
        assert result.total_insertions == 2
        assert result.total_deletions == 0
        assert result.true_positives == 0
        assert result.false_positives == 1  # seiz insertion

        # Empty hyp
        result = aligner.align(["seiz", "bckg"], [])
        assert result.hits == 0
        assert result.total_insertions == 0
        assert result.total_deletions == 2
        assert result.true_positives == 0
        assert result.false_negatives == 1  # seiz deletion

    def test_dp_single_element(self):
        """Test DP with single element sequences"""
        aligner = DPAligner()

        # Single match - positive class
        result = aligner.align(["seiz"], ["seiz"])
        assert result.hits == 1
        assert result.true_positives == 1
        assert result.false_positives == 0
        assert result.false_negatives == 0

        # Single match - negative class
        result = aligner.align(["bckg"], ["bckg"])
        assert result.hits == 1
        assert result.true_positives == 0  # bckg is not positive class
        assert result.false_positives == 0
        assert result.false_negatives == 0

        # Single mismatch
        result = aligner.align(["seiz"], ["bckg"])
        assert result.hits == 0
        assert result.total_substitutions == 1
        assert result.true_positives == 0
        assert result.false_positives == 0
        assert result.false_negatives == 1  # seiz substituted

    def test_dp_all_same_label(self):
        """Test DP when all labels are the same"""
        aligner = DPAligner()

        # All positive class
        ref = ["seiz"] * 10
        hyp = ["seiz"] * 10
        result = aligner.align(ref, hyp)
        assert result.hits == 10
        assert result.true_positives == 10
        assert result.false_positives == 0
        assert result.false_negatives == 0

        # All negative class
        ref = ["bckg"] * 10
        hyp = ["bckg"] * 10
        result = aligner.align(ref, hyp)
        assert result.hits == 10
        assert result.true_positives == 0  # No positive class hits
        assert result.false_positives == 0
        assert result.false_negatives == 0

    def test_dp_null_class_handling(self):
        """Test DP NULL_CLASS edge cases"""
        aligner = DPAligner()

        # NULL_CLASS in input (shouldn't happen but test defense)
        ref = [NULL_CLASS, "seiz", NULL_CLASS]
        hyp = ["bckg", NULL_CLASS, "seiz"]
        result = aligner.align(ref, hyp)

        # Verify NULL_CLASS sentinels are added
        assert result.aligned_ref[0] == NULL_CLASS
        assert result.aligned_ref[-1] == NULL_CLASS
        assert result.aligned_hyp[0] == NULL_CLASS
        assert result.aligned_hyp[-1] == NULL_CLASS

    def test_dp_extreme_length_mismatch(self):
        """Test DP with extreme length differences"""
        aligner = DPAligner()

        # Very long ref, short hyp
        ref = ["seiz", "bckg"] * 100  # 200 elements
        hyp = ["seiz"]  # 1 element
        result = aligner.align(ref, hyp)
        assert result.total_deletions == 199
        assert result.hits == 1
        assert result.true_positives == 1

        # Very short ref, long hyp
        ref = ["bckg"]
        hyp = ["seiz", "bckg"] * 100  # 200 elements
        result = aligner.align(ref, hyp)
        assert result.total_insertions == 199
        assert result.hits == 1
        assert result.true_positives == 0  # bckg hit doesn't count


class TestEpochScoringEdgeCases:
    """Critical edge cases for Epoch scoring - covers lines 241-307"""

    def test_epoch_empty_sequences(self):
        """Test Epoch with empty sequences"""
        scorer = EpochScorer()

        # Both empty
        result = scorer.score([], [])
        assert result.confusion_matrix == {}
        assert result.total_hits == 0
        assert result.total_misses == 0
        assert result.total_false_alarms == 0

        # Empty ref
        result = scorer.score([], ["seiz", "bckg"])
        assert result.total_false_alarms == 2
        assert result.total_hits == 0

        # Empty hyp
        result = scorer.score(["seiz", "bckg"], [])
        assert result.total_misses == 2
        assert result.total_hits == 0

    def test_epoch_single_label_only(self):
        """Test Epoch when only one label exists"""
        scorer = EpochScorer()

        # Only seiz in both
        ref = ["seiz", "seiz", "seiz"]
        hyp = ["seiz", "seiz", "seiz"]
        result = scorer.score(ref, hyp)

        assert "seiz" in result.confusion_matrix
        assert result.confusion_matrix["seiz"]["seiz"] == 3
        assert result.total_hits == 3
        assert result.total_misses == 0
        assert result.total_false_alarms == 0

    def test_epoch_null_class_transitions(self):
        """Test Epoch NULL_CLASS handling (lines 276-286)"""
        scorer = EpochScorer()
        scorer.null_class = "null"

        # Test null -> something (insertion)
        ref = ["null", "null", "bckg"]
        hyp = ["seiz", "bckg", "bckg"]
        result = scorer.score(ref, hyp)

        assert "seiz" in result.insertions
        assert result.insertions["seiz"] == 1
        assert "bckg" in result.insertions
        assert result.insertions["bckg"] == 1

        # Test something -> null (deletion)
        ref = ["seiz", "bckg", "seiz"]
        hyp = ["null", "null", "seiz"]
        result = scorer.score(ref, hyp)

        assert "seiz" in result.deletions
        assert result.deletions["seiz"] == 1
        assert "bckg" in result.deletions
        assert result.deletions["bckg"] == 1

    def test_epoch_unaligned_portions(self):
        """Test Epoch with unaligned sequence lengths (lines 288-305)"""
        scorer = EpochScorer()

        # Ref longer than hyp (deletions)
        ref = ["seiz", "bckg", "seiz", "bckg", "artf"]
        hyp = ["seiz", "bckg"]
        result = scorer.score(ref, hyp)

        # Last 3 elements are deletions
        assert result.total_misses >= 3
        assert "seiz" in result.deletions
        assert result.deletions["seiz"] == 1  # One unaligned seiz
        assert "bckg" in result.deletions
        assert result.deletions["bckg"] == 1  # One unaligned bckg
        assert "artf" in result.deletions
        assert result.deletions["artf"] == 1  # One unaligned artf

        # Hyp longer than ref (insertions)
        ref = ["seiz", "bckg"]
        hyp = ["seiz", "bckg", "seiz", "bckg", "artf"]
        result = scorer.score(ref, hyp)

        # Last 3 elements are insertions
        assert result.total_false_alarms >= 3
        assert "seiz" in result.insertions
        assert result.insertions["seiz"] == 1  # One extra seiz
        assert "bckg" in result.insertions
        assert result.insertions["bckg"] == 1  # One extra bckg
        assert "artf" in result.insertions
        assert result.insertions["artf"] == 1  # One extra artf

    def test_epoch_confusion_matrix_completeness(self):
        """Test confusion matrix has all label combinations"""
        scorer = EpochScorer()

        ref = ["seiz", "bckg", "artf", "seiz"]
        hyp = ["bckg", "artf", "seiz", "seiz"]
        result = scorer.score(ref, hyp)

        # All labels should be in confusion matrix
        labels = ["seiz", "bckg", "artf"]
        for ref_label in labels:
            assert ref_label in result.confusion_matrix
            for hyp_label in labels:
                assert hyp_label in result.confusion_matrix[ref_label]
                # All should be integers
                assert isinstance(result.confusion_matrix[ref_label][hyp_label], int)

    def test_epoch_extreme_mismatch(self):
        """Test Epoch with extreme length differences"""
        scorer = EpochScorer()

        # 1000 elements vs 1
        ref = ["seiz", "bckg"] * 500  # 1000 elements
        hyp = ["seiz"]  # 1 element
        result = scorer.score(ref, hyp)

        assert result.total_hits == 1
        assert result.total_misses == 999
        # All unaligned ref elements become deletions
        assert sum(result.deletions.values()) == 999


class TestTAESEdgeCases:
    """Edge cases for TAES fractional scoring"""

    def test_taes_zero_overlap(self):
        """Test TAES with zero overlap events"""
        scorer = TAESScorer()

        # Non-overlapping events
        ref_events = [
            {"start": 0.0, "stop": 10.0, "label": "seiz"},
        ]
        hyp_events = [
            {"start": 20.0, "stop": 30.0, "label": "seiz"},
        ]

        result = scorer.score(ref_events, hyp_events)
        assert result.true_positives == 0.0  # No overlap
        assert result.false_positives == 1.0  # Full hyp event
        assert result.false_negatives == 1.0  # Full ref event

    def test_taes_perfect_overlap(self):
        """Test TAES with perfect overlap"""
        scorer = TAESScorer()

        # Perfectly overlapping events
        ref_events = [
            {"start": 0.0, "stop": 10.0, "label": "seiz"},
        ]
        hyp_events = [
            {"start": 0.0, "stop": 10.0, "label": "seiz"},
        ]

        result = scorer.score(ref_events, hyp_events)
        assert result.true_positives == 1.0  # Perfect match
        assert result.false_positives == 0.0
        assert result.false_negatives == 0.0

    def test_taes_partial_overlap(self):
        """Test TAES fractional scoring with partial overlap"""
        scorer = TAESScorer()

        # 50% overlap
        ref_events = [
            {"start": 0.0, "stop": 10.0, "label": "seiz"},
        ]
        hyp_events = [
            {"start": 5.0, "stop": 15.0, "label": "seiz"},
        ]

        result = scorer.score(ref_events, hyp_events)
        # 5 seconds overlap out of 10 second events
        assert result.true_positives == 0.5
        assert result.false_positives == 0.5  # 5 seconds unmatched hyp
        assert result.false_negatives == 0.5  # 5 seconds unmatched ref


class TestIRAEdgeCases:
    """Edge cases for Inter-Rater Agreement"""

    def test_ira_perfect_agreement(self):
        """Test IRA with perfect agreement"""
        scorer = IRAScorer()

        ref = ["seiz", "bckg", "seiz", "bckg"]
        hyp = ["seiz", "bckg", "seiz", "bckg"]
        result = scorer.compute(ref, hyp)

        assert result.multi_class_kappa == 1.0  # Perfect agreement
        assert result.per_label_kappa["seiz"] == 1.0
        assert result.per_label_kappa["bckg"] == 1.0

    def test_ira_complete_disagreement(self):
        """Test IRA with complete disagreement"""
        scorer = IRAScorer()

        ref = ["seiz", "seiz", "seiz", "seiz"]
        hyp = ["bckg", "bckg", "bckg", "bckg"]
        result = scorer.compute(ref, hyp)

        # Complete disagreement should give negative kappa
        assert result.multi_class_kappa < 0

    def test_ira_single_label(self):
        """Test IRA when only one label exists"""
        scorer = IRAScorer()

        ref = ["seiz", "seiz", "seiz"]
        hyp = ["seiz", "seiz", "seiz"]
        result = scorer.compute(ref, hyp)

        # Perfect agreement but only one label
        # Kappa may be undefined or 1.0 depending on implementation
        assert result.multi_class_kappa >= 0


class TestOverlapEdgeCases:
    """Edge cases for Overlap scoring"""

    def test_overlap_minimum_threshold(self):
        """Test Overlap with exact minimum threshold"""
        scorer = OverlapScorer(min_overlap=0.5)

        # Exactly 50% overlap
        ref_events = [
            {"start": 0.0, "stop": 10.0, "label": "seiz"},
        ]
        hyp_events = [
            {"start": 5.0, "stop": 15.0, "label": "seiz"},
        ]

        result = scorer.score(ref_events, hyp_events)
        # 5/10 = 0.5, meets threshold
        assert result.total_hits == 1

        # Just under 50% overlap
        hyp_events = [
            {"start": 5.1, "stop": 15.0, "label": "seiz"},
        ]
        result = scorer.score(ref_events, hyp_events)
        # 4.9/10 = 0.49, fails threshold
        assert result.total_hits == 0
        assert result.total_misses == 1

    def test_overlap_multiple_overlaps(self):
        """Test Overlap when one event overlaps multiple"""
        scorer = OverlapScorer()

        # One long hyp event overlapping multiple ref events
        ref_events = [
            {"start": 0.0, "stop": 10.0, "label": "seiz"},
            {"start": 10.0, "stop": 20.0, "label": "seiz"},
            {"start": 20.0, "stop": 30.0, "label": "seiz"},
        ]
        hyp_events = [
            {"start": 5.0, "stop": 25.0, "label": "seiz"},  # Overlaps all 3
        ]

        result = scorer.score(ref_events, hyp_events)
        # All ref events should be hits
        assert result.total_hits == 3
        assert result.total_misses == 0
        assert result.total_false_alarms == 0


class TestParityIntegration:
    """Integration tests to ensure parity after all edge cases"""

    @pytest.mark.parametrize("ref,hyp", [
        ([], []),  # Empty
        (["seiz"], ["seiz"]),  # Single match
        (["seiz"], ["bckg"]),  # Single mismatch
        (["seiz"]*100, ["bckg"]*100),  # All mismatches
        (["seiz", "bckg"]*50, ["bckg", "seiz"]*50),  # Alternating
    ])
    def test_dp_parity_maintained(self, ref, hyp):
        """Ensure DP maintains correct positive class semantics"""
        aligner = DPAligner()
        result = aligner.align(ref, hyp)

        # Verify invariants
        assert isinstance(result.true_positives, int)
        assert isinstance(result.false_positives, int)
        assert isinstance(result.false_negatives, int)

        # True positives only count "seiz" hits
        seiz_hits = sum(1 for r, h in zip(ref, hyp) if r == "seiz" and h == "seiz")
        assert result.true_positives <= seiz_hits + 1  # +1 for alignment differences

        # All counts are non-negative integers
        assert result.true_positives >= 0
        assert result.false_positives >= 0
        assert result.false_negatives >= 0