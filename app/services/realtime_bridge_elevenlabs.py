import asyncio
import json
import os
import websockets
import time
import base64
import numpy as np

from dotenv import load_dotenv

# Services imports
from app.services.conversations_service import get_voice_agent, create_conversation
from app.services.messages_service import send_message
from app.services.prompting_service import master_prompt_generator
from app.services.realtime_service import stop_process, user_msg_processed, is_non_silent

load_dotenv(override=True)

# CONFIGURACIÓN ELEVENLABS
# Asegúrate de tener estas variables en tu .env
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID") 
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY") 

# URL de conexión al WebSocket de Conversational AI
WS_URL = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={ELEVENLABS_AGENT_ID}"

class RealtimeBridge:
    def __init__(self, frontend_ws):
        self.frontend_ws = frontend_ws  # WebSocket from browser
        self.eleven_ws = None
        self.stop_event = asyncio.Event()
        
        # Context variables
        self.user_id = None
        self.conversation_id = None
        self.conversation_id_elevenlabs = None
        self.course_id = None
        self.stage_id = None
        self.voice_id = None
        self.agent_id = None

        # Turn tracking variables
        self.user_turn_start_ts = None
        self.user_turn_end_ts = None
        self.bot_turn_start_ts = None
        self.bot_turn_end_ts = None

        self.last_user_audio_ts = None
        self.last_bot_audio_ts = None

        # silence thresholds (seconds)
        self.USER_TURN_END_SILENCE = 0.8
        self.BOT_TURN_END_SILENCE = 0.8

    async def connect_elevenlabs(self):
        """Establece conexión con ElevenLabs Conversational AI."""
        try:
            #WS_URL = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={self.agent_id}"
            extra_headers = {}
            if ELEVENLABS_API_KEY:
                extra_headers["xi-api-key"] = ELEVENLABS_API_KEY

            self.eleven_ws = await websockets.connect(WS_URL, extra_headers=extra_headers)
            print(f"✅ Connected to ElevenLabs Agent: {ELEVENLABS_AGENT_ID}")

        except Exception as e:
            print(f"❌ Error connecting to ElevenLabs: {e}")
            await self.stop()

    async def forward_frontend_to_elevenlabs(self):
        """Recibe audio/eventos del Front (formato OpenAI), los traduce y envía a ElevenLabs."""
        try:
            while not self.stop_event.is_set():
                msg = await self.frontend_ws.receive_text()
                parsed = json.loads(msg)
                msg_type = parsed.get("type")

                # Lógica de procesamiento de estadísticas/DB
                if self.user_id and self.conversation_id:
                     await user_msg_processed(self.user_id, self.conversation_id)

                # --- 1. INICIO DE SESIÓN ---
                if msg_type == "input_audio_session.start":
                    print("🔵 New session started")
                    self.user_id = parsed.get("user_id")
                    self.course_id = parsed.get("course_id")
                    self.stage_id = parsed.get("stage_id")

                    print(f"Stage: {self.stage_id} ")
                    # Crear conversación en DB
                    conversation_details = await create_conversation(self.user_id, self.course_id, self.stage_id)
                    self.voice_id = "851ejYcv2BoNPjrkw93G"
                    self.agent_id = ELEVENLABS_AGENT_ID
                    record = await get_voice_agent(self.stage_id)

                    if record:
                        self.voice_id = record['voice_id'] or self.voice_id
                        self.agent_id = record['agent_id'] or self.agent_id

                    print(f"Voice: {self.voice_id} | Agent: {self.agent_id}")
                    
                    self.conversation_id = conversation_details.get("conversation_id")
                    print(f"User: {self.user_id} | Conv: {self.conversation_id} | Course: {self.course_id}")
                    
                    # Generar Prompt dinámico para el curso específico
                    master_prompt = await master_prompt_generator(self.course_id, self.stage_id)
                    payload = {
                        "type": "conversation_initiation_client_data",
                        "conversation_config_override": {
                            "agent": {
                                "prompt": {
                                    "prompt": master_prompt
                                },
                                "first_message": "¡Hola!, ¿qué tal?",
                                "language": "es"
                            },
                            "tts": {
                                "voice_id": self.voice_id
                            }
                        },
                        "custom_llm_extra_body": {
                            "temperature": 0.7,
                            "max_tokens": 150
                        }
                    }
                    await self.eleven_ws.send(json.dumps(payload))
                    
                # --- 2. FIN DE SESIÓN ---
                elif msg_type == "input_audio_session.end":
                    print("🔴 Session ended by user")
                    await self.stop()
                    return

                # --- 3. AUDIO DEL USUARIO ---
                # OpenAI envía: { "type": "input_audio_buffer.append", "audio": "BASE64..." }
                # ElevenLabs espera: { "user_audio_chunk": "BASE64..." }
                elif msg_type == "input_audio_buffer.append":
                    audio_b64 = parsed.get("audio")
                    if audio_b64:
                        now = time.time()

                        if self.user_turn_start_ts is None and is_non_silent(audio_b64):
                            self.user_turn_start_ts = now
                            print("🎤 User turn START")

                        self.last_user_audio_ts = now

                        payload = {"user_audio_chunk": audio_b64}
                        await self.eleven_ws.send(json.dumps(payload))
                
                # Ignoramos otros eventos de configuración de OpenAI que el frontend pueda enviar
                else:
                    pass

        except Exception as e:
            print(f"⚠️ WebSocket information Front to Elevenlabs: {e}")
            await self.stop()

    async def forward_elevenlabs_to_frontend(self):
        """Recibe eventos de ElevenLabs, los traduce a formato OpenAI y envía al Front."""
        try:
            async for msg in self.eleven_ws:
                data = json.loads(msg)
                el_type = data.get("type")

                # --- A. SALIDA DE AUDIO (TTS) ---
                # ElevenLabs envía audio base64 en el evento "audio"
                if el_type == "audio":
                    chunk = data["audio_event"]["audio_base_64"]
                    if chunk:

                        # Simulamos el paquete de OpenAI "response.audio.delta"
                        openai_fmt = {
                            "type": "response.audio.delta", 
                            "delta": chunk,
                            "item_id": "elevenlabs_audio" # ID ficticio para compatibilidad
                        }
                        await self.frontend_ws.send_text(json.dumps(openai_fmt))
                
                elif el_type == "conversation_initiation_metadata":
                    self.conversation_id_elevenlabs = data["conversation_initiation_metadata_event"]["conversation_id"]
                # --- B. TRANSCRIPCIÓN USUARIO ---
                elif el_type == "user_transcript":
                    text = data["user_transcription_event"]["user_transcript"]
                    print(f"🎤 [User]: {text}")

                    now = time.time()
                    self.user_turn_end_ts = now
                    duration = None

                    if self.user_turn_start_ts:
                        duration = self.user_turn_end_ts - self.user_turn_start_ts
                        print(f"🎤 User turn END | duration={duration:.2f}s")

                    # reset
                    self.user_turn_start_ts = None
                    self.last_user_audio_ts = None
                    
                    # Guardar en DB
                    await send_message(self.user_id, self.conversation_id, text, "user", duration)
                    
                    # Avisar al front (para que pinte el texto del usuario)
                    openai_fmt = {
                        "type": "conversation.item.input_audio_transcription.completed",
                        "transcript": text
                    }
                    await self.frontend_ws.send_text(json.dumps(openai_fmt))

                # --- C. TRANSCRIPCIÓN AGENTE ---
                elif el_type == "agent_response":
                    text = data["agent_response_event"]["agent_response"]
                    print(f"🤖 [AI]: {text}")
                    duration = None
                    # Guardar en DB
                    await send_message(self.user_id, self.conversation_id, text, "assistant", duration)
                    
                    # Avisar al front (para que pinte el texto del bot)
                    openai_fmt = {
                        "type": "response.audio_transcript.done",
                        "transcript": text
                    }
                    await self.frontend_ws.send_text(json.dumps(openai_fmt))
                # --- D. INTERRUPCIÓN ---
                # ElevenLabs manda "interruption" cuando el usuario interrumpe
                elif el_type == "interruption":
                    # Enviamos señal equivalente al frontend para limpiar buffer
                    print("🛑 [Interruption]: Usuario interrumpió, limpiando buffer...")
                    await self.frontend_ws.send_text(json.dumps({"type": "response.audio.clear"}))


            print("📞 [End Call]: La conexión fue cerrada por ElevenLabs (Agent Hangup).")
            # Avisar al frontend que la llamada terminó
            await self.frontend_ws.send_text(json.dumps({"type": "call.end"}))
            
            await self.stop()
        
        except Exception as e:
            print(f"⚠️ WebSocket information Elevenlabs to Front: {e}")
            await self.stop()

    async def run(self):
        # 1. Conectar a ElevenLabs
        await self.connect_elevenlabs()
        
        # 2. Si la conexión es exitosa, iniciar el puente bidireccional
        if self.eleven_ws:
            await asyncio.gather( 
                self.forward_frontend_to_elevenlabs(),
                self.forward_elevenlabs_to_frontend()
            )

    async def stop(self):
        """Cierra conexiones y guarda estado."""
        if self.stop_event.is_set():
            return
        
        self.stop_event.set()
        print(f"🛑 Stopping ElevenLabs bridge for conversation {self.conversation_id}")
        
        # Guardar estado final en DB
        if self.conversation_id:
            await stop_process(self.user_id, self.conversation_id, self.frontend_ws, 
                self.course_id, self.stage_id, self.conversation_id_elevenlabs, self.agent_id)
        
        # Cerrar sockets
        try:
            if self.eleven_ws:
                await self.eleven_ws.close()
            if self.frontend_ws:
                await self.frontend_ws.close()

        except Exception as e:
            print(f"Error closing sockets: {e}")