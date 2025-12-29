# app/routers/realtime_router.py
from fastapi import APIRouter, WebSocket
from app.services.realtime_bridge_elevenlabs import RealtimeBridge

router = APIRouter()

@router.websocket("/ws/audio")
async def websocket_audio_bridge(websocket: WebSocket):
    # Accept the WebSocket connection from the frontend
    await websocket.accept()
    print("🎧 Frontend connected to /ws/audio")

    # Create RealtimeBridge instance and run it
    bridge = RealtimeBridge(frontend_ws=websocket)
    await bridge.run()
