from __future__ import annotations

import asyncio
import logging
import os
import pathlib
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import evaluation, health, websocket
from .middleware.error_handler import error_handler_middleware
from .middleware.rate_limit import rate_limit_middleware
from .services.job_manager import job_manager
from .services.processor import process_evaluation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle."""
    # Ensure NEDC env is available for orchestrator construction
    nedc_root = os.environ.get("NEDC_NFC")
    if not nedc_root:
        # Default to repo path for tests/dev
        default_root = pathlib.Path("nedc_eeg_eval/v6.0.0").resolve()
        os.environ["NEDC_NFC"] = str(default_root)
        # Ensure Alpha PYTHONPATH for imports
        lib_path = str(default_root / "lib")
        if os.environ.get("PYTHONPATH"):
            os.environ["PYTHONPATH"] = f"{lib_path}:{os.environ['PYTHONPATH']}"
        else:
            os.environ["PYTHONPATH"] = lib_path

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(evaluation.router, prefix="/api/v1", tags=["evaluation"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


# Optional: OpenAPI customization hook
try:
    from .docs import custom_openapi

    app.openapi = lambda: custom_openapi(app)  # type: ignore[method-assign]
except Exception:  # pragma: no cover - docs customization optional in tests
    pass
