"""Test suite for IRA (Inter-Rater Agreement) algorithm - TDD approach"""

import pytest

from nedc_bench.algorithms.ira import IRAScorer
from nedc_bench.models.annotations import EventAnnotation


class TestIRA:
    """Test IRA following NEDC exact semantics"""

    @pytest.fixture
    def perfect_agreement_case(self) -> tuple[list[EventAnnotation], list[EventAnnotation]]:
        """Perfect agreement case"""
        ref = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=4.0, stop_time=5.0, label="artf", confidence=1.0
            ),
        ]
        hyp = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=4.0, stop_time=5.0, label="artf", confidence=1.0
            ),
        ]
        return ref, hyp

    @pytest.fixture
    def no_agreement_case(self) -> tuple[list[EventAnnotation], list[EventAnnotation]]:
        """No agreement case"""
        ref = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="seiz", confidence=1.0
            ),
        ]
        hyp = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="bckg", confidence=1.0
            ),
        ]
        return ref, hyp

    @pytest.fixture
    def mixed_agreement_case(self) -> tuple[list[EventAnnotation], list[EventAnnotation]]:
        """Mixed agreement case"""
        ref = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=4.0, stop_time=5.0, label="artf", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=5.0, stop_time=6.0, label="null", confidence=1.0
            ),
        ]
        hyp = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=4.0, stop_time=5.0, label="artf", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=5.0, stop_time=6.0, label="artf", confidence=1.0
            ),
        ]
        return ref, hyp

    def test_ira_scorer_initialization(self):
        """Test scorer initialization"""
        scorer = IRAScorer()
        assert scorer is not None

    def test_confusion_matrix_is_integer(self, mixed_agreement_case):
        """Test that confusion matrix contains only integers"""
        ref, hyp = mixed_agreement_case
        scorer = IRAScorer()
        result = scorer.score(ref, hyp, epoch_duration=1.0, file_duration=6.0)

        # All confusion matrix entries must be integers
        for ref_label in result.confusion_matrix:
            for hyp_label in result.confusion_matrix[ref_label]:
                count = result.confusion_matrix[ref_label][hyp_label]
                assert isinstance(count, int), f"Count for {ref_label}->{hyp_label} must be int"

    def test_kappa_values_are_float(self, mixed_agreement_case):
        """Test that kappa values are floats"""
        ref, hyp = mixed_agreement_case
        scorer = IRAScorer()
        result = scorer.score(ref, hyp, epoch_duration=1.0, file_duration=6.0)

        # Per-label kappa values must be floats
        for label, kappa in result.per_label_kappa.items():
            assert isinstance(kappa, float), f"Kappa for {label} must be float"

        # Multi-class kappa must be float
        assert isinstance(result.multi_class_kappa, float)

    def test_perfect_agreement_kappa(self, perfect_agreement_case):
        """Test that perfect agreement yields kappa = 1.0"""
        ref, hyp = perfect_agreement_case
        scorer = IRAScorer()
        result = scorer.score(ref, hyp, epoch_duration=1.0, file_duration=5.0)

        # Perfect agreement should yield kappa close to 1.0
        assert abs(result.multi_class_kappa - 1.0) < 1e-10

        # Each label should also have perfect kappa
        for kappa in result.per_label_kappa.values():
            assert abs(kappa - 1.0) < 1e-10

    def test_no_agreement_kappa(self, no_agreement_case):
        """Test that no agreement yields zero or negative kappa"""
        ref, hyp = no_agreement_case
        scorer = IRAScorer()
        result = scorer.score(ref, hyp, epoch_duration=1.0, file_duration=3.0)

        # Complete disagreement should yield zero or negative kappa
        # In this case with 2 classes and complete disagreement, kappa = 0
        assert result.multi_class_kappa <= 0

    def test_confusion_matrix_structure(self, mixed_agreement_case):
        """Test confusion matrix structure and counts"""
        ref, hyp = mixed_agreement_case
        scorer = IRAScorer()
        result = scorer.score(ref, hyp, epoch_duration=1.0, file_duration=6.0)

        # Check that all labels are in the matrix
        expected_labels = sorted(set([ev.label for ev in ref] + [ev.label for ev in hyp]))
        assert sorted(result.labels) == expected_labels

        # Check matrix is square
        for ref_label in result.labels:
            assert ref_label in result.confusion_matrix
            for hyp_label in result.labels:
                assert hyp_label in result.confusion_matrix[ref_label]

        # Check total count matches number of samples (6 samples at 1s intervals)
        total_count = sum(
            result.confusion_matrix[r][h] for r in result.labels for h in result.labels
        )
        assert total_count == 6  # 6 samples at 0.5, 1.5, 2.5, 3.5, 4.5, 5.5

    def test_per_label_kappa_computation(self):
        """Test per-label kappa using 2x2 matrices"""
        # Simple case: mostly correct for one label
        ref = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=4.0, stop_time=5.0, label="bckg", confidence=1.0
            ),
        ]
        hyp = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="bckg", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=4.0, stop_time=5.0, label="bckg", confidence=1.0
            ),
        ]

        scorer = IRAScorer()
        result = scorer.score(ref, hyp, epoch_duration=1.0, file_duration=5.0)

        # seiz: 2 hits, 1 miss, 0 false alarms - should have positive kappa
        assert result.per_label_kappa["seiz"] > 0

        # bckg: 2 hits, 0 misses, 1 false alarm - should have positive kappa
        assert result.per_label_kappa["bckg"] > 0

    def test_multi_class_kappa_formula(self):
        """Test multi-class kappa computation"""
        ref = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="B", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="B", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=4.0, stop_time=5.0, label="C", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=5.0, stop_time=6.0, label="C", confidence=1.0
            ),
        ]
        hyp = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="B", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="B", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="C", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=4.0, stop_time=5.0, label="C", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=5.0, stop_time=6.0, label="A", confidence=1.0
            ),
        ]

        scorer = IRAScorer()
        result = scorer.score(ref, hyp, epoch_duration=1.0, file_duration=6.0)

        # Manual calculation check
        # Confusion: A->A:1, A->B:1, B->B:1, B->C:1, C->C:1, C->A:1
        # Diagonal sum = 3, Total = 6
        # Expected kappa should be moderate (not perfect, not terrible)
        assert 0 < result.multi_class_kappa < 1

    def test_empty_sequences(self):
        """Test handling of empty sequences"""
        scorer = IRAScorer()

        # Both empty
        result = scorer.score([], [], epoch_duration=1.0, file_duration=0.0)
        assert result.multi_class_kappa == 0.0  # No data = no agreement

    def test_single_label_case(self):
        """Test case with only one label type"""
        ref = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="seiz", confidence=1.0
            ),
        ]
        hyp = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="seiz", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="seiz", confidence=1.0
            ),
        ]

        scorer = IRAScorer()
        result = scorer.score(ref, hyp, epoch_duration=1.0, file_duration=3.0)

        # Perfect agreement on single label
        assert abs(result.multi_class_kappa - 1.0) < 1e-10
        assert abs(result.per_label_kappa["seiz"] - 1.0) < 1e-10

    def test_kappa_edge_cases(self):
        """Test kappa computation edge cases"""
        scorer = IRAScorer()

        # Case 1: All same label (no variance)
        ref1 = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="A", confidence=1.0
            ),
        ]
        hyp1 = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="A", confidence=1.0
            ),
        ]
        result1 = scorer.score(ref1, hyp1, epoch_duration=1.0, file_duration=4.0)
        assert abs(result1.multi_class_kappa - 1.0) < 1e-10

        # Case 2: Random agreement level
        ref2 = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="B", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="B", confidence=1.0
            ),
        ]
        hyp2 = [
            EventAnnotation(
                channel="TERM", start_time=0.0, stop_time=1.0, label="B", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=1.0, stop_time=2.0, label="A", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=2.0, stop_time=3.0, label="B", confidence=1.0
            ),
            EventAnnotation(
                channel="TERM", start_time=3.0, stop_time=4.0, label="A", confidence=1.0
            ),
        ]
        result2 = scorer.score(ref2, hyp2, epoch_duration=1.0, file_duration=4.0)
        # Complete reversal should give kappa < 0
        assert result2.multi_class_kappa < 0
