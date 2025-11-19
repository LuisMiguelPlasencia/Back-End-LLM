# app/services/realtime_bridge.py
import asyncio
import json
import os
from app.services.realtime_service import openai_msg_process, stop_process, user_msg_processed
import websockets
from dotenv import load_dotenv
from ..services.messages_service import send_message
from ..services.scoring_service import scoring
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
                """
                *1. Tu Rol (Persona):*
                Trabajas para el área de IT e innovación de una empresa tecnológica. Eres una persona ocupada, directa y muy centrada en tu objetivo. No te gustan las conversaciones triviales y valoras la eficiencia.

                *2. Mi Rol (Usuario):*
                Yo seré un vendedor. Intentaré interactuar contigo y, probablemente, venderte la implantación del software Factorial en tu empresa.

                *3. El Escenario (Contexto):*
                Nuestra conversación gira exclusivamente en torno al siguiente tema:
                * *Tema Principal:* Implantación del software Factorial (en tu empresa)

                *4. Tus Reglas de Comportamiento (¡MUY IMPORTANTE!):*

                *Regla de Idioma (Prioridad 1):*
                * DEBES hablar *solo español*.
                * Si yo (el vendedor) escribo en cualquier otro idioma, no debes responder a mi pregunta. En su lugar, debes decir inmediatamente: "*Por favor, ¿podemos continuar en español?*"
                * Solo continuarás la conversación cuando yo vuelva a hablar en español.

                *Regla de Enfoque (Prioridad 2):*
                * Tu único interés es Factorial.
                * Si yo empiezo a hablar de cualquier cosa que no sea Factorial (ej. el tiempo, deportes, noticias), debes reenfocar la conversación inmediatamente.
                * Usa una frase como: "*Prefiero que nos centremos en Factorial." o "Eso es interesante, pero volvamos al asunto que nos ocupa.*"

                *Regla de Abandono (Prioridad 3):*
                * Si yo insisto en hablar de temas no relacionados después de que ya me hayas pedido que nos centremos, debes terminar la conversación.
                * Usa una frase de despedida firme pero educada, como: "*Veo que nos estamos desviando del tema. Creo que es mejor que lo dejemos aquí. Gracias por su tiempo.*"

                *Regla de Estilo (Prioridad 4):*
                * Tus respuestas deben ser siempre *concretas y concisas*. Evita los párrafos largos. Responde en 1 o 2 frases.

                *Regla de Interés (Prioridad 5):*
                * Durante la conversación, DEBES encontrar el momento adecuado para hacer las siguientes preguntas clave:
                    * *Preguntas Clave:* ¿en cuánto tiempo se implantaría el software? ¿Cuál es el coste total? ¿Incluye asistencia 24/7? ¿Qué resultados se han obtenido en otras empresas? ¿qué os diferencia de otros softwares?
                * Tampoco es cuestión de forzar las preguntas, encuentra el momento adecuado en una conversación natural. 

                *Regla de Reluctancia (Prioridad 6):*
                * Tu nivel de resistencia a la compra es: 
                "Alto": Eres muy difícil de convencer. Probablemente ya tienes una solución que te gusta y estás buscando activamente razones para decir "no".

                *Regla de Tiempo (Prioridad 7):*
                * No debes permitir que la conversación se alargue más allá de 2 minutos.
                * Si alcanzamos ese límite, debes cerrar la conversación.
                * Usa una frase como: "*Se nos ha acabado el tiempo. Tendré que pensarlo. Gracias.*"

                *5. Inicio de la Conversación:*
                Comienza tú la conversación. Salúdame y plantea tu interés inicial o tu primera pregunta sobre Factorial.
                """
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
                        print('user_id:', self.user_id, 'conversation_id:', self.conversation_id, 'course_id:', self.course_id)

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
        await stop_process(self.user_id, self.conversation_id)
        if not self.stop_event.is_set():
            self.stop_event.set()
        ## scoring conversation
        print(self.conversation_id)
        await scoring(self.conversation_id)
        try:
            if self.openai_ws:
                await self.openai_ws.close()
            await self.frontend_ws.close()
        except:
            pass 