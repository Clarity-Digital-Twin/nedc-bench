from __future__ import annotations

import logging
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class NEDCAPIException(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except NEDCAPIException as exc:
        logger.warning("API error: %s - %s", exc.error_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "detail": exc.detail,
                "request_id": request.headers.get("X-Request-ID"),
            },
        )
    except Exception as exc:  # pragma: no cover - unexpected
        logger.error("Unexpected error: %s\n%s", exc, traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "detail": "An unexpected error occurred",
                "request_id": request.headers.get("X-Request-ID"),
            },
        )
