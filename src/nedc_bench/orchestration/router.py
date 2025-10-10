"""Orchestrator router - selects correct orchestrator based on pipeline type.

This router pattern decouples Beta from Alpha:
- Beta requests → BetaPipelineOrchestrator (no NEDC_NFC needed)
- Dual/Alpha requests → DualPipelineOrchestrator (lazy-loads Alpha wrapper)

This enables pure-beta deployments without legacy 1GB+ assets.
"""

from __future__ import annotations

import os

from nedc_bench.orchestration.beta_orchestrator import BetaPipelineOrchestrator
from nedc_bench.orchestration.dual_pipeline import DualPipelineOrchestrator


class OrchestratorRouter:
    """Route to correct orchestrator based on pipeline type."""

    def __init__(self) -> None:
        """Initialize router with lazy dual-orchestrator loading."""
        self._dual_orch: DualPipelineOrchestrator | None = None
        self.beta_orch = BetaPipelineOrchestrator()  # Always available, no NEDC_NFC needed

    @property
    def dual_orch(self) -> DualPipelineOrchestrator:
        """Lazy-load dual orchestrator (requires NEDC_NFC environment variable).

        Raises:
            RuntimeError: If NEDC_NFC not set when dual/alpha pipeline requested
        """
        if self._dual_orch is None:
            if "NEDC_NFC" not in os.environ:
                raise RuntimeError(
                    "NEDC_NFC environment variable required for dual/alpha pipelines. "
                    "Use pipeline='beta' for NEDC-independent execution."
                )
            self._dual_orch = DualPipelineOrchestrator()

        return self._dual_orch

    def get_orchestrator(
        self, pipeline: str
    ) -> BetaPipelineOrchestrator | DualPipelineOrchestrator:
        """Get appropriate orchestrator for pipeline type.

        Args:
            pipeline: Pipeline type ('beta', 'dual', or 'alpha')

        Returns:
            BetaPipelineOrchestrator for beta, DualPipelineOrchestrator for dual/alpha

        Raises:
            ValueError: If pipeline type is unknown
            RuntimeError: If NEDC_NFC not set for dual/alpha pipeline
        """
        if pipeline == "beta":
            return self.beta_orch
        elif pipeline in {"dual", "alpha"}:
            return self.dual_orch  # Lazy-loaded, will check NEDC_NFC
        else:
            raise ValueError(f"Unknown pipeline: {pipeline}")
