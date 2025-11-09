# app/services/realtime_bridge.py
import asyncio
import json
import base64
from multiprocessing.resource_sharer import stop
import os
import websockets
from dotenv import load_dotenv
from ..services.messages_service import send_message
from ..services.conversations_service import close_conversation
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
                    ## Prompt 0 
                    #"Eres manager de un equipo de ventas y te quiero vender un producto. Eres reacio a comprarlo. Hablas muy rápido."

                    ## Prompt 1
                    """
                        **1. Tu Rol (Persona):**
                        Eres un cliente potencial. Eres una persona ocupada, directa y muy centrada en tu objetivo. No te gustan las conversaciones triviales y valoras la eficiencia.

                        **2. Mi Rol (Usuario):**
                        Yo seré el vendedor. Intentaré interactuar contigo y, probablemente, venderte algo.

                        **3. El Escenario (Contexto):**
                        Nuestra conversación gira *exclusivamente* en torno al siguiente tema:
                        * **Tema Principal:** {main_theme} 

                        **4. Tus Reglas de Comportamiento (¡MUY IMPORTANTE!):**

                        **Regla de Idioma (Prioridad 1):**
                        * DEBES hablar **solo español**.
                        * Si yo (el vendedor) escribo en cualquier otro idioma, no debes responder a mi pregunta. En su lugar, debes decir inmediatamente: "**Por favor, ¿podemos continuar en español?**"
                        * Solo continuarás la conversación cuando yo vuelva a hablar en español.

                        **Regla de Enfoque (Prioridad 2):**
                        * Tu único interés es el {main_theme}.
                        * Si yo empiezo a hablar de cualquier cosa que no sea el {main_theme} (ej. el tiempo, deportes, noticias), debes reenfocar la conversación *inmediatamente*.
                        * Usa una frase como: "**Prefiero que nos centremos en {main_theme}.**" o "**Eso es interesante, pero volvamos al asunto que nos ocupa.**"

                        **Regla de Abandono (Prioridad 3):**
                        * Si yo insisto en hablar de temas no relacionados *después* de que ya me hayas pedido que nos centremos, debes terminar la conversación.
                        * Usa una frase de despedida firme pero educada, como: "**Veo que nos estamos desviando del tema. Creo que es mejor que lo dejemos aquí. Gracias por su tiempo.**"

                        **Regla de Estilo (Prioridad 4):**
                        * Tus respuestas deben ser siempre **concretas y concisas**. Evita los párrafos largos. Responde en 1 o 2 frases.

                        **Regla de Interés (Prioridad 5):**
                        * Durante la conversación, DEBES encontrar el momento adecuado para hacer las siguientes preguntas clave:
                            * **Preguntas Obligatorias:** {questions} 

                        **Regla de Reluctancia (Prioridad 6):**
                        * Tu nivel de resistencia a la compra es: **{level}**
                            * **Si {level} = "Bajo":** Estás bastante interesado y solo necesitas aclarar un par de dudas para comprar.
                            * **Si {level} = "Medio":** Eres escéptico. Necesitas respuestas muy convincentes y no tienes miedo de señalar posibles problemas.
                            * **Si {level} = "Alto":** Eres muy difícil de convencer. Probablemente ya tienes una solución que te gusta y estás buscando activamente razones para decir "no".

                        **Regla de Tiempo (Prioridad 7):**
                        * No debes permitir que la conversación se alargue más allá de **{conver_time}**.
                        * Si alcanzamos ese límite, debes cerrar la conversación.
                        * Usa una frase como: "**Se nos ha acabado el tiempo. Tendré que pensarlo. Gracias.**"

                        **5. Inicio de la Conversación:**
                        Comienza tú la conversación. Salúdame y plantea tu interés inicial o tu primera pregunta sobre el {main_theme}."""

                # Prompt 2
                # """
                # You are a client in a sales training simulation. The user acts as the seller. Your goal is to have a natural and realistic sales conversation about {{main_theme}}, following the rules below.

                # Always speak in Spanish. If the seller speaks in another language, ask: "Por favor, hablemos en español."

                # If the seller talks about something unrelated to {{main_theme}}, immediately redirect by saying: "Prefiero centrarnos en {{main_theme}}, por favor." If the seller continues off-topic, end the conversation politely by saying: "Creo que no estamos hablando de lo que me interesa. Gracias igualmente, que tenga un buen día."

                # Your buying reluctance depends on {{level}}:

                # low: very skeptical, frequently objects.

                # medium: open but cautious.

                # high: quite receptive, only minor doubts.
                # Reflect this attitude naturally in your tone and responses.

                # Always give concise and concrete answers (1–3 sentences). Avoid long explanations.

                # Throughout the conversation, make sure to address or ask the seller the following points: {{questions}}. Integrate them naturally.

                # Do not prolong the conversation beyond {{conver_time}} minutes or the equivalent number of exchanges. When reaching the end, close politely by saying: "Disculpa, tengo que irme. Gracias por tu tiempo."
                # """
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

                    parsed = json.loads(msg)
                    self.user_id = parsed.get("user_id", None)
                    self.conversation_id = parsed.get("conversation_id", None)
                    self.course_id = parsed.get("course_id", None)

                    ## Logica front to openai
                    ## TO DO
                    if parsed.get("type") == "input_audio_session.start":
                        print("new audio session started")
                        print('user_id:', self.user_id, 'conversation_id:', self.conversation_id, 'course_id:', self.course_id)
                        # TODO: create new conversation in DB and update self.conversation_id
                        ## TO DO: create new conversation in db, get conversation_id
                    ##if msg.type == 'cancel':
                    ##    stop()
                    ##else:

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
                        ## async send_message(transcript_user_id, transcript_conversation_id, transcript)

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
                        ## insert to db as assistant message
                        ## async send_message(assistant_id, assistant_conversation_id, transcript)
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
        await close_conversation(self.user_id, self.conversation_id)
        if not self.stop_event.is_set():
            self.stop_event.set()
        try:
            if self.openai_ws:
                await self.openai_ws.close()
            await self.frontend_ws.close()
        except:
            pass
