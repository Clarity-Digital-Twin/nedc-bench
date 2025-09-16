from __future__ import annotations

from datetime import datetime
from typing import Any


class ProgressTracker:
    """Track high-level progress for evaluation jobs."""

    def __init__(self) -> None:
        self.progress: dict[str, dict[str, Any]] = {}

    async def init_job(self, job_id: str, total_algorithms: int) -> None:
        self.progress[job_id] = {
            "total_algorithms": total_algorithms,
            "completed_algorithms": 0,
            "current_algorithm": None,
            "current_pipeline": None,
            "start_time": datetime.utcnow(),
            "algorithm_times": {},
        }

    async def update_algorithm(
        self, job_id: str, algorithm: str, pipeline: str, status: str
    ) -> None:
        if job_id not in self.progress:
            return
        p = self.progress[job_id]
        now = datetime.utcnow()
        if status == "started":
            p["current_algorithm"] = algorithm
            p["current_pipeline"] = pipeline
            p["algorithm_times"][algorithm] = {"start": now}
        elif status == "completed":
            if algorithm in p["algorithm_times"] and "start" in p["algorithm_times"][algorithm]:
                start = p["algorithm_times"][algorithm]["start"]
                p["algorithm_times"][algorithm]["end"] = now
                p["algorithm_times"][algorithm]["duration"] = (now - start).total_seconds()
            p["completed_algorithms"] += 1
            p["current_algorithm"] = None
            p["current_pipeline"] = None

    async def get_progress(self, job_id: str) -> dict[str, Any]:
        p = self.progress.get(job_id)
        if not p:
            return {}
        elapsed = (datetime.utcnow() - p["start_time"]).total_seconds()
        percent = (
            (p["completed_algorithms"] / p["total_algorithms"]) * 100
            if p["total_algorithms"]
            else 0.0
        )
        return {
            "percent_complete": percent,
            "current_algorithm": p["current_algorithm"],
            "current_pipeline": p["current_pipeline"],
            "completed": p["completed_algorithms"],
            "total": p["total_algorithms"],
            "elapsed_time": elapsed,
        }


progress_tracker = ProgressTracker()
