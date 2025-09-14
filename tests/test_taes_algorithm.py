"""Tests for TAES algorithm implementation"""

from nedc_bench.algorithms.taes import TAESResult, TAESScorer
from nedc_bench.models.annotations import EventAnnotation


def test_taes_exact_match():
    """Perfect match should give perfect scores"""
    ref = [
        EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0),
        EventAnnotation(start_time=20, stop_time=30, label="seiz", confidence=1.0),
    ]
    hyp = [
        EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0),
        EventAnnotation(start_time=20, stop_time=30, label="seiz", confidence=1.0),
    ]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    assert result.sensitivity == 1.0
    assert result.precision == 1.0
    assert result.f1_score == 1.0
    assert result.true_positives == 2
    assert result.false_positives == 0
    assert result.false_negatives == 0


def test_taes_no_overlap():
    """No overlap should give zero sensitivity"""
    ref = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]
    hyp = [EventAnnotation(start_time=20, stop_time=30, label="seiz", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    assert result.sensitivity == 0.0
    assert result.precision == 0.0
    assert result.false_positives == 1
    assert result.false_negatives == 1


def test_taes_partial_overlap():
    """Test partial overlap detection"""
    ref = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]
    hyp = [EventAnnotation(start_time=5, stop_time=15, label="seiz", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    # TAES counts any overlap as detection
    assert result.true_positives == 1
    assert result.sensitivity == 1.0


def test_taes_empty_reference():
    """Empty reference means all hypotheses are FP"""
    ref = []
    hyp = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    assert result.false_positives == 1
    assert result.false_negatives == 0
    assert result.sensitivity == 0.0  # 0/0 case


def test_taes_empty_hypothesis():
    """Empty hypothesis means all references are FN"""
    ref = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]
    hyp = []

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    assert result.false_negatives == 1
    assert result.false_positives == 0
    assert result.precision == 0.0  # 0/0 case


def test_taes_label_mismatch():
    """Different labels should not match"""
    ref = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]
    hyp = [EventAnnotation(start_time=0, stop_time=10, label="bckg", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    assert result.true_positives == 0
    assert result.false_positives == 1
    assert result.false_negatives == 1


def test_taes_multiple_overlap():
    """One hypothesis overlapping multiple references"""
    ref = [
        EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0),
        EventAnnotation(start_time=20, stop_time=30, label="seiz", confidence=1.0),
    ]
    # Long hypothesis spanning both references
    hyp = [EventAnnotation(start_time=5, stop_time=25, label="seiz", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    # Both references detected, no false positives
    assert result.true_positives == 2
    assert result.false_positives == 0
    assert result.false_negatives == 0
    assert result.sensitivity == 1.0
    assert result.precision == 1.0


def test_taes_one_to_many():
    """One reference matched by multiple hypotheses"""
    ref = [EventAnnotation(start_time=10, stop_time=20, label="seiz", confidence=1.0)]
    hyp = [
        EventAnnotation(start_time=5, stop_time=15, label="seiz", confidence=1.0),
        EventAnnotation(start_time=15, stop_time=25, label="seiz", confidence=1.0),
    ]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    # One reference detected, no false positives (both hyp match same ref)
    assert result.true_positives == 1
    assert result.false_positives == 0
    assert result.false_negatives == 0


def test_taes_result_properties():
    """Test TAESResult property calculations"""
    result = TAESResult(true_positives=8, false_positives=2, false_negatives=2)

    assert result.sensitivity == 0.8  # 8/(8+2)
    assert result.precision == 0.8  # 8/(8+2)
    assert abs(result.f1_score - 0.8) < 1e-10  # 2*0.8*0.8/(0.8+0.8)
    assert result.specificity == 0.0  # TAES doesn't compute
    assert result.accuracy == 0.0  # Not meaningful for TAES


def test_taes_zero_division():
    """Test zero division cases"""
    result = TAESResult(true_positives=0, false_positives=0, false_negatives=0)

    assert result.sensitivity == 0.0
    assert result.precision == 0.0
    assert result.f1_score == 0.0
