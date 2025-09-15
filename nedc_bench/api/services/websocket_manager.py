from __future__ import annotations

import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage WebSocket connections by job id."""

    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.setdefault(job_id, []).append(websocket)
        logger.info("WebSocket connected for job %s", job_id)

    def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        conns = self.connections.get(job_id)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.connections.pop(job_id, None)
        logger.info("WebSocket disconnected for job %s", job_id)

    async def broadcast(self, job_id: str, message: dict) -> None:
        conns = self.connections.get(job_id)
        if not conns:
            return

        dead: List[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception as exc:  # pragma: no cover (network error)
                logger.warning("WebSocket send failed: %s", exc)
                dead.append(ws)

        for ws in dead:
            self.disconnect(job_id, ws)


ws_manager = WebSocketManager()


async def broadcast_progress(job_id: str, message: dict) -> None:
    await ws_manager.broadcast(job_id, message)
