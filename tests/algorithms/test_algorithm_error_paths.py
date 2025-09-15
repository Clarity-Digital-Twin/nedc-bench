"""Test error handling paths in algorithms for coverage."""

import pytest
from nedc_bench.algorithms.dp_alignment import DPAligner
from nedc_bench.algorithms.epoch import EpochScorer


class TestDPAlignmentErrors:
    """Test DP alignment error paths."""

    def test_dp_empty_references(self):
        """Test DP with empty reference."""
        aligner = DPAligner()
        result = aligner.align([], ["seiz", "bckg"])

        # Should handle gracefully
        assert result.total_ref == 0
        assert result.total_hyp == 2
        assert result.insertions == 2

    def test_dp_empty_hypothesis(self):
        """Test DP with empty hypothesis."""
        aligner = DPAligner()
        result = aligner.align(["seiz", "bckg"], [])

        # Should handle gracefully
        assert result.total_ref == 2
        assert result.total_hyp == 0
        assert result.deletions == 2

    def test_dp_both_empty(self):
        """Test DP with both empty."""
        aligner = DPAligner()
        result = aligner.align([], [])

        # Should handle gracefully
        assert result.total_ref == 0
        assert result.total_hyp == 0
        assert result.hits == 0

    def test_dp_single_element(self):
        """Test DP with single elements."""
        aligner = DPAligner()

        # Match
        result = aligner.align(["seiz"], ["seiz"])
        assert result.hits == 1
        assert result.true_positives == 1  # seiz is positive

        # Mismatch
        result = aligner.align(["seiz"], ["bckg"])
        assert result.hits == 0
        assert result.substitutions == 1

    def test_dp_unknown_labels(self):
        """Test DP with unknown label types."""
        aligner = DPAligner()
        result = aligner.align(
            ["unknown1", "unknown2", "seiz"],
            ["unknown1", "different", "seiz"]
        )

        # Should handle unknown labels
        assert result.hits == 2  # unknown1 and seiz match
        assert result.true_positives == 1  # Only seiz counts as TP
        assert result.substitutions == 1  # unknown2 -> different


class TestEpochScorerErrors:
    """Test Epoch scorer error paths."""

    def test_epoch_empty_inputs(self):
        """Test Epoch with empty inputs."""
        scorer = EpochScorer()

        # Empty reference
        result = scorer.score([], ["seiz", "bckg"])
        assert result.total_ref == 0
        assert result.total_hyp == 2

        # Empty hypothesis
        result = scorer.score(["seiz", "bckg"], [])
        assert result.total_ref == 2
        assert result.total_hyp == 0

        # Both empty
        result = scorer.score([], [])
        assert result.total_ref == 0
        assert result.total_hyp == 0

    def test_epoch_mismatched_lengths(self):
        """Test Epoch with mismatched lengths."""
        scorer = EpochScorer()

        # Hypothesis longer
        result = scorer.score(
            ["seiz", "bckg"],
            ["seiz", "bckg", "seiz", "bckg"]
        )
        # Should pad reference with nulls or handle gracefully
        assert result.total_ref == 2
        assert result.total_hyp == 4

        # Reference longer
        result = scorer.score(
            ["seiz", "bckg", "seiz", "bckg"],
            ["seiz", "bckg"]
        )
        # Should pad hypothesis with nulls or handle gracefully
        assert result.total_ref == 4
        assert result.total_hyp == 2

    def test_epoch_unknown_labels(self):
        """Test Epoch with unknown labels."""
        scorer = EpochScorer()
        result = scorer.score(
            ["unknown", "seiz", "bckg"],
            ["unknown", "seiz", "bckg"]
        )

        # Should handle unknown labels
        assert result.per_label_metrics is not None
        # Unknown labels might be treated as background or ignored

    def test_epoch_single_class_only(self):
        """Test Epoch with single class only."""
        scorer = EpochScorer()

        # All seizures
        result = scorer.score(
            ["seiz", "seiz", "seiz"],
            ["seiz", "seiz", "seiz"]
        )
        assert result.per_label_metrics["seiz"]["precision"] == 1.0
        assert result.per_label_metrics["seiz"]["recall"] == 1.0

        # All background
        result = scorer.score(
            ["bckg", "bckg", "bckg"],
            ["bckg", "bckg", "bckg"]
        )
        assert result.per_label_metrics["bckg"]["precision"] == 1.0
        assert result.per_label_metrics["bckg"]["recall"] == 1.0

    def test_epoch_extreme_imbalance(self):
        """Test Epoch with extreme class imbalance."""
        scorer = EpochScorer()

        # 99% background, 1% seizure
        ref = ["bckg"] * 99 + ["seiz"]
        hyp = ["bckg"] * 100  # Misses the single seizure

        result = scorer.score(ref, hyp)

        # Should have very low seizure recall
        assert result.per_label_metrics["seiz"]["recall"] == 0.0
        # But high background precision
        assert result.per_label_metrics["bckg"]["precision"] == 1.0