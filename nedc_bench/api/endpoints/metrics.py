from __future__ import annotations

import os

from fastapi import APIRouter, Response

try:  # pragma: no cover - allow running without prometheus_client installed
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        generate_latest,
        multiprocess,  # type: ignore[attr-defined]
    )
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    def generate_latest() -> bytes:  # type: ignore
        return b""


router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:  # pragma: no cover - trivial I/O endpoint
    """Expose Prometheus metrics in text format."""
    data: bytes
    # Support Prometheus multiprocess mode if configured
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        try:
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)  # type: ignore[attr-defined]
            data = generate_latest(registry)
        except Exception:
            # Fallback to default registry if multiprocess not available
            data = generate_latest()
    else:
        data = generate_latest()
    # If fallback is used, this will return empty body with text/plain
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
