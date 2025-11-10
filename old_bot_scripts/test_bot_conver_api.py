import os
import asyncio
import json
import base64
import sounddevice as sd
import websockets
import sys
from datetime import datetime
from dotenv import load_dotenv

# api key from environment variable
sys.path.insert(0, "../../src")
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("Error: OPENAI_API_KEY is not set in environment variables.")
    sys.exit(1)

# WebSocket endpoint and model
MODEL = "gpt-realtime-2025-08-28"
WS_URL = f"wss://api.openai.com/v1/realtime?model={MODEL}"

# default device --- CHANGE IF NEEDED --- Use Test_audio.py to check devices
sd.default.device = (2, None)  # (input_device, output_device)

TRANSCRIPT_FILE = "transcript.json"
transcript_data = []

SAMPLE_RATE = 19000
CHUNK_SIZE = 1024  # frames per send (~64 ms at 16kHz mono)

async def conversation():
    headers = [("Authorization", f"Bearer {API_KEY}")]
    loop = asyncio.get_running_loop()
    while True:
        try:
            async with websockets.connect(WS_URL, additional_headers=headers, ping_interval=10, ping_timeout=5) as ws:
                # 1) Configure session
                session_update = {
                    "type": "session.update",
                    "session": {
                        "instructions": "You are a business owner who is skeptical about new technologies. I will try to sell you a generative AI product. Reply in Spanish.",
                        "voice": "alloy",           # output voice (optional)
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "turn_detection": {"type": "server_vad"}  # let the server detect pauses
                    }
                }
                await ws.send(json.dumps(session_update))

                async def record_and_send():
                    #Capture microphone input and send to the API in real time
                    def callback(indata, frames, time, status):
                        if status:
                            print("Mic status:", status)
                        pcm_bytes = indata.tobytes()
                        b64 = base64.b64encode(pcm_bytes).decode("ascii")
                        event = {"type": "input_audio_buffer.append", "audio": b64}
                        asyncio.run_coroutine_threadsafe(ws.send(json.dumps(event)), loop)

                    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SIZE, callback=callback):
                        print("🎤 Speaking... (Ctrl+C to exit)")
                        while True:
                            await asyncio.sleep(0.1)

                async def receive_and_play():
                    # Receive text/audio deltas and process them
                    audio_buffer = bytearray()

                    async for raw in ws:
                        event = json.loads(raw)
                        etype = event.get("type")

                        # Partial text
                        if etype == "response.output_text.delta":
                            delta = event.get("delta", "")
                            if delta:
                                print(delta, end="", flush=True)

                        # Final text
                        if etype == "response.output_text.done":
                            full_text = event.get("output_text", "")
                            print("\n--- model finished ---\n")
                            transcript_data.append({"role": "assistant", "text": full_text})
                            save_transcript()

                        # Audio chunk received
                        if etype == "response.output_audio.delta":
                            chunk = base64.b64decode(event.get("delta", ""))
                            audio_buffer.extend(chunk)

                        # Full audio ready
                        if etype == "response.output_audio.done":
                            # Play the complete audio received
                            import numpy as np
                            import sounddevice as sd
                            audio_np = np.frombuffer(bytes(audio_buffer), dtype="int16")
                            sd.play(audio_np, samplerate=SAMPLE_RATE)
                            sd.wait()
                            audio_buffer.clear()

                        # User turn detected
                        if etype == "conversation.item.input_audio_transcription.completed":
                            user_text = event.get("transcript", "")
                            if user_text:
                                print(f"\n👤 You: {user_text}")
                                transcript_data.append({"role": "user", "text": user_text})
                                save_transcript()

                await asyncio.gather(record_and_send(), receive_and_play())
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

def save_transcript():
    print("[DEBUG] transcript_data:", transcript_data)
    with open(TRANSCRIPT_FILE, "w", encoding="utf-8") as f:
        json.dump(transcript_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    try:
        asyncio.run(conversation())
    except KeyboardInterrupt:
        print("\nConversation ended.")
        save_transcript()
