# app/services/realtime_bridge.py
import asyncio
import json
import base64
import os
import websockets
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
WS_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime"

class RealtimeBridge:
    def __init__(self, frontend_ws):
        self.frontend_ws = frontend_ws  # WebSocket from browser
        self.openai_ws = None
        self.stop_event = asyncio.Event()

    async def connect_openai(self):
        self.openai_ws = await websockets.connect(
            WS_URL,
            extra_headers={
                "Authorization": f"Bearer {API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
        )
        print("✅ Connected to OpenAI Realtime API")

        # Send initial session configuration (reuse from realtime.py)
        session_config = {
            "type": "session.update",
            "session": {
                "instructions": "Eres manager de un equipo de ventas, hablas rápido y eres reacio a comprar.",
                "voice": "alloy",
                "modalities": ["audio", "text"],
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "silence_duration_ms": 500
                },
            },
        }
        await self.openai_ws.send(json.dumps(session_config))

    async def forward_frontend_to_openai(self):
        """Frontend sends audio → we forward to OpenAI"""
        try:
            while not self.stop_event.is_set():
                msg = await self.frontend_ws.receive_text()
                await self.openai_ws.send(msg)
        except Exception as e:
            print("Frontend stream ended:", e)
            await self.stop()

    async def forward_openai_to_frontend(self):
        """OpenAI sends back audio + transcript → send to frontend"""
        try:
            async for msg in self.openai_ws:
                await self.frontend_ws.send_text(msg)
        except Exception as e:
            print("OpenAI stream ended:", e)
            await self.stop()

    async def run(self):
        await self.connect_openai()
        await asyncio.gather(
            self.forward_frontend_to_openai(),
            self.forward_openai_to_frontend()
        )

    async def stop(self):
        if not self.stop_event.is_set():
            self.stop_event.set()
        try:
            if self.openai_ws:
                await self.openai_ws.close()
            await self.frontend_ws.close()
        except:
            pass
