"""Tests for OverlapScorer boundary conditions (strict any-overlap)."""

from nedc_bench.algorithms.overlap import OverlapScorer
from nedc_bench.models.annotations import EventAnnotation


def ev(start: float, stop: float, label: str = "seiz") -> EventAnnotation:
    return EventAnnotation(
        channel="TERM", start_time=start, stop_time=stop, label=label, confidence=1.0
    )


def test_no_overlap_on_tangent_boundary():
    """ref.stop == hyp.start must NOT count as overlap."""
    ref_events = [ev(0.0, 10.0, "seiz")]
    hyp_events = [ev(10.0, 20.0, "seiz")]

    res = OverlapScorer().score(ref_events, hyp_events)

    assert res.hits.get("seiz", 0) == 0
    assert res.misses.get("seiz", 0) == 1
    assert res.false_alarms.get("seiz", 0) == 1


def test_any_overlap_counts():
    """Any non-zero overlap should count as hit, regardless of length."""
    ref_events = [ev(0.0, 10.0, "seiz")]
    hyp_events = [ev(9.999, 12.0, "seiz")]

    res = OverlapScorer().score(ref_events, hyp_events)

    assert res.hits.get("seiz", 0) == 1
    assert res.misses.get("seiz", 0) == 0
    assert res.false_alarms.get("seiz", 0) == 0
