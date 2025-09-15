from __future__ import annotations

from fastapi import APIRouter, HTTPException

from nedc_bench.api.services.cache import redis_cache
from nedc_bench.api.services.job_manager import job_manager

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness probe that validates internal worker and Redis connectivity."""
    # Check background worker loop is active
    if not job_manager.is_running():
        raise HTTPException(status_code=503, detail="Worker not running")

    # Check Redis connectivity (optional in dev)
    ok = await redis_cache.ping()
    if not ok:
        raise HTTPException(status_code=503, detail="Redis not reachable")

    return {"status": "ready"}
