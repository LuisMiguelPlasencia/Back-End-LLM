# ---------------------------------------------------------------------------
# WebSocket router — real-time audio bridge (ElevenLabs)
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket

from app.services.realtime_bridge_elevenlabs import RealtimeBridge

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Realtime"])


@router.websocket("/ws/audio")
async def websocket_audio_bridge(websocket: WebSocket):
    """Bidirectional audio bridge between the frontend and ElevenLabs."""
    await websocket.accept()
    logger.info("Frontend connected to /ws/audio")

    bridge = RealtimeBridge(frontend_ws=websocket)
    await bridge.run()
