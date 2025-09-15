"""Tests for Beta pipeline data models"""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from nedc_bench.models.annotations import AnnotationFile, EventAnnotation
from ..utils import create_csv_bi_annotation


def test_event_annotation_validation():
    """Test event annotation validation"""
    # Valid annotation
    event = EventAnnotation(
        channel="TERM", start_time=0.0, stop_time=10.0, label="seiz", confidence=1.0
    )
    assert event.duration == 10.0

    # Invalid: stop < start
    with pytest.raises(ValidationError):
        EventAnnotation(
            channel="TERM", start_time=10.0, stop_time=5.0, label="seiz", confidence=1.0
        )


def test_csv_bi_parsing(test_data_dir):
    """Parse actual CSV_BI format files"""
    csv_file = test_data_dir / "ref" / "aaaaaasf_s001_t000.csv_bi"

    annotation_file = AnnotationFile.from_csv_bi(csv_file)

    assert annotation_file.version == "csv_v1.0.0"
    assert annotation_file.patient == "aaaaaasf_s001_t000"
    # Session not parsed from this format
    # assert annotation_file.session == "s001"
    assert len(annotation_file.events) > 0

    # Check first event structure
    first_event = annotation_file.events[0]
    assert first_event.channel == "TERM"
    assert first_event.start_time >= 0
    assert first_event.stop_time > first_event.start_time


def test_integration_with_existing_utils():
    """Beta models work with existing test utilities"""
    # Use existing utility to create test data
    events = [
        ("TERM", 10.0, 20.0, "seiz", 1.0),
        ("TERM", 30.0, 45.0, "seiz", 1.0),
    ]

    csv_file = create_csv_bi_annotation(events, patient_id="test_beta")

    try:
        # Parse with Beta model
        annotation = AnnotationFile.from_csv_bi(Path(csv_file))

        assert annotation.patient == "test_beta"
        assert len(annotation.events) == 2
        assert annotation.events[0].start_time == 10.0
        assert annotation.events[0].stop_time == 20.0

    finally:
        Path(csv_file).unlink()


def test_from_csv_bi_line():
    """Test parsing single CSV_BI line"""
    line = "TERM,10.0,20.0,seiz,1.0"
    event = EventAnnotation.from_csv_bi_line(line)

    assert event.channel == "TERM"
    assert event.start_time == 10.0
    assert event.stop_time == 20.0
    assert event.label == "seiz"
    assert event.confidence == 1.0


def test_invalid_csv_bi_line():
    """Test invalid CSV_BI line handling"""
    with pytest.raises(ValueError):
        EventAnnotation.from_csv_bi_line("invalid,line")


def test_file_not_found():
    """Test FileNotFoundError for missing file"""
    with pytest.raises(FileNotFoundError):
        AnnotationFile.from_csv_bi(Path("nonexistent.csv_bi"))


def test_malformed_csv_bi():
    """Test handling of malformed CSV_BI file"""
    with tempfile.NamedTemporaryFile(
        encoding="utf-8", mode="w", suffix=".csv_bi", delete=False
    ) as f:
        f.write("# version = tse_v1.0.0\n")
        f.write("# patient = test\n")
        f.write("# session = s001\n")
        f.write("channel,start_time,stop_time,label,confidence\n")
        f.write("invalid,csv,format\n")  # Malformed line
        f.write("TERM,10.0,20.0,seiz,1.0\n")  # Valid line
        f.flush()

        try:
            # Should handle gracefully
            annotation = AnnotationFile.from_csv_bi(Path(f.name))
            assert len(annotation.events) == 1  # Only valid line parsed
            assert annotation.events[0].start_time == 10.0
        finally:
            Path(f.name).unlink()
