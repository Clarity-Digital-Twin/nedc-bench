from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="NEDC-BENCH API",
        version="1.0.0",
        description=(
            "Dual-pipeline EEG evaluation platform with FastAPI and real-time updates.\n\n"
            "Features: Alpha+Beta pipelines, 5 algorithms, parity validation, WebSockets."
        ),
        routes=app.routes,
    )

    openapi_schema["tags"] = [
        {"name": "health", "description": "Health check endpoints"},
        {"name": "evaluation", "description": "EEG evaluation endpoints"},
        {"name": "websocket", "description": "Real-time progress updates"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
