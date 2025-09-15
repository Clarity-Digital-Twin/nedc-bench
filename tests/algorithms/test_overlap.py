"""Test suite for Overlap Scoring algorithm - TDD approach"""

import pytest
from typing import List
from nedc_bench.algorithms.overlap import OverlapScorer, OverlapResult
from nedc_bench.models.annotations import EventAnnotation


class TestOverlapScoring:
    """Test Overlap Scoring following NEDC exact semantics"""

    @pytest.fixture
    def any_overlap_case(self) -> tuple[List[EventAnnotation], List[EventAnnotation]]:
        """Test case demonstrating ANY overlap (not proportional)"""
        ref = [
            EventAnnotation(
                label="seiz",
                start_time=1.0,
                stop_time=5.0,  # 4 second event
                channel="TERM",
                confidence=1.0
            )
        ]
        hyp = [
            EventAnnotation(
                label="seiz",
                start_time=4.5,
                stop_time=5.5,  # Only 0.5s overlap but counts as HIT
                channel="TERM",
                confidence=1.0
            )
        ]
        return ref, hyp

    @pytest.fixture
    def no_confusion_matrix_case(self) -> tuple[List[EventAnnotation], List[EventAnnotation]]:
        """Test case showing overlap doesn't build confusion matrix"""
        ref = [
            EventAnnotation(
                label="seiz",
                start_time=0.0,
                stop_time=2.0,
                channel="TERM",
                confidence=1.0
            ),
            EventAnnotation(
                label="bckg",
                start_time=2.0,
                stop_time=4.0,
                channel="TERM",
                confidence=1.0
            )
        ]
        hyp = [
            EventAnnotation(
                label="bckg",  # Wrong label but overlaps with seiz
                start_time=0.5,
                stop_time=1.5,
                channel="TERM",
                confidence=1.0
            ),
            EventAnnotation(
                label="seiz",  # Wrong position
                start_time=3.0,
                stop_time=3.5,
                channel="TERM",
                confidence=1.0
            )
        ]
        return ref, hyp

    @pytest.fixture
    def perfect_overlap_case(self) -> tuple[List[EventAnnotation], List[EventAnnotation]]:
        """Perfect overlap case"""
        events = [
            EventAnnotation(
                label="seiz",
                start_time=1.0,
                stop_time=2.0,
                channel="TERM",
                confidence=1.0
            ),
            EventAnnotation(
                label="bckg",
                start_time=3.0,
                stop_time=4.0,
                channel="TERM",
                confidence=1.0
            )
        ]
        return events, events  # Same events for ref and hyp

    def test_overlap_scorer_initialization(self):
        """Test scorer initialization"""
        scorer = OverlapScorer()
        assert scorer is not None

    def test_any_overlap_counts_as_hit(self, any_overlap_case):
        """Test that ANY overlap (even tiny) counts as full hit"""
        ref, hyp = any_overlap_case
        scorer = OverlapScorer()
        result = scorer.score(ref, hyp)

        # NEDC semantics: ANY overlap = hit
        assert result.hits["seiz"] == 1  # Full hit despite minimal overlap
        assert result.misses.get("seiz", 0) == 0
        assert result.total_hits == 1

    def test_no_confusion_matrix(self, no_confusion_matrix_case):
        """Test that overlap doesn't create confusion matrix"""
        ref, hyp = no_confusion_matrix_case
        scorer = OverlapScorer()
        result = scorer.score(ref, hyp)

        # NEDC line 686: "overlap method does not give us a confusion matrix"
        # We track hits/misses/false_alarms per label, not cross-label confusion
        assert not hasattr(result, 'confusion_matrix')

        # Each label tracked independently
        assert "seiz" in result.misses  # seiz ref has no seiz hyp overlap
        assert "bckg" in result.misses  # bckg ref has no bckg hyp overlap
        assert "bckg" in result.false_alarms  # bckg hyp has no bckg ref overlap
        assert "seiz" in result.false_alarms  # seiz hyp has no seiz ref overlap

    def test_all_counts_are_integers(self, perfect_overlap_case):
        """Test that all counts are integers"""
        ref, hyp = perfect_overlap_case
        scorer = OverlapScorer()
        result = scorer.score(ref, hyp)

        # Check all per-label dictionaries
        for label_dict in [result.hits, result.misses, result.false_alarms]:
            for label, count in label_dict.items():
                assert isinstance(count, int), f"Count for {label} must be int"

        # Check totals
        assert isinstance(result.total_hits, int)
        assert isinstance(result.total_misses, int)
        assert isinstance(result.total_false_alarms, int)

    def test_insertions_equal_false_alarms(self, no_confusion_matrix_case):
        """Test NEDC mapping: insertions = false_alarms"""
        ref, hyp = no_confusion_matrix_case
        scorer = OverlapScorer()
        result = scorer.score(ref, hyp)

        # NEDC line 712: insertions = false_alarms
        assert result.insertions == result.false_alarms

    def test_deletions_equal_misses(self, no_confusion_matrix_case):
        """Test NEDC mapping: deletions = misses"""
        ref, hyp = no_confusion_matrix_case
        scorer = OverlapScorer()
        result = scorer.score(ref, hyp)

        # NEDC line 713: deletions = misses
        assert result.deletions == result.misses

    def test_perfect_overlap_produces_all_hits(self, perfect_overlap_case):
        """Test perfect overlap case"""
        ref, hyp = perfect_overlap_case
        scorer = OverlapScorer()
        result = scorer.score(ref, hyp)

        assert result.total_hits == 2  # Both events match
        assert result.total_misses == 0
        assert result.total_false_alarms == 0
        assert result.hits["seiz"] == 1
        assert result.hits["bckg"] == 1

    def test_overlap_condition(self):
        """Test the exact NEDC overlap condition"""
        scorer = OverlapScorer()

        # Test various overlap scenarios
        ref = EventAnnotation(
            label="seiz",
            start_time=2.0,
            stop_time=5.0,
            channel="TERM",
            confidence=1.0
        )

        # Case 1: Overlap at start
        hyp1 = EventAnnotation(
            label="seiz",
            start_time=1.0,
            stop_time=3.0,  # Overlaps [2.0, 3.0]
            channel="TERM",
            confidence=1.0
        )
        result1 = scorer.score([ref], [hyp1])
        assert result1.hits["seiz"] == 1

        # Case 2: Overlap at end
        hyp2 = EventAnnotation(
            label="seiz",
            start_time=4.0,
            stop_time=6.0,  # Overlaps [4.0, 5.0]
            channel="TERM",
            confidence=1.0
        )
        result2 = scorer.score([ref], [hyp2])
        assert result2.hits["seiz"] == 1

        # Case 3: Complete containment
        hyp3 = EventAnnotation(
            label="seiz",
            start_time=3.0,
            stop_time=4.0,  # Completely inside ref
            channel="TERM",
            confidence=1.0
        )
        result3 = scorer.score([ref], [hyp3])
        assert result3.hits["seiz"] == 1

        # Case 4: No overlap - before
        hyp4 = EventAnnotation(
            label="seiz",
            start_time=0.0,
            stop_time=2.0,  # Ends exactly at ref start
            channel="TERM",
            confidence=1.0
        )
        result4 = scorer.score([ref], [hyp4])
        assert result4.hits.get("seiz", 0) == 0
        assert result4.misses["seiz"] == 1

        # Case 5: No overlap - after
        hyp5 = EventAnnotation(
            label="seiz",
            start_time=5.0,
            stop_time=7.0,  # Starts exactly at ref end
            channel="TERM",
            confidence=1.0
        )
        result5 = scorer.score([ref], [hyp5])
        assert result5.hits.get("seiz", 0) == 0
        assert result5.misses["seiz"] == 1

    def test_multiple_labels(self):
        """Test handling of multiple different labels"""
        ref = [
            EventAnnotation(
                label="seiz",
                start_time=0.0,
                stop_time=2.0,
                channel="TERM",
                confidence=1.0
            ),
            EventAnnotation(
                label="bckg",
                start_time=2.0,
                stop_time=4.0,
                channel="TERM",
                confidence=1.0
            ),
            EventAnnotation(
                label="artf",
                start_time=4.0,
                stop_time=6.0,
                channel="TERM",
                confidence=1.0
            )
        ]
        hyp = [
            EventAnnotation(
                label="seiz",
                start_time=0.5,
                stop_time=1.5,  # Hits seiz
                channel="TERM",
                confidence=1.0
            ),
            EventAnnotation(
                label="artf",
                start_time=4.5,
                stop_time=5.5,  # Hits artf
                channel="TERM",
                confidence=1.0
            ),
            EventAnnotation(
                label="null",
                start_time=6.0,
                stop_time=7.0,  # False alarm
                channel="TERM",
                confidence=1.0
            )
        ]

        scorer = OverlapScorer()
        result = scorer.score(ref, hyp)

        # Check per-label results
        assert result.hits["seiz"] == 1
        assert result.misses["bckg"] == 1  # No bckg in hyp
        assert result.hits["artf"] == 1
        assert result.false_alarms["null"] == 1  # No null in ref