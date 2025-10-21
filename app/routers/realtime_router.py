# app/routers/realtime_router.py
from fastapi import APIRouter, WebSocket
from app.services.realtime_bridge import RealtimeBridge

router = APIRouter()

@router.websocket("/ws/audio")
async def websocket_audio_bridge(websocket: WebSocket):
    await websocket.accept()
    print("🎧 Frontend connected to /ws/audio")

    bridge = RealtimeBridge(frontend_ws=websocket)
    await bridge.run()
