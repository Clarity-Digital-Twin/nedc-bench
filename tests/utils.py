"""Test utilities for NEDC Alpha Pipeline"""

import contextlib
import tempfile
from pathlib import Path


def create_csv_bi_annotation(
    events: list[tuple[str, float, float, str, float]],
    duration: float = 1000.0,
    patient_id: str = "test_patient",
) -> str:
    """
    Create a temporary CSV_BI format annotation file.

    Args:
        events: List of (channel, start_time, stop_time, label, confidence)
        duration: Total duration in seconds
        patient_id: Patient identifier

    Returns:
        Path to the created temporary file
    """
    # Create temp file
    with tempfile.NamedTemporaryFile(
        encoding="utf-8", mode="w", suffix=".csv_bi", delete=False, prefix=f"{patient_id}_"
    ) as f:
        # Write CSV_BI header
        f.write("# version = csv_v1.0.0\n")
        f.write(f"# bname = {patient_id}\n")
        f.write(f"# duration = {duration:.4f} secs\n")
        f.write("# montage_file = nedc_eas_default_montage.txt\n")
        f.write("#\n")
        f.write("channel,start_time,stop_time,label,confidence\n")

        # Write events
        for channel, start, stop, label, conf in events:
            f.write(f"{channel},{start:.4f},{stop:.4f},{label},{conf:.4f}\n")

        return f.name


def create_test_list_file(csv_files: list[str]) -> str:
    """
    Create a list file pointing to CSV_BI files.

    Args:
        csv_files: List of paths to CSV_BI files

    Returns:
        Path to the created list file
    """
    with tempfile.NamedTemporaryFile(encoding="utf-8", mode="w", suffix=".list", delete=False) as f:
        for csv_file in csv_files:
            f.write(f"{Path(csv_file).absolute()}\n")
        return f.name


def cleanup_temp_files(*files) -> None:
    """Clean up temporary test files"""
    for file_path in files:
        if file_path and Path(file_path).exists():
            with contextlib.suppress(Exception):
                Path(file_path).unlink()


def create_perfect_match_pair() -> tuple[str, str]:
    """Create identical reference and hypothesis files for perfect scoring"""
    events = [
        ("TERM", 10.0, 20.0, "seiz", 1.0),
        ("TERM", 30.0, 45.0, "seiz", 1.0),
        ("TERM", 60.0, 75.0, "seiz", 1.0),
    ]

    ref_file = create_csv_bi_annotation(events, patient_id="perfect_ref")
    hyp_file = create_csv_bi_annotation(events, patient_id="perfect_hyp")

    return ref_file, hyp_file


def create_no_overlap_pair() -> tuple[str, str]:
    """Create files with no overlapping events"""
    ref_events = [
        ("TERM", 10.0, 20.0, "seiz", 1.0),
        ("TERM", 30.0, 40.0, "seiz", 1.0),
    ]

    hyp_events = [
        ("TERM", 50.0, 60.0, "seiz", 1.0),
        ("TERM", 70.0, 80.0, "seiz", 1.0),
    ]

    ref_file = create_csv_bi_annotation(ref_events, patient_id="no_overlap_ref")
    hyp_file = create_csv_bi_annotation(hyp_events, patient_id="no_overlap_hyp")

    return ref_file, hyp_file


def create_empty_reference_pair() -> tuple[str, str]:
    """Create empty reference with events in hypothesis"""
    ref_events = []  # No events

    hyp_events = [
        ("TERM", 10.0, 20.0, "seiz", 1.0),
        ("TERM", 30.0, 40.0, "seiz", 1.0),
    ]

    ref_file = create_csv_bi_annotation(ref_events, patient_id="empty_ref")
    hyp_file = create_csv_bi_annotation(hyp_events, patient_id="empty_hyp")

    return ref_file, hyp_file


def create_partial_overlap_pair() -> tuple[str, str]:
    """Create files with partial overlap"""
    ref_events = [
        ("TERM", 10.0, 30.0, "seiz", 1.0),  # 20 seconds
        ("TERM", 50.0, 70.0, "seiz", 1.0),  # 20 seconds
    ]

    hyp_events = [
        ("TERM", 20.0, 40.0, "seiz", 1.0),  # Overlaps 10s with first ref event
        ("TERM", 60.0, 80.0, "seiz", 1.0),  # Overlaps 10s with second ref event
    ]

    ref_file = create_csv_bi_annotation(ref_events, patient_id="partial_ref")
    hyp_file = create_csv_bi_annotation(hyp_events, patient_id="partial_hyp")

    return ref_file, hyp_file
