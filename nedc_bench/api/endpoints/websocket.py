from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from nedc_bench.api.services.job_manager import job_manager
from nedc_bench.api.services.websocket_manager import ws_manager


router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str) -> None:
    await ws_manager.connect(job_id, websocket)

    try:
        job = await job_manager.get_job(job_id)
        if job:
            await websocket.send_json({
                "type": "initial",
                "job": {
                    "id": job["id"],
                    "status": job["status"],
                    "created_at": job["created_at"].isoformat(),
                },
            })
        else:
            await websocket.send_json({"type": "error", "message": f"Job {job_id} not found"})
            await websocket.close()
            return

        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if msg == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        ws_manager.disconnect(job_id, websocket)
        logger.info("WebSocket disconnected for job %s", job_id)
