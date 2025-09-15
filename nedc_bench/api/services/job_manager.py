from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class JobManager:
    """In-memory job manager with a simple async queue."""

    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.lock = asyncio.Lock()

    async def add_job(self, job: dict[str, Any]) -> None:
        async with self.lock:
            self.jobs[job["id"]] = job
            await self.queue.put(job["id"])
            logger.info("Job %s added to queue", job["id"])

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)

    async def update_job(self, job_id: str, updates: dict[str, Any]) -> None:
        async with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].update(updates)
                logger.info("Job %s updated: %s", job_id, updates.get("status"))

    async def list_jobs(
        self,
        limit: int = 10,
        offset: int = 0,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        jobs = list(self.jobs.values())

        if status:
            jobs = [j for j in jobs if j.get("status") == status]

        jobs.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        return jobs[offset : offset + limit]

    async def get_next_job(self) -> str | None:
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    async def run_worker(self, processor) -> None:
        """Run the background worker to process jobs."""
        logger.info("Job worker started")
        self._running = True
        while self._running:
            try:
                job_id = await self.get_next_job()
                if job_id:
                    logger.info("Processing job %s", job_id)
                    await processor(job_id)
            except asyncio.CancelledError:
                logger.info("Job worker cancelled")
                break
            except Exception as exc:
                logger.exception("Worker error: %s", exc)
                await asyncio.sleep(1)  # Prevent tight loop on errors

    async def shutdown(self) -> None:
        """Shutdown the worker gracefully."""
        self._running = False


# Singleton instance
job_manager = JobManager()
