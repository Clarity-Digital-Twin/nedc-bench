"""
Dual pipeline orchestrator for Alpha-Beta comparison
Runs both pipelines and validates parity
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha.wrapper import NEDCAlphaWrapper
from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.models.annotations import AnnotationFile
from nedc_bench.validation.parity import ParityValidator, ValidationReport


@dataclass
class DualPipelineResult:
    """Results from dual pipeline execution"""

    alpha_result: dict[str, Any]
    beta_result: Any  # Algorithm-specific result object
    parity_report: ValidationReport
    parity_passed: bool
    execution_time_alpha: float
    execution_time_beta: float

    @property
    def speedup(self) -> float:
        """Beta speedup over Alpha"""
        if self.execution_time_beta > 0:
            return self.execution_time_alpha / self.execution_time_beta
        return 0.0


class BetaPipeline:
    """Beta pipeline runner"""

    def evaluate_taes(self, ref_file: Path, hyp_file: Path) -> Any:  # noqa: PLR6301
        """Run TAES evaluation on single file pair"""
        ref_annotations = AnnotationFile.from_csv_bi(ref_file)
        hyp_annotations = AnnotationFile.from_csv_bi(hyp_file)

        scorer = TAESScorer()
        return scorer.score(ref_annotations.events, hyp_annotations.events)


class DualPipelineOrchestrator:
    """Orchestrate execution of both pipelines"""

    def __init__(self, tolerance: float = 1e-10):
        """
        Initialize orchestrator

        Args:
            tolerance: Numerical tolerance for parity validation
        """
        self.alpha_wrapper = NEDCAlphaWrapper(nedc_root=Path(os.environ["NEDC_NFC"]))
        self.beta_pipeline = BetaPipeline()
        self.validator = ParityValidator(tolerance=tolerance)

    def evaluate(self, ref_file: str, hyp_file: str, algorithm: str = "taes") -> DualPipelineResult:
        """
        Run both pipelines on single file pair

        Args:
            ref_file: Path to reference CSV_BI file
            hyp_file: Path to hypothesis CSV_BI file
            algorithm: Algorithm to run (currently only 'taes')

        Returns:
            DualPipelineResult with comparison
        """
        # Run Alpha pipeline
        start_alpha = time.perf_counter()
        alpha_result = self.alpha_wrapper.evaluate(ref_file, hyp_file)
        time_alpha = time.perf_counter() - start_alpha

        # Run Beta pipeline
        start_beta = time.perf_counter()
        if algorithm == "taes":
            beta_result = self.beta_pipeline.evaluate_taes(Path(ref_file), Path(hyp_file))
        else:
            raise ValueError(f"Algorithm {algorithm} not yet implemented in Beta")
        time_beta = time.perf_counter() - start_beta

        # Validate parity
        if algorithm == "taes":
            parity_report = self.validator.compare_taes(alpha_result["taes"], beta_result)
        else:
            raise ValueError(f"Parity validation for {algorithm} not implemented")

        return DualPipelineResult(
            alpha_result=alpha_result,
            beta_result=beta_result,
            parity_report=parity_report,
            parity_passed=parity_report.passed,
            execution_time_alpha=time_alpha,
            execution_time_beta=time_beta,
        )

    def evaluate_lists(
        self, ref_list: str, hyp_list: str, algorithm: str = "taes"
    ) -> dict[str, Any]:
        """
        Run both pipelines on list files

        Args:
            ref_list: Path to reference list file
            hyp_list: Path to hypothesis list file
            algorithm: Algorithm to run

        Returns:
            Dictionary with results for all file pairs
        """
        # Parse list files
        ref_files = []
        hyp_files = []

        with open(ref_list, encoding="utf-8") as f:  # noqa: PTH123
            ref_files = [line.strip() for line in f if line.strip()]

        with open(hyp_list, encoding="utf-8") as f:  # noqa: PTH123
            hyp_files = [line.strip() for line in f if line.strip()]

        assert len(ref_files) == len(hyp_files), "List files must have same length"

        # Process each pair
        results = {"file_results": [], "all_passed": True, "total_files": len(ref_files)}

        for ref_file, hyp_file in zip(ref_files, hyp_files):
            result = self.evaluate(ref_file, hyp_file, algorithm)
            results["file_results"].append({
                "ref": ref_file,
                "hyp": hyp_file,
                "parity_passed": result.parity_passed,
                "speedup": result.speedup,
            })

            if not result.parity_passed:
                results["all_passed"] = False
                print(f"❌ Parity failed for {Path(ref_file).name}")
                print(result.parity_report)

        results["parity_passed"] = results["all_passed"]
        return results
