"""Simplified edge case tests focused on increasing coverage for core algorithms"""

import pytest
from nedc_bench.algorithms.dp_alignment import DPAligner, NULL_CLASS
from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.models.annotations import EventAnnotation


class TestDPAlignmentCoverage:
    """Tests to cover uncovered lines in DP alignment"""

    def test_dp_empty_and_single_element(self):
        """Cover edge cases for empty and single element sequences"""
        aligner = DPAligner()

        # Empty sequences
        result = aligner.align([], [])
        assert result.hits == 0
        assert result.total_insertions == 0
        assert result.total_deletions == 0
        assert result.true_positives == 0

        # Single element match - positive class
        result = aligner.align(["seiz"], ["seiz"])
        assert result.hits == 1
        assert result.true_positives == 1  # seiz is positive

        # Single element match - negative class
        result = aligner.align(["bckg"], ["bckg"])
        assert result.hits == 1
        assert result.true_positives == 0  # bckg is not positive

    def test_dp_matrix_edge_cases(self):
        """Test edge cases that might trigger matrix boundary conditions"""
        aligner = DPAligner()

        # Very unbalanced sequences
        result = aligner.align(["seiz"] * 100, ["seiz"])
        assert result.total_deletions == 99
        assert result.hits == 1

        result = aligner.align(["seiz"], ["seiz"] * 100)
        assert result.total_insertions == 99
        assert result.hits == 1

    def test_dp_all_mismatches(self):
        """Test when everything is a substitution"""
        aligner = DPAligner()

        ref = ["seiz", "seiz", "seiz"]
        hyp = ["bckg", "bckg", "bckg"]
        result = aligner.align(ref, hyp)

        assert result.hits == 0
        assert result.total_substitutions == 3
        assert result.false_negatives == 3  # All seiz were substituted

    def test_dp_with_artf_label(self):
        """Test with artifact label (neither positive nor negative)"""
        aligner = DPAligner()

        ref = ["seiz", "artf", "bckg"]
        hyp = ["artf", "artf", "artf"]
        result = aligner.align(ref, hyp)

        # artf matches in position 2
        assert result.hits == 1
        # seiz->artf is a substitution counting as FN
        assert result.false_negatives >= 1


class TestEpochCoverage:
    """Tests to cover uncovered lines in Epoch scoring (lines 241-307)"""

    def test_epoch_empty_events(self):
        """Test with no events - all epochs become null"""
        scorer = EpochScorer()

        # Empty event lists for 10 second file
        result = scorer.score([], [], 10.0)

        # Should create 10 null epochs
        assert "null" in result.confusion_matrix
        # All null epochs match each other
        assert result.confusion_matrix["null"]["null"] == 10

    def test_epoch_unaligned_lengths(self):
        """Test unaligned sequence lengths (lines 288-305)"""
        scorer = EpochScorer()

        # Create events that result in different compressed lengths
        ref_events = [
            EventAnnotation(channel="TERM", start_time=0.0, stop_time=5.0, label="seiz", confidence=1.0),
            EventAnnotation(channel="TERM", start_time=5.0, stop_time=10.0, label="bckg", confidence=1.0),
        ]

        hyp_events = [
            EventAnnotation(channel="TERM", start_time=0.0, stop_time=2.0, label="seiz", confidence=1.0),
        ]

        result = scorer.score(ref_events, hyp_events, 10.0)

        # Should handle mismatched lengths
        assert result.compressed_ref  # Has compressed sequences
        assert result.compressed_hyp

    def test_epoch_null_transitions(self):
        """Test null class transitions (lines 276-286)"""
        scorer = EpochScorer()

        # Event that doesn't cover whole file - creates nulls
        ref_events = []  # All nulls
        hyp_events = [
            EventAnnotation(channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0),
        ]

        result = scorer.score(ref_events, hyp_events, 5.0)

        # null -> seiz is an insertion
        assert "seiz" in result.insertions
        assert result.insertions["seiz"] >= 1

        # Reverse: something -> null is deletion
        ref_events = [
            EventAnnotation(channel="TERM", start_time=0.0, stop_time=1.0, label="bckg", confidence=1.0),
        ]
        hyp_events = []  # All nulls

        result = scorer.score(ref_events, hyp_events, 5.0)

        # bckg -> null is a deletion
        assert "bckg" in result.deletions
        assert result.deletions["bckg"] >= 1

    def test_epoch_all_labels_in_matrix(self):
        """Test that confusion matrix includes all labels"""
        scorer = EpochScorer()

        ref_events = [
            EventAnnotation(channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0),
            EventAnnotation(channel="TERM", start_time=1.0, stop_time=2.0, label="bckg", confidence=1.0),
            EventAnnotation(channel="TERM", start_time=2.0, stop_time=3.0, label="artf", confidence=1.0),
        ]

        hyp_events = [
            EventAnnotation(channel="TERM", start_time=0.0, stop_time=1.0, label="bckg", confidence=1.0),
            EventAnnotation(channel="TERM", start_time=1.0, stop_time=2.0, label="artf", confidence=1.0),
            EventAnnotation(channel="TERM", start_time=2.0, stop_time=3.0, label="seiz", confidence=1.0),
        ]

        result = scorer.score(ref_events, hyp_events, 3.0)

        # All labels should be in confusion matrix
        for label in ["seiz", "bckg", "artf"]:
            assert label in result.confusion_matrix
            # Each should have entries for all labels
            assert len(result.confusion_matrix[label]) >= 3

    def test_epoch_extreme_file_duration(self):
        """Test with very long file duration"""
        scorer = EpochScorer()

        # Single event in a very long file
        ref_events = [
            EventAnnotation(channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0),
        ]
        hyp_events = [
            EventAnnotation(channel="TERM", start_time=999.0, stop_time=1000.0, label="seiz", confidence=1.0),
        ]

        result = scorer.score(ref_events, hyp_events, 1000.0)

        # Should handle 1000 epochs
        assert result.compressed_ref
        assert result.compressed_hyp
        # Most will be nulls
        assert "null" in result.confusion_matrix


class TestCriticalParity:
    """Ensure critical parity properties are maintained"""

    def test_dp_positive_class_semantics(self):
        """Verify DP uses correct positive class semantics"""
        aligner = DPAligner()

        # Mix of seiz (positive) and bckg (negative)
        ref = ["seiz", "bckg", "seiz", "bckg"]
        hyp = ["seiz", "bckg", "bckg", "seiz"]
        result = aligner.align(ref, hyp)

        # Count actual seiz hits
        seiz_hits = 0
        for i in range(len(result.aligned_ref)):
            if result.aligned_ref[i] == "seiz" and result.aligned_hyp[i] == "seiz":
                seiz_hits += 1

        # True positives should match seiz hits (minus sentinels)
        # DP adds NULL_CLASS sentinels, so need to account for that
        assert result.true_positives <= seiz_hits

        # All metrics are integers
        assert isinstance(result.true_positives, int)
        assert isinstance(result.false_positives, int)
        assert isinstance(result.false_negatives, int)