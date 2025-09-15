"""End-to-end integration test for Phase 3 algorithms parity validation"""

import json
import tempfile
from pathlib import Path

import pytest

from alpha.wrapper.nedc_wrapper import NEDCAlphaWrapper as NEDCWrapper
from alpha.wrapper.parsers import UnifiedOutputParser
from nedc_bench.orchestration.dual_pipeline import DualPipelineOrchestrator


class TestIntegrationParity:
    """Integration tests for algorithm parity between Alpha and Beta pipelines"""

    @pytest.fixture
    def test_data_paths(self) -> tuple[Path, Path]:
        """Get paths to test CSV_BI files"""
        base = Path("nedc_eeg_eval/v6.0.0/data/csv")
        ref_file = base / "ref" / "aaaaaasf_s001_t000.csv_bi"
        hyp_file = base / "hyp" / "aaaaaasf_s001_t000.csv_bi"
        return ref_file, hyp_file

    @pytest.fixture
    def list_files(self, tmp_path) -> tuple[Path, Path]:
        """Create temporary list files for testing"""
        ref_list = tmp_path / "ref.list"
        hyp_list = tmp_path / "hyp.list"

        base = Path("nedc_eeg_eval/v6.0.0/data/csv")
        ref_file = base / "ref" / "aaaaaasf_s001_t000.csv_bi"
        hyp_file = base / "hyp" / "aaaaaasf_s001_t000.csv_bi"

        ref_list.write_text(str(ref_file.absolute()))
        hyp_list.write_text(str(hyp_file.absolute()))

        return ref_list, hyp_list

    @pytest.fixture
    def orchestrator(self):
        """Create dual pipeline orchestrator"""
        return DualPipelineOrchestrator()

    @pytest.mark.parametrize("algorithm", ["dp", "epoch", "overlap", "taes", "ira"])
    def test_algorithm_parity(self, algorithm, list_files, orchestrator, tmp_path):
        """Test parity for each algorithm"""
        ref_list, hyp_list = list_files

        # Run Alpha pipeline
        wrapper = NEDCWrapper(nedc_root=Path("nedc_eeg_eval/v6.0.0"))
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = Path(output_dir)

            # Run NEDC with specific algorithm
            algo_flag = {
                "dp": "-dpalign",
                "epoch": "-epoch",
                "overlap": "-ovlp",
                "taes": "-taes",
                "ira": "",  # IRA runs with all algorithms
            }[algorithm]

            # For integration test, we'll use the orchestrator's Alpha wrapper
            # which properly calls the NEDC tool
            import subprocess
            import os

            os.environ["NEDC_NFC"] = str(Path("nedc_eeg_eval/v6.0.0").absolute())
            os.environ["PYTHONPATH"] = str(Path("nedc_eeg_eval/v6.0.0/lib").absolute())

            cmd = [
                "python3",
                "nedc_eeg_eval/v6.0.0/bin/nedc_eeg_eval",
                str(ref_list),
                str(hyp_list),
                "-o", str(output_path)
            ]
            if algo_flag:
                cmd.append(algo_flag)

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"NEDC failed: {result.stderr}")

            # Parse Alpha results
            summary_file = output_path / "summary.txt"
            assert summary_file.exists(), f"Summary file not created for {algorithm}"

            parser = UnifiedOutputParser()
            alpha_results = parser.parse_summary(
                summary_file.read_text(),
                output_path
            )

        # Run parity check via orchestrator
        ref_file = Path("nedc_eeg_eval/v6.0.0/data/csv/ref/aaaaaasf_s001_t000.csv_bi")
        hyp_file = Path("nedc_eeg_eval/v6.0.0/data/csv/hyp/aaaaaasf_s001_t000.csv_bi")

        parity_report = orchestrator.evaluate(
            algorithm=algorithm,
            ref_file=str(ref_file),
            hyp_file=str(hyp_file),
            alpha_result=alpha_results
        )

        # Assert parity (parity_report is a DualPipelineResult)
        assert parity_report.parity_passed, (
            f"Parity failed for {algorithm}:\n"
            f"Alpha: {json.dumps(parity_report.alpha_result.get(algorithm, {}), indent=2)}\n"
            f"Discrepancies: {parity_report.parity_report.discrepancies if parity_report.parity_report else 'N/A'}"
        )

        # Verify no discrepancies
        assert len(parity_report.parity_report.discrepancies) == 0, (
            f"Found {len(parity_report.parity_report.discrepancies)} discrepancies in {algorithm}"
        )

    def test_all_algorithms_sequential(self, list_files, orchestrator):
        """Test all algorithms in sequence with same data"""
        ref_list, hyp_list = list_files

        # Run Alpha pipeline with all algorithms
        wrapper = NEDCWrapper(nedc_root=Path("nedc_eeg_eval/v6.0.0"))
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = Path(output_dir)

            # Run NEDC with all algorithms (default)
            import subprocess
            import os

            os.environ["NEDC_NFC"] = str(Path("nedc_eeg_eval/v6.0.0").absolute())
            os.environ["PYTHONPATH"] = str(Path("nedc_eeg_eval/v6.0.0/lib").absolute())

            cmd = [
                "python3",
                "nedc_eeg_eval/v6.0.0/bin/nedc_eeg_eval",
                str(ref_list),
                str(hyp_list),
                "-o", str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"NEDC failed: {result.stderr}")

            # Parse Alpha results
            summary_file = output_path / "summary.txt"
            assert summary_file.exists(), "Summary file not created"

            parser = UnifiedOutputParser()
            alpha_results = parser.parse_summary(
                summary_file.read_text(),
                output_path
            )

        # Test each algorithm
        ref_file = Path("nedc_eeg_eval/v6.0.0/data/csv/ref/aaaaaasf_s001_t000.csv_bi")
        hyp_file = Path("nedc_eeg_eval/v6.0.0/data/csv/hyp/aaaaaasf_s001_t000.csv_bi")

        results = {}
        for algo in ["dp", "epoch", "overlap", "taes", "ira"]:
            parity_report = orchestrator.evaluate(
                algorithm=algo,
                ref_file=str(ref_file),
                hyp_file=str(hyp_file),
                alpha_result=alpha_results
            )

            results[algo] = {
                "passed": parity_report.parity_passed,
                "discrepancies": len(parity_report.parity_report.discrepancies) if parity_report.parity_report else 0
            }

            # Each should pass
            assert parity_report.parity_passed, (
                f"Parity failed for {algo}:\n"
                f"Alpha result: {json.dumps(parity_report.alpha_result.get(algo, {}), indent=2)}\n"
                f"Beta result: {parity_report.beta_result}\n"
                f"Report: {parity_report.parity_report}"
            )

        # Summary assertion
        assert all(r["passed"] for r in results.values()), (
            f"Not all algorithms passed parity:\n{json.dumps(results, indent=2)}"
        )

    def test_empty_files_handling(self, tmp_path, orchestrator):
        """Test handling of empty annotation files"""
        # Create empty CSV_BI files
        ref_file = tmp_path / "empty_ref.csv_bi"
        hyp_file = tmp_path / "empty_hyp.csv_bi"

        # CSV_BI header only, no events
        csv_bi_header = """version = csv_bi_v1.0.0
label_name = null,seiz,bckg,artf
montage_file = ./nedc_eeg_eval/params/montage.txt
"""
        ref_file.write_text(csv_bi_header)
        hyp_file.write_text(csv_bi_header)

        # Create list files
        ref_list = tmp_path / "ref.list"
        hyp_list = tmp_path / "hyp.list"
        ref_list.write_text(str(ref_file))
        hyp_list.write_text(str(hyp_file))

        # Run Alpha
        wrapper = NEDCWrapper(nedc_root=Path("nedc_eeg_eval/v6.0.0"))
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = Path(output_dir)
            import subprocess
            import os

            os.environ["NEDC_NFC"] = str(Path("nedc_eeg_eval/v6.0.0").absolute())
            os.environ["PYTHONPATH"] = str(Path("nedc_eeg_eval/v6.0.0/lib").absolute())

            cmd = [
                "python3",
                "nedc_eeg_eval/v6.0.0/bin/nedc_eeg_eval",
                str(ref_list),
                str(hyp_list),
                "-o", str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"NEDC failed: {result.stderr}")

            parser = UnifiedOutputParser()
            alpha_results = parser.parse_summary(
                (output_path / "summary.txt").read_text(),
                output_path
            )

        # Test each algorithm with empty data
        for algo in ["dp", "epoch", "overlap", "taes", "ira"]:
            parity_report = orchestrator.evaluate(
                algorithm=algo,
                ref_file=str(ref_file),
                hyp_file=str(hyp_file),
                alpha_result=alpha_results
            )

            # Should still pass parity even with empty data
            assert parity_report.parity_passed, f"Empty file parity failed for {algo}"

    def test_mismatched_labels(self, tmp_path, orchestrator):
        """Test with completely mismatched labels"""
        # Create CSV_BI files with different labels
        ref_file = tmp_path / "ref.csv_bi"
        hyp_file = tmp_path / "hyp.csv_bi"

        ref_content = """version = csv_bi_v1.0.0
label_name = null,seiz,bckg,artf
montage_file = ./nedc_eeg_eval/params/montage.txt
0.000,10.000,FP1-F7,seiz,1.0
10.000,20.000,FP1-F7,bckg,1.0
"""

        hyp_content = """version = csv_bi_v1.0.0
label_name = null,seiz,bckg,artf
montage_file = ./nedc_eeg_eval/params/montage.txt
0.000,10.000,FP1-F7,bckg,1.0
10.000,20.000,FP1-F7,artf,1.0
"""

        ref_file.write_text(ref_content)
        hyp_file.write_text(hyp_content)

        # Create list files
        ref_list = tmp_path / "ref.list"
        hyp_list = tmp_path / "hyp.list"
        ref_list.write_text(str(ref_file))
        hyp_list.write_text(str(hyp_file))

        # Run Alpha
        wrapper = NEDCWrapper(nedc_root=Path("nedc_eeg_eval/v6.0.0"))
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = Path(output_dir)
            import subprocess
            import os

            os.environ["NEDC_NFC"] = str(Path("nedc_eeg_eval/v6.0.0").absolute())
            os.environ["PYTHONPATH"] = str(Path("nedc_eeg_eval/v6.0.0/lib").absolute())

            cmd = [
                "python3",
                "nedc_eeg_eval/v6.0.0/bin/nedc_eeg_eval",
                str(ref_list),
                str(hyp_list),
                "-o", str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"NEDC failed: {result.stderr}")

            parser = UnifiedOutputParser()
            alpha_results = parser.parse_summary(
                (output_path / "summary.txt").read_text(),
                output_path
            )

        # Test parity with mismatched labels
        for algo in ["dp", "epoch", "overlap", "taes"]:
            parity_report = orchestrator.evaluate(
                algorithm=algo,
                ref_file=str(ref_file),
                hyp_file=str(hyp_file),
                alpha_result=alpha_results
            )

            # Should still achieve parity (both should handle mismatches the same way)
            assert parity_report.parity_passed, (
                f"Mismatched label parity failed for {algo}:\n"
                f"Report: {parity_report.parity_report}"
            )