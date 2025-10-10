from __future__ import annotations

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast

from nedc_bench import PACKAGE_VERSION
from nedc_bench.api.services.cache import RedisCache, redis_cache
from nedc_bench.monitoring.metrics import (
    evaluation_counter,
    evaluation_duration,
    parity_failures,
    track_evaluation_dynamic,
)
from nedc_bench.orchestration.router import OrchestratorRouter

logger = logging.getLogger(__name__)


class AsyncOrchestrator:
    """Async wrapper around orchestration layer using smart routing.

    Routes to appropriate orchestrator based on pipeline type:
    - Beta pipeline → BetaPipelineOrchestrator (no NEDC_NFC needed)
    - Dual/Alpha pipeline → DualPipelineOrchestrator (lazy-loads Alpha wrapper)
    """

    def __init__(self, max_workers: int = 4):
        # Use router pattern - no forced NEDC_NFC setup (only set when needed)
        self.router = OrchestratorRouter()
        env_workers = int(os.environ.get("MAX_WORKERS", str(max_workers)))
        self.executor = ThreadPoolExecutor(max_workers=env_workers)
        self.cache: RedisCache = redis_cache

    async def evaluate(
        self,
        ref_file: str,
        hyp_file: str,
        algorithm: str = "taes",
        pipeline: str = "dual",
    ) -> dict[str, Any]:
        """Run a single evaluation asynchronously with caching and metrics."""

        loop = asyncio.get_event_loop()
        algorithm = algorithm.lower()
        pipeline = pipeline.lower()
        labels = {"algorithm": algorithm, "pipeline": pipeline}

        # Precompute cache key (best-effort). Use classmethod to avoid tests mocking
        # the cache instance and accidentally returning an un-awaited coroutine.
        key: str | None = None
        try:
            ref_bytes = Path(ref_file).read_bytes()
            hyp_bytes = Path(hyp_file).read_bytes()
            key = RedisCache.make_key(ref_bytes, hyp_bytes, algorithm, pipeline, PACKAGE_VERSION)
        except Exception:  # pragma: no cover - IO issues treated as cache miss
            key = None

        # Cache lookup for dual/beta pipelines
        if pipeline in {"dual", "beta"} and key is not None:
            cached = await self.cache.get_json(key)
            if cached is not None:
                evaluation_counter.labels(**labels, status="success").inc()
                evaluation_duration.labels(**labels).observe(0.0)
                return cast(dict[str, Any], cached)

        async def _run() -> dict[str, Any]:
            if pipeline == "dual":
                # Use router to get dual orchestrator (lazy-loads Alpha if needed)
                orchestrator = self.router.get_orchestrator("dual")
                result = await loop.run_in_executor(
                    self.executor,
                    orchestrator.evaluate,
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

                out = {
                    "alpha_result": result.alpha_result,
                    "beta_result": beta_dict,
                    "parity_passed": result.parity_passed,
                    "parity_report": result.parity_report.to_dict()
                    if result.parity_report
                    else None,
                    "alpha_time": result.execution_time_alpha,
                    "beta_time": result.execution_time_beta,
                    "speedup": result.speedup,
                }
                if not result.parity_passed:
                    parity_failures.labels(algorithm=algorithm).inc()
                return out

            if pipeline == "alpha":
                # Use router to get dual orchestrator (lazy-loads Alpha if needed)
                orchestrator = self.router.get_orchestrator("alpha")
                alpha_res = await loop.run_in_executor(
                    self.executor,
                    orchestrator.alpha_wrapper.evaluate,
                    ref_file,
                    hyp_file,
                )
                return {"alpha_result": alpha_res}

            if pipeline == "beta":
                # Use router to get beta orchestrator (NO NEDC_NFC needed!)
                orchestrator = self.router.get_orchestrator("beta")

                def _run_beta() -> Any:
                    r = Path(ref_file)
                    h = Path(hyp_file)
                    return orchestrator.evaluate(r, h, algorithm)

                beta_res = await loop.run_in_executor(self.executor, _run_beta)
                # Convert dataclass to dict
                return {
                    "beta_result": beta_res.__dict__ if hasattr(beta_res, "__dict__") else beta_res
                }

            raise ValueError(f"Unsupported pipeline: {pipeline}")

        # Wrap with metrics
        result = await track_evaluation_dynamic(
            algorithm,
            pipeline,
            _run,
        )

        # Store in cache for dual/beta
        if pipeline in {"dual", "beta"} and key is not None:
            await self.cache.set_json(key, result)
        return cast(dict[str, Any], result)

    async def evaluate_batch(
        self,
        file_pairs: list[tuple[str, str]],
        algorithm: str = "taes",
        pipeline: str = "dual",
    ) -> list[dict[str, Any]]:
        """Process multiple file pairs concurrently."""

        tasks = [self.evaluate(ref, hyp, algorithm, pipeline) for ref, hyp in file_pairs]
        return await asyncio.gather(*tasks)
