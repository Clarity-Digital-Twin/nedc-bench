"""Tests for EpochScorer sampling at boundaries."""

from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.models.annotations import EventAnnotation


def ev(start: float, stop: float, label: str = "seiz") -> EventAnnotation:
    return EventAnnotation(
        channel="TERM", start_time=start, stop_time=stop, label=label, confidence=1.0
    )


def test_epoch_sampling_two_midpoints():
    """With duration=0.5s and epoch=0.25s, expect 2 sample midpoints."""
    scorer = EpochScorer(epoch_duration=0.25, null_class="bckg")
    # single event covering entire duration
    ref_events = [ev(0.0, 0.5, "seiz")]
    hyp_events = [ev(0.0, 0.5, "seiz")]

    res = scorer.score(ref_events, hyp_events, file_duration=0.5)

    # Confusion on diagonal for seiz should have at least 2 counts (2 midpoints)
    assert res.confusion_matrix["seiz"]["seiz"] >= 2
