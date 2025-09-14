"""Parity test for multi-match TAES scenarios.

Ensures Alpha and Beta agree when one hypothesis overlaps
multiple reference events (and vice versa), locking matching policy.
"""

import os
from pathlib import Path

import pytest

from alpha.wrapper import NEDCAlphaWrapper
from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.models.annotations import AnnotationFile
from nedc_bench.validation.parity import ParityValidator
from tests.utils import create_csv_bi_annotation, cleanup_temp_files


@pytest.mark.integration
def test_parity_one_hyp_multiple_refs(setup_nedc_env: None) -> None:
    """One hypothesis spans two reference events: counts must match Alpha."""
    # Two non-overlapping ref events
    ref_events = [
        ("TERM", 10.0, 20.0, "seiz", 1.0),
        ("TERM", 30.0, 40.0, "seiz", 1.0),
    ]
    # One long hypothesis spanning both
    hyp_events = [("TERM", 15.0, 35.0, "seiz", 1.0)]

    ref_file = create_csv_bi_annotation(ref_events, patient_id="mm_ref")
    hyp_file = create_csv_bi_annotation(hyp_events, patient_id="mm_hyp")

    try:
        # Run Alpha
        alpha = NEDCAlphaWrapper(nedc_root=Path(os.environ["NEDC_NFC"]))
        alpha_result = alpha.evaluate(ref_file, hyp_file)

        # Run Beta
        ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
        hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))
        beta = TAESScorer()
        beta_result = beta.score(ref_ann.events, hyp_ann.events)

        # Compare
        validator = ParityValidator(tolerance=1e-10)
        report = validator.compare_taes(alpha_result["taes"], beta_result)

        assert report.passed, f"Discrepancy:\n{report}"
        # Lock expectations explicitly
        assert beta_result.true_positives >= 1
        assert beta_result.false_positives in {0, 1}
        assert beta_result.false_negatives in {0, 1}
    finally:
        cleanup_temp_files(ref_file, hyp_file)


@pytest.mark.integration
def test_parity_multiple_hyps_one_ref(setup_nedc_env: None) -> None:
    """Two hypotheses overlap one reference: counts must match Alpha."""
    ref_events = [("TERM", 20.0, 40.0, "seiz", 1.0)]
    hyp_events = [
        ("TERM", 15.0, 25.0, "seiz", 1.0),
        ("TERM", 35.0, 45.0, "seiz", 1.0),
    ]

    ref_file = create_csv_bi_annotation(ref_events, patient_id="mr_ref")
    hyp_file = create_csv_bi_annotation(hyp_events, patient_id="mr_hyp")

    try:
        alpha = NEDCAlphaWrapper(nedc_root=Path(os.environ["NEDC_NFC"]))
        alpha_result = alpha.evaluate(ref_file, hyp_file)

        ref_ann = AnnotationFile.from_csv_bi(Path(ref_file))
        hyp_ann = AnnotationFile.from_csv_bi(Path(hyp_file))
        beta = TAESScorer()
        beta_result = beta.score(ref_ann.events, hyp_ann.events)

        validator = ParityValidator(tolerance=1e-10)
        report = validator.compare_taes(alpha_result["taes"], beta_result)

        assert report.passed, f"Discrepancy:\n{report}"
        assert beta_result.true_positives >= 1
    finally:
        cleanup_temp_files(ref_file, hyp_file)

