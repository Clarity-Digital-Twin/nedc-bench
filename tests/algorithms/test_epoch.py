"""Test suite for Epoch Scoring algorithm - TDD approach"""

import pytest

from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.models.annotations import EventAnnotation


class TestEpochScoring:
    """Test Epoch Scoring following NEDC exact semantics"""

    @pytest.fixture
    def simple_events(self) -> tuple[list[EventAnnotation], list[EventAnnotation]]:
        """Simple test case with events"""
        ref = [
            EventAnnotation(
                label="seiz", start_time=0.0, stop_time=2.0, channel="TERM", confidence=1.0
            ),
            EventAnnotation(
                label="bckg", start_time=2.0, stop_time=5.0, channel="TERM", confidence=1.0
            ),
        ]
        hyp = [
            EventAnnotation(
                label="seiz", start_time=0.5, stop_time=2.5, channel="TERM", confidence=1.0
            ),
            EventAnnotation(
                label="bckg", start_time=2.5, stop_time=5.0, channel="TERM", confidence=1.0
            ),
        ]
        return ref, hyp

    @pytest.fixture
    def consecutive_duplicate_case(self) -> tuple[list[EventAnnotation], list[EventAnnotation]]:
        """Test case requiring consecutive duplicate compression"""
        ref = [
            EventAnnotation(
                label="seiz", start_time=0.0, stop_time=1.0, channel="TERM", confidence=1.0
            ),
            EventAnnotation(
                label="seiz",  # Consecutive duplicate
                start_time=1.0,
                stop_time=2.0,
                channel="TERM",
                confidence=1.0,
            ),
            EventAnnotation(
                label="bckg", start_time=2.0, stop_time=3.0, channel="TERM", confidence=1.0
            ),
        ]
        hyp = [
            EventAnnotation(
                label="seiz", start_time=0.0, stop_time=2.0, channel="TERM", confidence=1.0
            ),
            EventAnnotation(
                label="bckg", start_time=2.0, stop_time=3.0, channel="TERM", confidence=1.0
            ),
        ]
        return ref, hyp

    def test_epoch_scorer_initialization(self):
        """Test scorer initialization with epoch duration"""
        scorer = EpochScorer(epoch_duration=1.0, null_class="null")
        assert scorer.epoch_duration == 1.0
        assert scorer.null_class == "null"

    def test_epoch_compression_removes_consecutive_duplicates(self):
        """Test that consecutive duplicate labels are compressed"""
        scorer = EpochScorer()

        # Test compression
        labels = ["seiz", "seiz", "seiz", "bckg", "seiz", "seiz", "bckg", "bckg"]
        compressed = scorer._compress_epochs(labels)

        # NEDC semantics: remove consecutive duplicates
        assert compressed == ["seiz", "bckg", "seiz", "bckg"]

    def test_empty_compression(self):
        """Test compression of empty sequence"""
        scorer = EpochScorer()
        assert scorer._compress_epochs([]) == []

    def test_single_label_compression(self):
        """Test compression of single label"""
        scorer = EpochScorer()
        assert scorer._compress_epochs(["seiz"]) == ["seiz"]

    def test_confusion_matrix_is_integer(self, simple_events):
        """Test that confusion matrix contains only integers"""
        ref, hyp = simple_events
        scorer = EpochScorer(epoch_duration=1.0)
        result = scorer.score(ref, hyp, file_duration=5.0)

        # All confusion matrix entries must be integers
        for ref_label in result.confusion_matrix:
            for hyp_label in result.confusion_matrix[ref_label]:
                count = result.confusion_matrix[ref_label][hyp_label]
                assert isinstance(count, int), f"Count for {ref_label}->{hyp_label} must be int"

    def test_per_label_counts_are_integers(self, simple_events):
        """Test that all per-label counts are integers"""
        ref, hyp = simple_events
        scorer = EpochScorer(epoch_duration=1.0)
        result = scorer.score(ref, hyp, file_duration=5.0)

        # Check all per-label dictionaries
        for label_dict in [
            result.hits,
            result.misses,
            result.false_alarms,
            result.insertions,
            result.deletions,
        ]:
            for label, count in label_dict.items():
                assert isinstance(count, int), f"Count for {label} must be int"

    def test_null_class_transitions(self):
        """Test NULL_CLASS handling for insertions/deletions"""
        scorer = EpochScorer(epoch_duration=1.0, null_class="null")

        ref = [
            EventAnnotation(
                label="seiz", start_time=0.0, stop_time=2.0, channel="TERM", confidence=1.0
            )
        ]
        hyp = [
            EventAnnotation(
                label="seiz", start_time=1.0, stop_time=3.0, channel="TERM", confidence=1.0
            ),
            EventAnnotation(
                label="artf",  # False alarm/insertion
                start_time=3.0,
                stop_time=4.0,
                channel="TERM",
                confidence=1.0,
            ),
        ]

        result = scorer.score(ref, hyp, file_duration=5.0)

        # Check that insertions are tracked via NULL_CLASS transitions
        assert "artf" in result.insertions or "artf" in result.false_alarms

    def test_compressed_sequences_in_result(self, consecutive_duplicate_case):
        """Test that result contains compressed sequences for debugging"""
        ref, hyp = consecutive_duplicate_case
        scorer = EpochScorer(epoch_duration=1.0)
        result = scorer.score(ref, hyp, file_duration=3.0)

        # Compressed sequences should be present
        assert hasattr(result, "compressed_ref")
        assert hasattr(result, "compressed_hyp")

        # Check no consecutive duplicates in compressed sequences
        for i in range(1, len(result.compressed_ref)):
            assert result.compressed_ref[i] != result.compressed_ref[i - 1]
        for i in range(1, len(result.compressed_hyp)):
            assert result.compressed_hyp[i] != result.compressed_hyp[i - 1]

    def test_epoch_creation_with_fixed_windows(self):
        """Test that epochs are fixed-width windows"""
        scorer = EpochScorer(epoch_duration=1.0)
        epochs = scorer._create_epochs(file_duration=5.0)

        # Should have 5 epochs of 1 second each
        assert len(epochs) == 5
        for i, (start, end) in enumerate(epochs):
            assert start == i * 1.0
            assert end == (i + 1) * 1.0

    def test_epoch_classification(self):
        """Test epoch classification based on events"""
        scorer = EpochScorer(epoch_duration=1.0)

        events = [
            EventAnnotation(
                label="seiz", start_time=0.5, stop_time=1.5, channel="TERM", confidence=1.0
            )
        ]

        epochs = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]
        labels = scorer._classify_epochs(epochs, events)

        # First two epochs should be classified as "seiz"
        assert labels[0] == "seiz"  # 0.5-1.0 overlaps
        assert labels[1] == "seiz"  # 1.0-1.5 overlaps
        assert labels[2] == scorer.null_class  # No overlap
