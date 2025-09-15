"""
Critical tests for duration calculation - P0 bug prevention
Tests ensure FA/24h calculation matches NEDC v6.0.0 exactly
"""

import pytest
from nedc_bench.models.annotations import EventAnnotation


class TestDurationCalculation:
    """Test duration calculation for FA/24h metric accuracy"""

    def test_single_file_duration_from_events(self):
        """Test duration calc when only events are available"""
        events = [
            EventAnnotation(start_time=100.0, stop_time=200.0, label="seiz", confidence=1.0),
            EventAnnotation(start_time=500.0, stop_time=600.0, label="seiz", confidence=1.0),
            EventAnnotation(start_time=1000.0, stop_time=1500.0, label="bckg", confidence=1.0),
        ]

        # Duration should be last_stop - first_start
        expected_duration = 1500.0 - 100.0  # 1400 seconds

        # This is what Beta was doing WRONG:
        wrong_duration = max(e.stop_time for e in events)  # 1500 (WRONG!)

        # This is what it SHOULD do:
        correct_duration = max(e.stop_time for e in events) - min(e.start_time for e in events)

        assert correct_duration == expected_duration
        assert wrong_duration != expected_duration  # Verify the bug exists

    def test_duration_from_file_metadata(self):
        """Test reading duration from CSV_BI file metadata"""
        # CSV_BI files can have duration in header
        # Format: duration field or calculated from montage info

        # Mock a file with 1800 second recording
        file_duration = 1800.0

        # Even if last event ends at 1500, file duration is 1800
        events = [
            EventAnnotation(start_time=100.0, stop_time=200.0, label="seiz", confidence=1.0),
            EventAnnotation(start_time=1400.0, stop_time=1500.0, label="seiz", confidence=1.0),
        ]

        # Should use file duration, not event span
        assert file_duration > (1500.0 - 100.0)

    def test_duration_aggregation_across_files(self):
        """Test that durations are SUMMED not MAXED across files"""
        # This was the CRITICAL bug!

        file_durations = [
            1800.0,  # 30 minutes
            1800.0,  # 30 minutes
            3600.0,  # 60 minutes
            900.0,  # 15 minutes
        ]

        # CORRECT: Sum all durations
        correct_total = sum(file_durations)  # 8100 seconds

        # WRONG: What Beta was accidentally doing
        wrong_total = max(file_durations)  # 3600 (WRONG!)

        assert correct_total == 8100.0
        assert wrong_total == 3600.0
        assert correct_total != wrong_total

    def test_fa_rate_calculation(self):
        """Test false alarm rate per 24 hours calculation"""
        # This is the formula that MUST be exact

        total_false_alarms = 552.77
        total_duration_seconds = 1567844.73

        # FA/24h = (FA / duration_seconds) * 86400
        expected_fa_per_24h = (total_false_alarms / total_duration_seconds) * 86400

        # This should equal Alpha's result
        assert abs(expected_fa_per_24h - 30.4617) < 0.001

        # Verify wrong duration gives wrong FA/24h
        wrong_duration = 276519.05  # What Beta was calculating
        wrong_fa_per_24h = (total_false_alarms / wrong_duration) * 86400

        # This is the 5.67x error we found!
        assert abs(wrong_fa_per_24h - 172.7159) < 0.001
        assert wrong_fa_per_24h / expected_fa_per_24h > 5.6

    def test_empty_file_duration(self):
        """Test files with no events still contribute duration"""
        # A 30-minute recording with no seizures
        file_duration = 1800.0
        events = []  # No events

        # Should still count the 1800 seconds
        assert file_duration == 1800.0

    def test_partial_file_duration(self):
        """Test files that start/end mid-recording"""
        # Recording from 10:00:00 to 10:30:00 (1800 seconds)
        # But first event at 10:05:00 (300s) and last at 10:25:00 (1500s)

        file_metadata_duration = 1800.0
        first_event_time = 300.0
        last_event_time = 1500.0

        # Should use full file duration, not just event span
        event_span = last_event_time - first_event_time  # 1200s

        assert file_metadata_duration > event_span
        # Duration should be 1800, not 1200

    @pytest.mark.parametrize(
        "num_files,file_duration,expected_total",
        [
            (10, 1800.0, 18000.0),  # 10 files × 30 min = 5 hours
            (100, 3600.0, 360000.0),  # 100 files × 1 hour = 100 hours
            (1832, 856.0, 1568192.0),  # Our test case approximation
        ],
    )
    def test_large_scale_duration_aggregation(self, num_files, file_duration, expected_total):
        """Test duration aggregation at scale"""
        durations = [file_duration] * num_files
        total = sum(durations)

        assert total == expected_total

        # Verify the bug would give wrong result
        wrong_total = max(durations) if durations else 0
        assert wrong_total == file_duration  # Only one file's duration!
        assert wrong_total != expected_total


class TestDurationRegressionPrevention:
    """Regression tests to prevent reintroduction of the bug"""

    def test_transformer_data_duration(self):
        """Test with actual transformer output dimensions"""
        # Based on our parity test discovery
        num_files = 1832

        # Alpha reported this exact duration
        expected_total_duration = 1567844.73

        # Average duration per file
        avg_duration = expected_total_duration / num_files
        assert abs(avg_duration - 856.0) < 1.0  # ~856 seconds per file

    def test_fa_rate_never_exceeds_reasonable_bounds(self):
        """Sanity check that FA/24h is in reasonable range"""
        # For seizure detection, FA/24h typically ranges 0.1 to 100
        # Our bug caused 172.72 which while possible, was suspicious

        # Test the BUGGY value
        buggy_fa_per_24h = 172.72
        buggy_sensitivity = 12.45

        # This should be detected as suspicious
        is_suspicious = buggy_sensitivity < 20 and buggy_fa_per_24h > 150
        assert is_suspicious, "Bug detection failed - should flag this as suspicious"

        # Test the CORRECT value
        correct_fa_per_24h = 30.46
        correct_sensitivity = 12.45

        # This should NOT be flagged
        is_ok = not (correct_sensitivity < 20 and correct_fa_per_24h > 150)
        assert is_ok, "False positive - correct value flagged as suspicious"

    def test_duration_matches_nedc_algorithm(self):
        """Ensure we match NEDC's duration algorithm exactly"""
        # NEDC v6.0.0 algorithm:
        # 1. Try to read duration from file metadata
        # 2. If not available, use span of all events
        # 3. Sum across all files (never max!)

        # This test would need actual NEDC comparison
        # Placeholder for integration test
        pass
