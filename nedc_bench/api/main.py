from __future__ import annotations

import logging
import os
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nedc_bench.orchestration.dual_pipeline import DualPipelineOrchestrator

from .endpoints import evaluation, health, websocket
from .middleware.error_handler import error_handler_middleware
from .middleware.rate_limit import rate_limit_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


orchestrator: DualPipelineOrchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global orchestrator

    # Ensure NEDC env is available for orchestrator construction
    nedc_root = os.environ.get("NEDC_NFC")
    if not nedc_root:
        # Default to repo path for tests/dev
        default_root = pathlib.Path("nedc_eeg_eval/v6.0.0").resolve()
        os.environ["NEDC_NFC"] = default_root
        # Ensure Alpha PYTHONPATH for imports
        os.environ.setdefault("PYTHONPATH", os.path.join(default_root, "lib"))

    logger.info("Starting NEDC-BENCH API")
    orchestrator = DualPipelineOrchestrator()
    try:
        yield
    finally:
        logger.info("Shutting down NEDC-BENCH API")


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

    app.openapi = lambda: custom_openapi(app)  # type: ignore[assignment]
except Exception:  # pragma: no cover - docs customization optional in tests
    pass
