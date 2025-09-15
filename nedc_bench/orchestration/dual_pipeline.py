"""
Dual pipeline orchestrator for Alpha-Beta comparison
Runs both pipelines and validates parity
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from alpha.wrapper import NEDCAlphaWrapper
from nedc_bench.algorithms.dp_alignment import DPAligner
from nedc_bench.algorithms.epoch import EpochScorer
from nedc_bench.algorithms.ira import IRAScorer
from nedc_bench.algorithms.overlap import OverlapScorer
from nedc_bench.algorithms.taes import TAESScorer
from nedc_bench.models.annotations import AnnotationFile
from nedc_bench.utils.params import load_nedc_params, map_event_label
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

    def _map_events(self, events: list, label_map: dict[str, str]) -> list:
        for ev in events:
            ev.label = map_event_label(ev.label, label_map)
        return events

    def _expand_with_null(self, events: list, duration: float, null_label: str) -> list:
        """Expand sparse events by inserting null segments to cover full duration."""
        if not events:
            return []
        # Ensure sorted
        evs = sorted(events, key=lambda e: e.start_time)
        expanded: list = []
        cur = 0.0
        for ev in evs:
            if ev.start_time > cur:
                # insert null
                expanded.append(
                    type(ev)(
                        channel=ev.channel,
                        start_time=cur,
                        stop_time=ev.start_time,
                        label=null_label,
                        confidence=1.0,
                    )
                )
            expanded.append(ev)
            cur = ev.stop_time
        if cur < duration:
            expanded.append(
                type(evs[0])(
                    channel=evs[0].channel,
                    start_time=cur,
                    stop_time=duration,
                    label=null_label,
                    confidence=1.0,
                )
            )
        return expanded

    def evaluate_dp(self, ref_file: Path, hyp_file: Path) -> Any:
        params = load_nedc_params()
        ref_ann = AnnotationFile.from_csv_bi(ref_file)
        hyp_ann = AnnotationFile.from_csv_bi(hyp_file)
        # Expand both annotations to include background segments
        ref_events = self._expand_with_null(ref_ann.events, ref_ann.duration, params.null_class)
        hyp_events = self._expand_with_null(hyp_ann.events, hyp_ann.duration, params.null_class)
        # Apply label mapping
        self._map_events(ref_events, params.label_map)
        self._map_events(hyp_events, params.label_map)
        ref = [e.label for e in ref_events]
        hyp = [e.label for e in hyp_events]
        return DPAligner().align(ref, hyp)

    def evaluate_epoch(self, ref_file: Path, hyp_file: Path) -> Any:
        params = load_nedc_params()
        ref_ann = AnnotationFile.from_csv_bi(ref_file)
        hyp_ann = AnnotationFile.from_csv_bi(hyp_file)
        ref_events = self._expand_with_null(ref_ann.events, ref_ann.duration, params.null_class)
        hyp_events = self._expand_with_null(hyp_ann.events, hyp_ann.duration, params.null_class)
        self._map_events(ref_events, params.label_map)
        self._map_events(hyp_events, params.label_map)
        scorer = EpochScorer(epoch_duration=params.epoch_duration, null_class=params.null_class)
        return scorer.score(ref_events, hyp_events, ref_ann.duration)

    def evaluate_overlap(self, ref_file: Path, hyp_file: Path) -> Any:
        params = load_nedc_params()
        ref_ann = AnnotationFile.from_csv_bi(ref_file)
        hyp_ann = AnnotationFile.from_csv_bi(hyp_file)
        ref_events = self._expand_with_null(ref_ann.events, ref_ann.duration, params.null_class)
        hyp_events = self._expand_with_null(hyp_ann.events, hyp_ann.duration, params.null_class)
        self._map_events(ref_events, params.label_map)
        self._map_events(hyp_events, params.label_map)
        scorer = OverlapScorer()
        return scorer.score(ref_events, hyp_events)

    def evaluate_ira(self, ref_file: Path, hyp_file: Path) -> Any:
        params = load_nedc_params()
        ref_ann = AnnotationFile.from_csv_bi(ref_file)
        hyp_ann = AnnotationFile.from_csv_bi(hyp_file)
        ref_events = self._expand_with_null(ref_ann.events, ref_ann.duration, params.null_class)
        hyp_events = self._expand_with_null(hyp_ann.events, hyp_ann.duration, params.null_class)
        self._map_events(ref_events, params.label_map)
        self._map_events(hyp_events, params.label_map)
        return IRAScorer().score(
            ref_events,
            hyp_events,
            epoch_duration=params.epoch_duration,
            file_duration=ref_ann.duration,
            null_class=params.null_class,
        )


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

    def evaluate(
        self,
        ref_file: str,
        hyp_file: str,
        algorithm: str = "taes",
        alpha_result: dict[str, Any] | None = None,
    ) -> DualPipelineResult:
        """
        Run both pipelines on single file pair

        Args:
            ref_file: Path to reference CSV_BI file
            hyp_file: Path to hypothesis CSV_BI file
            algorithm: Algorithm to run (currently only 'taes')
            alpha_result: Pre-computed Alpha results (optional, for testing)

        Returns:
            DualPipelineResult with comparison
        """
        # Run Alpha pipeline if not provided
        if alpha_result is None:
            start_alpha = time.perf_counter()
            alpha_result = self.alpha_wrapper.evaluate(ref_file, hyp_file)
            time_alpha = time.perf_counter() - start_alpha
        else:
            time_alpha = 0.0

        # Run Beta pipeline
        start_beta = time.perf_counter()
        if algorithm == "taes":
            beta_result = self.beta_pipeline.evaluate_taes(Path(ref_file), Path(hyp_file))
        elif algorithm == "dp":
            beta_result = self.beta_pipeline.evaluate_dp(Path(ref_file), Path(hyp_file))
        elif algorithm == "epoch":
            beta_result = self.beta_pipeline.evaluate_epoch(Path(ref_file), Path(hyp_file))
        elif algorithm == "overlap":
            beta_result = self.beta_pipeline.evaluate_overlap(Path(ref_file), Path(hyp_file))
        elif algorithm == "ira":
            beta_result = self.beta_pipeline.evaluate_ira(Path(ref_file), Path(hyp_file))
        else:
            raise ValueError(f"Algorithm {algorithm} not yet implemented in Beta")
        time_beta = time.perf_counter() - start_beta

        # Validate parity
        if algorithm == "taes":
            parity_report = self.validator.compare_taes(alpha_result["taes"], beta_result)
        elif algorithm == "dp":
            parity_report = self.validator.compare_dp(alpha_result["dp_alignment"], beta_result)
        elif algorithm == "epoch":
            parity_report = self.validator.compare_epoch(alpha_result["epoch"], beta_result)
        elif algorithm == "overlap":
            parity_report = self.validator.compare_overlap(alpha_result["overlap"], beta_result)
        elif algorithm == "ira":
            parity_report = self.validator.compare_ira(alpha_result["ira"], beta_result)
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

        # Expand $NEDC_NFC paths
        nedc_nfc = os.environ.get("NEDC_NFC", str(Path("nedc_eeg_eval/v6.0.0").absolute()))
        ref_files = [f.replace("$NEDC_NFC", nedc_nfc) for f in ref_files]
        hyp_files = [f.replace("$NEDC_NFC", nedc_nfc) for f in hyp_files]

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
