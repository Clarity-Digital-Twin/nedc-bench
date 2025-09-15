from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from .async_wrapper import AsyncOrchestrator
from .job_manager import job_manager
from .progress_tracker import progress_tracker
from .websocket_manager import broadcast_progress

logger = logging.getLogger(__name__)

async_orchestrator = AsyncOrchestrator()


async def process_evaluation(job_id: str) -> None:
    """Process a single evaluation job and broadcast progress."""

    job = await job_manager.get_job(job_id)
    if not job:
        logger.error("Job %s not found", job_id)
        return

    await job_manager.update_job(job_id, {"status": "processing", "started_at": datetime.utcnow()})
    await broadcast_progress(
        job_id, {"type": "status", "status": "processing", "message": "Starting evaluation"}
    )

    algorithms = job["algorithms"]
    if any(a == "all" for a in algorithms):
        algorithms = ["dp", "epoch", "overlap", "ira", "taes"]

    await progress_tracker.init_job(job_id, total_algorithms=len(algorithms))

    results: dict[str, dict[str, Any]] = {}
    for algo in algorithms:
        await progress_tracker.update_algorithm(job_id, algo, job["pipeline"], "started")
        await broadcast_progress(
            job_id, {"type": "algorithm", "algorithm": algo, "status": "running"}
        )

        try:
            res = await async_orchestrator.evaluate(
                job["ref_path"],
                job["hyp_path"],
                algo,
                job["pipeline"],
            )
            results[algo] = res
            await broadcast_progress(
                job_id,
                {"type": "algorithm", "algorithm": algo, "status": "completed", "result": res},
            )
        except Exception as exc:
            logger.exception("Algorithm %s failed on job %s: %s", algo, job_id, exc)
            await job_manager.update_job(
                job_id,
                {
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "error": str(exc),
                },
            )
            await broadcast_progress(
                job_id, {"type": "status", "status": "failed", "error": str(exc)}
            )
            return
        finally:
            await progress_tracker.update_algorithm(job_id, algo, job["pipeline"], "completed")

    # Update and broadcast completion
    await job_manager.update_job(
        job_id,
        {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "results": results,
        },
    )
    await broadcast_progress(
        job_id,
        {"type": "status", "status": "completed", "message": "Evaluation completed successfully"},
    )
