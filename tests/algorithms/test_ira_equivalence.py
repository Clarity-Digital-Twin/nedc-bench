"""Tests for IRA label-mode vs event-mode equivalence."""

from nedc_bench.algorithms.ira import IRAScorer
from nedc_bench.models.annotations import EventAnnotation


def ev(start: float, stop: float, label: str) -> EventAnnotation:
    return EventAnnotation(
        channel="TERM", start_time=start, stop_time=stop, label=label, confidence=1.0
    )


def test_ira_label_vs_event_mode_equivalence():
    scorer = IRAScorer()
    epoch = 0.25
    dur = 1.0

    # Events: half seiz, half bckg
    ref_events = [ev(0.0, 0.5, "seiz"), ev(0.5, 1.0, "bckg")]
    hyp_events = [ev(0.0, 0.5, "seiz"), ev(0.5, 1.0, "bckg")]

    # Event mode
    res_event = scorer.score(
        ref_events, hyp_events, epoch_duration=epoch, file_duration=dur, null_class="bckg"
    )

    # Label mode: build labels at epoch midpoints
    n = int(dur / epoch)
    labels = ["seiz", "seiz", "bckg", "bckg"][:n]
    res_label = scorer.score(labels, labels, null_class="bckg")

    assert res_event.confusion_matrix == res_label.confusion_matrix
    assert abs(res_event.multi_class_kappa - res_label.multi_class_kappa) < 1e-8
