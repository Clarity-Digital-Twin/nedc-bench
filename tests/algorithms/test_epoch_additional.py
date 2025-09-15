"""Additional tests for Epoch algorithm to improve coverage.

Covers:
- _compress_joint empty input path
- _compute_metrics: hits, misses, false alarms, insertions, deletions, and unaligned tails
- Helper paths: _create_epochs, _classify_epochs, _compress_epochs
"""

from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.models.annotations import EventAnnotation


def test_epoch_compress_joint_empty():
    scorer = EpochScorer()
    refo, hypo = scorer._compress_joint([], [])
    assert refo == []
    assert hypo == []


def test_epoch_compute_metrics_varied_paths():
    scorer = EpochScorer()

    # Construct compressed sequences to exercise all branches
    # Index-by-index:
    # 0: null vs null -> hit(null)
    # 1: seiz vs null -> miss(seiz) + deletion(seiz)
    # 2: null vs seiz -> miss(null) + insertion(seiz)
    # Tail: extra ref label 'bckg' -> miss(bckg) + deletion(bckg)
    ref_c = ["null", "seiz", "null", "bckg"]
    hyp_c = ["null", "null", "seiz"]

    result = scorer._compute_metrics(ref_c, hyp_c)

    # Confusion matrix entries
    assert result.confusion_matrix["null"]["null"] == 1
    assert result.confusion_matrix["seiz"]["null"] == 1
    assert result.confusion_matrix["null"]["seiz"] == 1

    # Hits/misses/false alarms
    assert result.hits["null"] == 1
    assert result.misses["seiz"] == 1
    assert result.misses["null"] == 1
    assert result.false_alarms["null"] == 1
    assert result.false_alarms["seiz"] == 1

    # Insertions/deletions
    assert result.insertions.get("seiz", 0) == 1  # null->seiz
    assert result.deletions.get("seiz", 0) == 1  # seiz->null

    # Unaligned tail handling (extra ref label)
    assert result.misses.get("bckg", 0) == 1
    assert result.deletions.get("bckg", 0) == 1


def test_epoch_helpers_create_classify_compress():
    scorer = EpochScorer(epoch_duration=1.0)

    # File duration: 3s => epochs: [0-1), [1-2), [2-3)
    epochs = scorer._create_epochs(3.0)
    assert epochs == [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]

    # One event overlapping first two epochs
    events = [EventAnnotation(start_time=0.2, stop_time=1.4, label="seiz", confidence=1.0)]
    labels = scorer._classify_epochs(epochs, events)

    # Any overlap sets the epoch label to the event label
    assert labels == ["seiz", "seiz", "null"]

    # Compression removes consecutive duplicates
    compressed = scorer._compress_epochs(labels)
    assert compressed == ["seiz", "null"]
