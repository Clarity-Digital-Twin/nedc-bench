from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, cast

from fastapi import APIRouter, Response

CONTENT_TYPE_LATEST: str
CollectorRegistry: Any
generate_latest: Callable[..., bytes]
multiprocess_mod: Any | None

try:  # pragma: no cover - allow running without prometheus_client installed
    import prometheus_client.multiprocess as _multiprocess
    from prometheus_client import (
        CONTENT_TYPE_LATEST as _CTL,
        CollectorRegistry as _CollectorRegistry,
        generate_latest as _gen_latest,
    )

    CONTENT_TYPE_LATEST = _CTL
    CollectorRegistry = _CollectorRegistry
    generate_latest = _gen_latest
    multiprocess_mod = _multiprocess
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    def _fallback_generate_latest(*_args: Any, **_kwargs: Any) -> bytes:
        return b""

    class _FallbackRegistry:  # minimal placeholder for typing
        pass

    CollectorRegistry = _FallbackRegistry
    generate_latest = _fallback_generate_latest
    multiprocess_mod = None


router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:  # pragma: no cover - trivial I/O endpoint
    """Expose Prometheus metrics in text format."""
    data: bytes
    # Support Prometheus multiprocess mode if configured
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ and multiprocess_mod is not None:
        try:
            registry = CollectorRegistry()
            cast(Any, multiprocess_mod).MultiProcessCollector(registry)
            data = generate_latest(registry)
        except Exception:
            # Fallback to default registry if multiprocess not available
            data = generate_latest()
    else:
        data = generate_latest()
    # If fallback is used, this will return empty body with text/plain
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
