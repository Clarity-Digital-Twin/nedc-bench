"""Golden tests for perfect match scenarios"""

import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.utils import (
    cleanup_temp_files,
    create_empty_reference_pair,
    create_no_overlap_pair,
    create_partial_overlap_pair,
    create_perfect_match_pair,
)


def test_golden_exact_match():
    """Reference and hypothesis are identical - should score 100%"""
    # Skip if not in proper environment
    if not os.environ.get("NEDC_NFC"):
        print("Skipping: NEDC environment not configured")
        return

    from alpha.wrapper.nedc_wrapper import NEDCAlphaWrapper

    ref_file, hyp_file = create_perfect_match_pair()

    try:
        alpha_wrapper = NEDCAlphaWrapper(nedc_root=Path(os.environ["NEDC_NFC"]))
        result = alpha_wrapper.evaluate(ref_file, hyp_file)

        # Perfect match should yield 100% for all metrics
        assert (
            result["taes"]["sensitivity"] == 1.0
        ), f"TAES sensitivity: {result['taes']['sensitivity']}"
        assert (
            result["taes"]["specificity"] == 1.0
        ), f"TAES specificity: {result['taes']['specificity']}"
        assert result["taes"]["f1_score"] == 1.0, f"TAES F1: {result['taes']['f1_score']}"

        # Check other algorithms too
        assert result["epoch"]["sensitivity"] == 1.0
        assert result["overlap"]["sensitivity"] == 1.0

    finally:
        cleanup_temp_files(ref_file, hyp_file)


def test_no_overlap():
    """No overlapping events - should score 0% sensitivity"""
    if not os.environ.get("NEDC_NFC"):
        print("Skipping: NEDC environment not configured")
        return

    from alpha.wrapper.nedc_wrapper import NEDCAlphaWrapper

    ref_file, hyp_file = create_no_overlap_pair()

    try:
        alpha_wrapper = NEDCAlphaWrapper(nedc_root=Path(os.environ["NEDC_NFC"]))
        result = alpha_wrapper.evaluate(ref_file, hyp_file)

        # No overlap means 0% sensitivity (no true positives)
        assert result["taes"]["sensitivity"] == 0.0
        assert result["taes"]["true_positives"] == 0
        assert result["taes"]["false_positives"] > 0

    finally:
        cleanup_temp_files(ref_file, hyp_file)


def test_empty_reference():
    """Empty reference file - all hypothesis events are false positives"""
    if not os.environ.get("NEDC_NFC"):
        print("Skipping: NEDC environment not configured")
        return

    from alpha.wrapper.nedc_wrapper import NEDCAlphaWrapper

    ref_file, hyp_file = create_empty_reference_pair()

    try:
        alpha_wrapper = NEDCAlphaWrapper(nedc_root=Path(os.environ["NEDC_NFC"]))
        result = alpha_wrapper.evaluate(ref_file, hyp_file)

        # With no reference events, sensitivity is undefined (0/0)
        # But all hypothesis events are false positives
        assert result["taes"]["false_positives"] == 2
        assert result["taes"]["true_positives"] == 0

    finally:
        cleanup_temp_files(ref_file, hyp_file)


def test_partial_overlap():
    """Partial overlap - should have intermediate scores"""
    if not os.environ.get("NEDC_NFC"):
        print("Skipping: NEDC environment not configured")
        return

    from alpha.wrapper.nedc_wrapper import NEDCAlphaWrapper

    ref_file, hyp_file = create_partial_overlap_pair()

    try:
        alpha_wrapper = NEDCAlphaWrapper(nedc_root=Path(os.environ["NEDC_NFC"]))
        result = alpha_wrapper.evaluate(ref_file, hyp_file)

        # Note: NEDC's overlap algorithm counts ANY overlap as a full hit
        # So partial overlap can still give 100% sensitivity
        assert result["overlap"]["sensitivity"] > 0  # Has detections
        assert result["overlap"]["true_positives"] > 0

        # TAES algorithm should show partial overlap better
        assert 0 < result["taes"]["sensitivity"] <= 1.0

    finally:
        cleanup_temp_files(ref_file, hyp_file)
