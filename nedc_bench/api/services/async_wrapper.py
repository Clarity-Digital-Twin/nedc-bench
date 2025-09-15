from __future__ import annotations

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from nedc_bench.orchestration.dual_pipeline import DualPipelineOrchestrator

logger = logging.getLogger(__name__)


class AsyncOrchestrator:
    """Async wrapper around DualPipelineOrchestrator using a thread pool."""

    def __init__(self, max_workers: int = 4):
        # Ensure NEDC environment is available (tests may import before app startup)
        if "NEDC_NFC" not in os.environ:
            default_root = Path("nedc_eeg_eval/v6.0.0").absolute()
            os.environ["NEDC_NFC"] = str(default_root)
            os.environ.setdefault("PYTHONPATH", str(default_root / "lib"))
        self.orchestrator = DualPipelineOrchestrator()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def evaluate(
        self,
        ref_file: str,
        hyp_file: str,
        algorithm: str = "taes",
        pipeline: str = "dual",
    ) -> dict[str, Any]:
        """Run a single evaluation asynchronously."""

        loop = asyncio.get_event_loop()

        if pipeline == "dual":
            result = await loop.run_in_executor(
                self.executor,
                self.orchestrator.evaluate,
                ref_file,
                hyp_file,
                algorithm,
                None,
            )

            # Convert dataclasses to dicts
            beta_dict = (
                result.beta_result.__dict__
                if hasattr(result.beta_result, "__dict__")
                else result.beta_result
            )

            return {
                "alpha_result": result.alpha_result,
                "beta_result": beta_dict,
                "parity_passed": result.parity_passed,
                "parity_report": result.parity_report.to_dict() if result.parity_report else None,
                "alpha_time": result.execution_time_alpha,
                "beta_time": result.execution_time_beta,
                "speedup": result.speedup,
            }

        if pipeline == "alpha":
            alpha_res = await loop.run_in_executor(
                self.executor,
                self.orchestrator.alpha_wrapper.evaluate,
                ref_file,
                hyp_file,
            )
            return {"alpha_result": alpha_res}

        if pipeline == "beta":
            # Dispatch to specific Beta algorithm
            def _run_beta() -> Any:
                r = Path(ref_file)
                h = Path(hyp_file)
                if algorithm == "taes":
                    return self.orchestrator.beta_pipeline.evaluate_taes(r, h)
                if algorithm == "dp":
                    return self.orchestrator.beta_pipeline.evaluate_dp(r, h)
                if algorithm == "epoch":
                    return self.orchestrator.beta_pipeline.evaluate_epoch(r, h)
                if algorithm == "overlap":
                    return self.orchestrator.beta_pipeline.evaluate_overlap(r, h)
                if algorithm == "ira":
                    return self.orchestrator.beta_pipeline.evaluate_ira(r, h)
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            beta_res = await loop.run_in_executor(self.executor, _run_beta)
            # Convert dataclass to dict
            return {"beta_result": beta_res.__dict__ if hasattr(beta_res, "__dict__") else beta_res}

        raise ValueError(f"Unsupported pipeline: {pipeline}")

    async def evaluate_batch(
        self,
        file_pairs: list[tuple[str, str]],
        algorithm: str = "taes",
        pipeline: str = "dual",
    ) -> list[dict[str, Any]]:
        """Process multiple file pairs concurrently."""

        tasks = [self.evaluate(ref, hyp, algorithm, pipeline) for ref, hyp in file_pairs]
        return await asyncio.gather(*tasks)
