"""Additional IRA tests to cover label-mode and edge branches.

Covers:
- Label-mode confusion increments (line 84)
- _time_to_index returning -1 via event-mode with uncovered sample (line 62)
- _compute_label_kappa denom==0 (line 159) via label-mode mismatch length
- _compute_multi_class_kappa sum_n==0 (line 211) via label-mode mismatch length
"""

from nedc_bench.algorithms.ira import IRAScorer
from nedc_bench.models.annotations import EventAnnotation


def test_ira_label_mode_confusion_increments():
    scorer = IRAScorer()
    # Label mode: pass strings
    ref = ["A", "B", "A"]
    hyp = ["A", "C", "B"]

    res = scorer.score(ref, hyp)

    # Ensure confusion increments occurred
    assert res.confusion_matrix["A"]["A"] == 1
    assert res.confusion_matrix["B"]["C"] == 1
    assert res.confusion_matrix["A"]["B"] == 1


def test_ira_event_mode_time_to_index_no_cover():
    scorer = IRAScorer()
    # Event mode with a sample that is not covered by any event
    # epoch_duration=1.0 => sample at 0.5; event ends at 0.4, so -1 index path is used
    ref = [
        EventAnnotation(channel="TERM", start_time=0.0, stop_time=0.4, label="X", confidence=1.0)
    ]
    hyp = [
        EventAnnotation(channel="TERM", start_time=0.0, stop_time=0.4, label="X", confidence=1.0)
    ]

    res = scorer.score(ref, hyp, epoch_duration=1.0, file_duration=1.0)
    # With both -1, both map to null; ensure label exists and count is 1
    assert "null" in res.labels
    assert res.confusion_matrix["null"]["null"] == 1


def test_ira_label_mode_zero_counts_edge_paths():
    scorer = IRAScorer()
    # Label mode with mismatched lengths -> labels non-empty but zero counts
    ref = ["A"]
    hyp = []

    res = scorer.score(ref, hyp)

    # Per-label kappa for A should hit denom==0 path and return 0.0
    assert res.per_label_kappa.get("A", 0.0) == 0.0

    # Multi-class kappa should also see sum_n==0 and return 0.0
    assert res.multi_class_kappa == 0.0
