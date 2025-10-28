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
        # Event to signal stopping
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
                "instructions": (
                    "Eres manager de un equipo de ventas y te quiero vender un producto. Eres reacio a comprarlo. Hablas muy rápido."
                ),
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "voice": "alloy",
                "temperature": 1,
                "max_response_output_tokens": 4096,
                "modalities": ["text", "audio"],
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",     
                "input_audio_transcription": {
                    "model": "gpt-4o-transcribe",#"gpt-4o-transcribe", #"whisper-1"
                    #"prompt": "",
                    "language": "es"
                },
                "input_audio_noise_reduction": {
                    "type": "near_field"
                },
                "include": [
                    "item.input_audio_transcription.logprobs"
                ],
            }
        }
        await self.openai_ws.send(json.dumps(session_config))

    async def forward_frontend_to_openai(self):
        try:
            while not self.stop_event.is_set():
                try:
                    msg = await self.frontend_ws.receive_text()
                    #print("📥 Received from frontend:", msg[:100], "...")  # print first 100 chars
                    await self.openai_ws.send(msg)
                except Exception as e:
                    print("⚠️ Frontend WebSocket error:", e)
                    await self.stop()
        except Exception as e:
            print("Frontend stream ended:", e)
            await self.stop()


    async def forward_openai_to_frontend(self):
        try:
            async for msg in self.openai_ws:
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    print("⚠️ [OpenAI] Received non-JSON message.")
                    continue

                msg_type = data.get("type")
                if msg_type == "conversation.item.input_audio_transcription.completed":
                    transcript = (
                        data.get("transcript") or
                        data.get("item", {}).get("transcript") or
                        data.get("item", {}).get("input_audio_transcription", {}).get("transcript")
                    )
                    if transcript:
                        print(f"[User audio]: {transcript}")

                elif msg_type == "response.audio_transcript.delta":
                    partial = data.get("delta", "")
                    if partial:
                        print(f"[Assistant audio partial]: {partial}")

                elif msg_type == "response.audio_transcript.done":
                    transcript = data.get("transcript", "")
                    if transcript:
                        print(f"[Assistant audio full]: {transcript}")

                # forward raw message to frontend
                await self.frontend_ws.send_text(msg)

        except Exception as e:
            print("OpenAI stream ended:", e)
            await self.stop()


    async def run(self):
        # establish connection to OpenAI
        await self.connect_openai()
        # Start the forwarding tasks in parallel
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
