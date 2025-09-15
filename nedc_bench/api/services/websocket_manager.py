from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage WebSocket connections and last-event replay per job id."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._last_event: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[job_id].add(websocket)
            last = self._last_event.get(job_id)
        logger.info("WebSocket connected for job %s", job_id)
        # Replay last event if available so late subscribers don't miss updates
        if last is not None:
            try:
                await websocket.send_json(last)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("WebSocket replay failed for %s: %s", job_id, exc)

    async def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(job_id)
            if conns and websocket in conns:
                conns.discard(websocket)
                if not conns:
                    self._connections.pop(job_id, None)
        logger.info("WebSocket disconnected for job %s", job_id)

    async def broadcast(self, job_id: str, message: dict[str, Any]) -> None:
        async with self._lock:
            self._last_event[job_id] = message
            conns = list(self._connections.get(job_id, set()))

        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception as exc:  # pragma: no cover (network error)
                logger.warning("WebSocket send failed: %s", exc)
                dead.append(ws)

        # Clean up any dead connections
        for ws in dead:
            await self.disconnect(job_id, ws)

    def get_last_event(self, job_id: str) -> dict[str, Any] | None:
        return self._last_event.get(job_id)


ws_manager = WebSocketManager()


async def broadcast_progress(job_id: str, message: dict[str, Any]) -> None:
    await ws_manager.broadcast(job_id, message)
