from __future__ import annotations

from fastapi import APIRouter, Response

try:  # pragma: no cover - allow running without prometheus_client installed
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest  # type: ignore
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    def generate_latest() -> bytes:  # type: ignore
        return b""

router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:  # pragma: no cover - trivial I/O endpoint
    """Expose Prometheus metrics in text format."""
    data = generate_latest()
    # If fallback is used, this will return empty body with text/plain
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
