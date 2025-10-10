from __future__ import annotations

import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any, cast

from .dual_pipeline import DualPipelineOrchestrator

logger = logging.getLogger(__name__)


def _evaluate_pair(
    ref_file: str,
    hyp_file: str,
    algorithm: str,
    pipeline: str,
) -> dict[str, Any]:
    orch = DualPipelineOrchestrator()
    if pipeline == "dual":
        res = orch.evaluate(ref_file, hyp_file, algorithm)
        beta_dict = (
            res.beta_result.__dict__ if hasattr(res.beta_result, "__dict__") else res.beta_result
        )
        return {
            "alpha_result": res.alpha_result,
            "beta_result": beta_dict,
            "parity_passed": res.parity_passed,
            "parity_report": res.parity_report.to_dict() if res.parity_report else None,
            "alpha_time": res.execution_time_alpha,
            "beta_time": res.execution_time_beta,
            "speedup": res.speedup,
        }
    if pipeline == "beta":
        r = Path(ref_file)
        h = Path(hyp_file)
        if algorithm == "taes":
            beta = orch.beta_pipeline.evaluate_taes(r, h)
        elif algorithm == "dp":
            beta = orch.beta_pipeline.evaluate_dp(r, h)
        elif algorithm == "epoch":
            beta = orch.beta_pipeline.evaluate_epoch(r, h)
        elif algorithm == "overlap":
            beta = orch.beta_pipeline.evaluate_overlap(r, h)
        elif algorithm == "ira":
            beta = orch.beta_pipeline.evaluate_ira(r, h)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        return {"beta_result": beta.__dict__ if hasattr(beta, "__dict__") else beta}
    if pipeline == "alpha":
        return {"alpha_result": orch.alpha_wrapper.evaluate(ref_file, hyp_file)}
    raise ValueError(f"Unsupported pipeline: {pipeline}")


class ParallelEvaluator:
    """Evaluate multiple file pairs in parallel using processes for CPU-bound work."""

    def __init__(self, max_workers: int | None = None) -> None:
        self.max_workers = max_workers or int(os.environ.get("PARALLEL_WORKERS", str(cpu_count())))

    def evaluate_batch(
        self,
        file_pairs: list[tuple[str, str]],
        algorithm: str,
        pipeline: str = "dual",
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any] | None] = [None] * len(file_pairs)
        with ProcessPoolExecutor(max_workers=self.max_workers) as ex:
            futures = {
                ex.submit(_evaluate_pair, ref, hyp, algorithm, pipeline): idx
                for idx, (ref, hyp) in enumerate(file_pairs)
            }
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    results[idx] = fut.result()
                except Exception as exc:
                    ref, hyp = file_pairs[idx]
                    logger.error(
                        "Evaluation failed for file pair %d (%s, %s): %s",
                        idx,
                        ref,
                        hyp,
                        exc,
                        exc_info=True,
                    )
                    results[idx] = {
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                        "ref_file": ref,
                        "hyp_file": hyp,
                    }

        # Ensure no None values remain (defensive - should not happen if all futures complete)
        for idx, result in enumerate(results):
            if result is None:
                ref, hyp = file_pairs[idx]
                logger.error(
                    "Unexpected None result for file pair %d (%s, %s) - future did not complete",
                    idx,
                    ref,
                    hyp,
                )
                results[idx] = {
                    "error": "Evaluation did not complete",
                    "error_type": "UnexpectedNone",
                    "ref_file": ref,
                    "hyp_file": hyp,
                }

        # All None values replaced - safe to cast
        return cast(list[dict[str, Any]], results)
