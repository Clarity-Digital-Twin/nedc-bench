"""Tests for NEDC wrapper functionality."""

import subprocess
from pathlib import Path

import pytest


class TestNEDCWrapper:
    """Test the NEDC wrapper script."""

    def test_wrapper_script_exists(self, project_root: Path) -> None:
        """Test that the wrapper script exists."""
        wrapper_path = project_root / "run_nedc.sh"
        assert wrapper_path.exists(), "Wrapper script not found"
        assert wrapper_path.is_file(), "Wrapper path is not a file"

    def test_wrapper_help_command(self, project_root: Path) -> None:
        """Test that the wrapper script shows help."""
        wrapper_path = project_root / "run_nedc.sh"
        result = subprocess.run(
            [str(wrapper_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Help command failed: {result.stderr}"
        assert "nedc_eeg_eval" in result.stdout.lower()
        assert "synopsis" in result.stdout.lower()

    def test_nedc_data_exists(self, test_data_dir: Path) -> None:
        """Test that NEDC test data is present."""
        assert test_data_dir.exists(), "Test data directory not found"

        # Check for ref and hyp subdirectories
        ref_dir = test_data_dir / "ref"
        hyp_dir = test_data_dir / "hyp"

        assert ref_dir.exists(), "Reference data directory not found"
        assert hyp_dir.exists(), "Hypothesis data directory not found"

        # Check that CSV_BI files exist
        ref_files = list(ref_dir.glob("*.csv_bi"))
        hyp_files = list(hyp_dir.glob("*.csv_bi"))

        assert len(ref_files) > 0, "No reference CSV_BI files found"
        assert len(hyp_files) > 0, "No hypothesis CSV_BI files found"

    def test_list_files_exist(
        self,
        ref_list_file: Path,
        hyp_list_file: Path
    ) -> None:
        """Test that list files exist."""
        assert ref_list_file.exists(), "Reference list file not found"
        assert hyp_list_file.exists(), "Hypothesis list file not found"

        # Check that files have content
        assert ref_list_file.stat().st_size > 0, "Reference list file is empty"
        assert hyp_list_file.stat().st_size > 0, "Hypothesis list file is empty"