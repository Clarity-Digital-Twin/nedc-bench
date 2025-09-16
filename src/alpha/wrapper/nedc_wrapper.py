"""
NEDC Alpha Pipeline Wrapper
Wraps the original NEDC v6.0.0 tool and parses text output to JSON
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .parsers import UnifiedOutputParser


class NEDCAlphaWrapper:
    """Wrapper around original NEDC v6.0.0 code"""

    def __init__(self, nedc_root: Path | None = None):
        """Initialize wrapper with NEDC installation path"""
        self.nedc_root = nedc_root or Path("/opt/nedc")

        # Set environment variables
        os.environ["NEDC_NFC"] = str(self.nedc_root)
        os.environ["PYTHONPATH"] = f"{self.nedc_root}/lib:{os.environ.get('PYTHONPATH', '')}"

        # Validate installation
        self._validate_installation()

        # Initialize parser
        self.parser = UnifiedOutputParser()

    def _validate_installation(self) -> None:
        """TDD: Verify NEDC installation"""
        if not self.nedc_root.exists():
            raise RuntimeError(f"NEDC root not found: {self.nedc_root}")

        lib_path = self.nedc_root / "lib"
        if not lib_path.exists():
            raise RuntimeError(f"NEDC lib not found: {lib_path}")

        eval_script = self.nedc_root / "bin" / "nedc_eeg_eval"
        if not eval_script.exists():
            raise RuntimeError(f"NEDC evaluation script not found: {eval_script}")

    def evaluate(self, ref_csv: str, hyp_csv: str, output_dir: str | None = None) -> dict[str, Any]:
        """
        Run nedc_eeg_eval on a single file pair by creating temp lists,
        then parse summary files into structured JSON (all 5 algorithms).

        Args:
            ref_csv: Path to reference CSV_BI file
            hyp_csv: Path to hypothesis CSV_BI file
            output_dir: Optional output directory (temp dir if not specified)

        Returns:
            Dictionary with parsed results from all 5 algorithms
        """
        # Use temp directory if output_dir not specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            temp_dir = None
        else:
            temp_dir = tempfile.TemporaryDirectory()
            output_path = Path(temp_dir.name)

        try:
            # Create temporary list files
            ref_list = output_path / "ref.list"
            hyp_list = output_path / "hyp.list"

            # Write absolute paths to list files
            ref_list.write_text(str(Path(ref_csv).absolute()) + "\n")
            hyp_list.write_text(str(Path(hyp_csv).absolute()) + "\n")

            # Build command
            cmd = [
                "python3",
                str(self.nedc_root / "bin" / "nedc_eeg_eval"),
                "--odir",
                str(output_path / "output"),
                str(ref_list),
                str(hyp_list),
            ]

            # Run NEDC evaluation
            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, env=os.environ.copy()
            )

            # Check for errors
            if result.returncode != 0:
                raise RuntimeError(f"NEDC evaluation failed:\n{result.stderr}")

            # Parse output files
            summary_file = output_path / "output" / "summary.txt"
            if not summary_file.exists():
                raise RuntimeError(f"Summary file not generated: {summary_file}")

            # Read summary text
            summary_text = summary_file.read_text()

            # Parse all algorithm outputs
            parsed_results = self.parser.parse_summary(summary_text, output_path / "output")

            return parsed_results

        finally:
            # Clean up temp directory if used
            if temp_dir:
                temp_dir.cleanup()

    def evaluate_batch(
        self, ref_list_file: str, hyp_list_file: str, output_dir: str
    ) -> dict[str, Any]:
        """
        Run NEDC evaluation on pre-existing list files (original mode).

        Args:
            ref_list_file: Path to reference list file
            hyp_list_file: Path to hypothesis list file
            output_dir: Output directory

        Returns:
            Dictionary with parsed results
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [
            "python3",
            str(self.nedc_root / "bin" / "nedc_eeg_eval"),
            "--odir",
            str(output_path),
            ref_list_file,
            hyp_list_file,
        ]

        # Run NEDC evaluation
        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, env=os.environ.copy()
        )

        if result.returncode != 0:
            raise RuntimeError(f"NEDC evaluation failed:\n{result.stderr}")

        # Parse output
        summary_file = output_path / "summary.txt"
        summary_text = summary_file.read_text()

        return self.parser.parse_summary(summary_text, output_path)
