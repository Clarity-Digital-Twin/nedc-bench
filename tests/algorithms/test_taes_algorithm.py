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
    assert result.true_positives == 2.0  # TAES uses floats
    assert result.false_positives == 0.0
    assert result.false_negatives == 0.0


def test_taes_no_overlap():
    """No overlap should give zero sensitivity"""
    ref = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]
    hyp = [EventAnnotation(start_time=20, stop_time=30, label="seiz", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    assert result.sensitivity == 0.0
    assert result.precision == 0.0
    assert result.false_positives == 1.0  # TAES uses floats
    assert result.false_negatives == 1.0


def test_taes_partial_overlap():
    """Test partial overlap detection - TAES uses fractional scoring"""
    ref = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]
    hyp = [EventAnnotation(start_time=5, stop_time=15, label="seiz", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    # TAES uses fractional scoring: hit = overlap_duration / ref_duration
    # Overlap is 5 seconds (5-10), ref is 10 seconds, so hit = 0.5
    assert result.true_positives == 0.5
    assert result.false_negatives == 0.5  # miss = 1 - hit
    assert result.false_positives == 0.5  # FA from non-overlap portion
    assert result.sensitivity == 0.5  # 0.5 / (0.5 + 0.5)


def test_taes_empty_reference():
    """Empty reference means all hypotheses are FP"""
    ref = []
    hyp = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    assert result.false_positives == 1.0  # TAES uses floats
    assert result.false_negatives == 0.0
    assert result.sensitivity == 0.0  # 0/0 case


def test_taes_empty_hypothesis():
    """Empty hypothesis means all references are FN"""
    ref = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]
    hyp = []

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    assert result.false_negatives == 1.0  # TAES uses floats
    assert result.false_positives == 0.0
    assert result.precision == 0.0  # 0/0 case


def test_taes_label_mismatch():
    """Different labels should not match - NEDC filters by target label"""
    ref = [EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0)]
    hyp = [EventAnnotation(start_time=0, stop_time=10, label="bckg", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    # NEDC filters to target label (seiz), so bckg events are ignored
    assert result.true_positives == 0.0  # No seiz hyps to match
    assert result.false_positives == 0.0  # bckg is filtered out
    assert result.false_negatives == 1.0  # seiz ref unmatched


def test_taes_multiple_overlap():
    """One hypothesis overlapping multiple references - fractional scoring"""
    ref = [
        EventAnnotation(start_time=0, stop_time=10, label="seiz", confidence=1.0),
        EventAnnotation(start_time=20, stop_time=30, label="seiz", confidence=1.0),
    ]
    # Long hypothesis spanning both references
    hyp = [EventAnnotation(start_time=5, stop_time=25, label="seiz", confidence=1.0)]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    # NEDC multi-overlap sequencing:
    # First ref: hit = 0.5 (5-10 overlap / 10 duration), miss = 0.5
    # Second ref: adds +1.0 to miss (penalty for spanning multiple refs)
    # Total: TP = 0.5, FN = 1.5, FP = 1.0 (non-overlap portion 10-20)
    assert abs(result.true_positives - 0.5) < 1e-10
    assert abs(result.false_negatives - 1.5) < 1e-10
    assert abs(result.false_positives - 1.0) < 1e-10


def test_taes_one_to_many():
    """One reference matched by multiple hypotheses - fractional scoring"""
    ref = [EventAnnotation(start_time=10, stop_time=20, label="seiz", confidence=1.0)]
    hyp = [
        EventAnnotation(start_time=5, stop_time=15, label="seiz", confidence=1.0),
        EventAnnotation(start_time=15, stop_time=25, label="seiz", confidence=1.0),
    ]

    scorer = TAESScorer()
    result = scorer.score(ref, hyp)

    # Fractional: Both hyps overlap the ref
    # First hyp: 5 sec overlap (10-15), hit = 0.5
    # Second hyp: 5 sec overlap (15-20), hit = 0.5
    # Total hit = 1.0 (capped), miss = 0.0
    assert abs(result.true_positives - 1.0) < 1e-10
    assert abs(result.false_negatives - 0.0) < 1e-10


def test_taes_result_properties():
    """Test TAESResult property calculations with float counts"""
    result = TAESResult(true_positives=8.0, false_positives=2.0, false_negatives=2.0)

    assert result.sensitivity == 0.8  # 8/(8+2)
    assert result.precision == 0.8  # 8/(8+2)
    assert abs(result.f1_score - 0.8) < 1e-10  # 2*0.8*0.8/(0.8+0.8)
    assert result.specificity == 0.0  # TAES doesn't compute
    assert result.accuracy == 0.0  # Not meaningful for TAES


def test_taes_zero_division():
    """Test zero division cases"""
    result = TAESResult(true_positives=0.0, false_positives=0.0, false_negatives=0.0)

    assert result.sensitivity == 0.0
    assert result.precision == 0.0
    assert result.f1_score == 0.0
