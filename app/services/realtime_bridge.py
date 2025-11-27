# app/services/realtime_bridge.py
import asyncio
import json
import os
from app.services.conversations_service import get_conversation_status
from app.services.realtime_service import openai_msg_process, stop_process, user_msg_processed
import websockets
from dotenv import load_dotenv
from ..services.messages_service import send_message
from ..services.scoring_service import scoring
from ..services.prompting_service import master_prompt_generator
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
WS_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime"

class RealtimeBridge:
    def __init__(self, frontend_ws):
        self.frontend_ws = frontend_ws  # WebSocket from browser
        self.openai_ws = None
        # Event to signal stopping
        self.stop_event = asyncio.Event()
        self.user_id = None
        self.conversation_id = None
        self.course_id = None
        self.stage_id = None

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
        #master_prompt = await master_prompt_generator(self.course_id, self.stage_id)
        session_config = {
            "type": "session.update",
            "session": {
                "instructions": 'Eres una ia inteligente',#(master_prompt),
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
                    "model": "whisper-1",#"gpt-4o-transcribe", #"whisper-1"
                    "prompt": "Ehhh, mmm hola buenas te voy a hablar de, ehh negocioss y mmm, bueno pues eso",
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

                    parsed = json.loads(msg)
                    

                    ## Logica front to openai
                    ## TO DO
                    await user_msg_processed(self.user_id, self.conversation_id)

                    if parsed.get("type") == "input_audio_session.start":
                        print("new audio session started")
                        
                        self.user_id = parsed.get("user_id", None)
                        self.conversation_id = parsed.get("conversation_id", None)
                        self.course_id = parsed.get("course_id", None)
                        self.stage_id = parsed.get("stage_id", None)
                        print('user_id:', self.user_id, 'conversation_id:', self.conversation_id, 'course_id:', self.course_id, 'stage_id:', self.stage_id)
                        #master_prompt = await master_prompt_generator(self.course_id, self.stage_id)
                        
                        #await self.openai_ws.send(json.dumps(session_config))
                        #continue

                    elif parsed.get("type") == "input_audio_session.end":
                        print("audio session ended")
                        await self.stop()

                    #parsed.pop("user_id", None)
                    #parsed.pop("conversation_id", None)
                    #parsed.pop("course_id", None)

                    await self.openai_ws.send(json.dumps(parsed))
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

                await openai_msg_process(self.user_id, self.conversation_id)

                ## USER AUDIO TRANSCRIPTION
                if msg_type == "conversation.item.input_audio_transcription.completed":
                    transcript = (
                        data.get("transcript") or
                        data.get("item", {}).get("transcript") or
                        data.get("item", {}).get("input_audio_transcription", {}).get("transcript")
                    )
                    if transcript:
                        print(f"[User audio]: {transcript}")
                        ## insert to db as user message
                        print(self.user_id, self.conversation_id, transcript, "user")
                        await send_message(self.user_id, self.conversation_id, transcript, "user")

                ## AI AUDIO CHUNK
                elif msg_type == "response.audio_transcript.delta":
                    partial = data.get("delta", "")
                    if partial:
                        print(f"[Assistant audio partial]: {partial}")

                ## AI AUDIO FULL
                elif msg_type == "response.audio_transcript.done":
                    transcript = data.get("transcript", "")
                    if transcript:
                        print(f"[Assistant audio full]: {transcript}")
                        # if keyword in transcript:
                        # stop()
                        #await openai_msg_process(self.user_id, self.conversation_id)
                        ## insert to db as assistant message
                        await send_message(self.user_id, self.conversation_id, transcript, "assistant")
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
        ## update conversation status to closed in db
        print('stopping realtime bridge...')
        await stop_process(self.conversation_id, self.user_id)
        if not self.stop_event.is_set():
            self.stop_event.set()

        print(self.conversation_id)
        
        ## scoring conversation if conver finished
        status = await get_conversation_status(self.conversation_id,self.user_id)
        print(f'status checked: {status}')
        if status == "FINISHED": 
            print('computing scores')
            await scoring(self.conversation_id)

        try:
            if self.openai_ws:
                await self.openai_ws.close()
            await self.frontend_ws.close()
        except:
            pass 