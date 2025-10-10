"""Pure-beta orchestrator with NO Alpha dependencies.

This orchestrator runs ONLY the beta pipeline, with zero coupling to legacy NEDC assets.
It does NOT require NEDC_NFC environment variable and can run in lightweight containers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nedc_bench.orchestration.dual_pipeline import BetaPipeline


class BetaPipelineOrchestrator:
    """Pure-beta orchestrator - runs only beta pipeline, no Alpha coupling."""

    def __init__(self) -> None:
        """Initialize beta-only orchestrator.

        No NEDC_NFC required - this is a fully independent implementation.
        """
        self.beta = BetaPipeline()

    def evaluate(self, ref_file: Path, hyp_file: Path, algorithm: str) -> Any:
        """Run beta-only evaluation.

        Args:
            ref_file: Reference annotation file path
            hyp_file: Hypothesis annotation file path
            algorithm: Algorithm to run (taes, dp, epoch, overlap, ira, any)

        Returns:
            Algorithm-specific result dict

        Raises:
            ValueError: If algorithm is unknown
        """
        if algorithm == "taes":
            return self.beta.evaluate_taes(ref_file, hyp_file)
        elif algorithm == "dp":
            return self.beta.evaluate_dp(ref_file, hyp_file)
        elif algorithm == "epoch":
            return self.beta.evaluate_epoch(ref_file, hyp_file)
        elif algorithm == "overlap":
            return self.beta.evaluate_overlap(ref_file, hyp_file)
        elif algorithm == "ira":
            return self.beta.evaluate_ira(ref_file, hyp_file)
        elif algorithm == "any":
            return self.beta.evaluate_any(ref_file, hyp_file)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
