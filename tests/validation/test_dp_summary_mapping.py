"""Validation test to ensure DP parity uses summary totals when available."""

from nedc_bench.algorithms.dp_alignment import DPAlignmentResult
from nedc_bench.validation.parity import ParityValidator


def test_compare_dp_prefers_summary_totals():
    validator = ParityValidator(tolerance=0.0)

    # Alpha (parsed from NEDC summary): totals across all labels
    alpha = {
        "true_positives": 10,
        "false_positives": 3,
        "false_negatives": 2,
        "insertions": 3,
        "deletions": 2,
        "substitutions": 5,
    }

    # Beta DPAlignmentResult: positive-class metrics differ, but summary matches alpha
    beta = DPAlignmentResult(
        hits=0,
        substitutions={"seiz": {"bckg": 5}},
        insertions={"seiz": 3},
        deletions={"seiz": 2},
        total_insertions=3,
        total_deletions=2,
        total_substitutions=5,
        true_positives=7,  # positive-class only
        false_positives=3,  # positive-class
        false_negatives=2,  # positive-class
        sum_true_positives=10,  # totals across labels
        sum_false_positives=3,
        sum_false_negatives=2,
        aligned_ref=["null"],
        aligned_hyp=["null"],
    )

    report = validator.compare_dp(alpha, beta)
    assert report.passed
    assert len(report.discrepancies) == 0

