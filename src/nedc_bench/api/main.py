from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import pathlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import evaluation, health, metrics as metrics_endpoint, websocket
from .middleware.error_handler import error_handler_middleware
from .middleware.rate_limit import rate_limit_middleware
from .services.job_manager import job_manager
from .services.processor import process_evaluation

# Configure logging (respect LOG_LEVEL if set)
level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
level = getattr(logging, level_name, logging.INFO)
logging.basicConfig(level=level)
logger = logging.getLogger(__name__)


def _cleanup_orphaned_temp_files() -> int:
    """Clean up orphaned temp files from previous crashes.

    Returns the number of files removed.
    """
    tmp_dir = pathlib.Path("/tmp")
    orphaned_patterns = [
        "*_ref.csv_bi",
        "*_hyp.csv_bi",
    ]
    removed_count = 0
    for pattern in orphaned_patterns:
        for filepath in tmp_dir.glob(pattern):
            try:
                filepath.unlink()
                removed_count += 1
                logger.debug("Removed orphaned temp file: %s", filepath)
            except OSError as exc:  # noqa: PERF203
                logger.warning("Failed to remove orphaned file %s: %s", filepath, exc)

    if removed_count > 0:
        logger.info("Cleaned up %d orphaned temp files from previous sessions", removed_count)

    return removed_count


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle."""
    # Clean up orphaned temp files from previous crashes (crash-resistant)
    _cleanup_orphaned_temp_files()

    # Check if NEDC_NFC is set (optional - only needed for dual/alpha pipelines)
    nedc_root = os.environ.get("NEDC_NFC")
    if nedc_root:
        logger.info("NEDC_NFC set to: %s (dual/alpha pipelines available)", nedc_root)
    else:
        # Try to auto-detect in dev/test environments
        default_root = pathlib.Path("nedc_eeg_eval/v6.0.0").resolve()
        if default_root.exists():
            os.environ["NEDC_NFC"] = str(default_root)
            lib_path = str(default_root / "lib")
            if os.environ.get("PYTHONPATH"):
                os.environ["PYTHONPATH"] = f"{lib_path}:{os.environ['PYTHONPATH']}"
            else:
                os.environ["PYTHONPATH"] = lib_path
            logger.info(
                "NEDC_NFC auto-detected at: %s (dual/alpha pipelines available)", default_root
            )
        else:
            logger.warning(
                "NEDC_NFC not set and legacy assets not found. "
                "Beta pipeline available, but dual/alpha pipelines will fail. "
                "Set NEDC_NFC environment variable to enable dual/alpha pipelines."
            )

    logger.info("Starting NEDC-BENCH API")
    # Start the job worker task
    worker_task = asyncio.create_task(job_manager.run_worker(process_evaluation))
    logger.info("Job worker task started")

    try:
        yield
    finally:
        logger.info("Shutting down NEDC-BENCH API")
        await job_manager.shutdown()
        worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker_task


app = FastAPI(
    title="NEDC-BENCH API",
    description="Dual-pipeline EEG evaluation benchmarking platform",
    version="1.0.0",
    lifespan=lifespan,
)


# Global middleware
app.middleware("http")(error_handler_middleware)
app.middleware("http")(rate_limit_middleware)

# CORS Configuration - customize via CORS_ALLOWED_ORIGINS environment variable
# Default to localhost for development; use comma-separated list for production
cors_origins_str = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000"
)
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(evaluation.router, prefix="/api/v1", tags=["evaluation"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(metrics_endpoint.router, tags=["metrics"])  # /metrics


# Optional: OpenAPI customization hook
try:
    from .docs import custom_openapi

    app.openapi = lambda: custom_openapi(app)  # type: ignore[method-assign]
    logger.debug("OpenAPI customization loaded successfully")
except ImportError:  # pragma: no cover - docs module may not exist in test environments
    logger.debug("OpenAPI customization module not found, using default OpenAPI schema")
except Exception as exc:  # pragma: no cover - catch other unexpected errors
    logger.warning(
        "Failed to load OpenAPI customization: %s. Using default OpenAPI schema. "
        "This may indicate a broken docs module.",
        exc,
        exc_info=True,
    )
