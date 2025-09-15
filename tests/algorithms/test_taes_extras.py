"""Extra TAES tests to cover edge paths not exercised by main tests."""

from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.models.annotations import EventAnnotation


def test_taes_zero_overlap_events():
    """Test TAES with non-overlapping events."""
    scorer = TAESScorer()

    # Events that don't overlap at all
    ref = [
        EventAnnotation(start_time=0.0, stop_time=1.0, label="seiz", confidence=1.0),
        EventAnnotation(start_time=5.0, stop_time=6.0, label="seiz", confidence=1.0)
    ]
    hyp = [
        EventAnnotation(start_time=2.0, stop_time=3.0, label="seiz", confidence=1.0),
        EventAnnotation(start_time=7.0, stop_time=8.0, label="seiz", confidence=1.0)
    ]

    result = scorer.score(ref, hyp)

    # No overlaps means no true positives
    assert result.true_positives == 0.0
    # All ref events are false negatives
    assert result.false_negatives == 2.0
    # All hyp events are false positives
    assert result.false_positives == 2.0


def test_taes_exact_overlap():
    """Test TAES with exactly overlapping events."""
    scorer = TAESScorer()

    # Perfect overlap
    ref = [EventAnnotation(start_time=1.0, stop_time=3.0, label="seiz", confidence=1.0)]
    hyp = [EventAnnotation(start_time=1.0, stop_time=3.0, label="seiz", confidence=1.0)]

    result = scorer.score(ref, hyp)

    # Perfect overlap = 1.0 true positive (100% of ref duration)
    assert result.true_positives == 1.0
    assert result.false_negatives == 0.0
    assert result.false_positives == 0.0


def test_taes_partial_overlap():
    """Test TAES with partial overlap."""
    scorer = TAESScorer()

    # 50% overlap: ref [1,3], hyp [2,4] -> overlap [2,3] = 1s out of 2s ref
    ref = [EventAnnotation(start_time=1.0, stop_time=3.0, label="seiz", confidence=1.0)]
    hyp = [EventAnnotation(start_time=2.0, stop_time=4.0, label="seiz", confidence=1.0)]

    result = scorer.score(ref, hyp)

    # 50% of ref is covered = 0.5 TP
    assert result.true_positives == 0.5
    # 50% of ref is uncovered = 0.5 FN
    assert result.false_negatives == 0.5
    # 50% of hyp is outside ref = 0.5 FP
    assert result.false_positives == 0.5
