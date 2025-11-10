import base64
import json
import os
import queue
from re import S
import socket
import subprocess
import threading
import time
import pyaudio
import socks
import websocket
import psycopg2
from dotenv import load_dotenv
import os

# Load variables from a .env file into environment variables
load_dotenv()

# Set up SOCKS5 proxy
socket.socket = socks.socksocket

# Use the provided OpenAI API key and URL
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("API key is missing. Please set the 'OPENAI_API_KEY' environment variable.")

WS_URL = 'wss://api.openai.com/v1/realtime?model=gpt-realtime'

CHUNK_SIZE = 1024
RATE = 24000
FORMAT = pyaudio.paInt16
conversation_log = []  # full transcript (speaker, text)
last_activity_time = time.time()
MAX_SILENCE_SECONDS = 30  # shutdown after 30 seconds of silence
MAX_TURNS = 6


audio_buffer = bytearray()
mic_queue = queue.Queue()

stop_event = threading.Event()

mic_on_at = 0
mic_active = None
REENGAGE_DELAY_MS = 500

# Function to clear the audio buffer
def clear_audio_buffer():
    global audio_buffer
    audio_buffer = bytearray()
    # print('🔵 Audio buffer cleared.')

# Function to stop audio playback
def stop_audio_playback():
    global is_playing
    is_playing = False
    # print('🔵 Stopping audio playback.')

# Function to handle microphone input and put it into a queue
def mic_callback(in_data, frame_count, time_info, status):
    global mic_on_at, mic_active

    if mic_active != True:
        # print('🎙️🟢 Mic active')
        mic_active = True
    mic_queue.put(in_data)

    # if time.time() > mic_on_at:
    #     if mic_active != True:
    #         print('🎙️🟢 Mic active')
    #         mic_active = True
    #     mic_queue.put(in_data)
    # else:
    #     if mic_active != False:
    #         print('🎙️🔴 Mic suppressed')
    #         mic_active = False

    return (None, pyaudio.paContinue)


# Function to send microphone audio data to the WebSocket
def send_mic_audio_to_websocket(ws):
    try:
        while not stop_event.is_set():
            if not mic_queue.empty():
                mic_chunk = mic_queue.get()
                # print(f'🎤 Sending {len(mic_chunk)} bytes of audio data.')
                encoded_chunk = base64.b64encode(mic_chunk).decode('utf-8')
                message = json.dumps({'type': 'input_audio_buffer.append', 'audio': encoded_chunk})
                try:
                    ws.send(message)
                except Exception as e:
                    print(f'Error sending mic audio: {e}')
    except Exception as e:
        print(f'Exception in send_mic_audio_to_websocket thread: {e}')
    finally:
        print('Exiting send_mic_audio_to_websocket thread.')


# Function to handle audio playback callback
def speaker_callback(in_data, frame_count, time_info, status):
    global audio_buffer, mic_on_at

    bytes_needed = frame_count * 2
    current_buffer_size = len(audio_buffer)

    if current_buffer_size >= bytes_needed:
        audio_chunk = bytes(audio_buffer[:bytes_needed])
        audio_buffer = audio_buffer[bytes_needed:]
        mic_on_at = time.time() + REENGAGE_DELAY_MS / 1000
    else:
        audio_chunk = bytes(audio_buffer) + b'\x00' * (bytes_needed - current_buffer_size)
        audio_buffer.clear()

    return (audio_chunk, pyaudio.paContinue)


# Function to receive audio data from the WebSocket and process events
def receive_audio_from_websocket(ws):
    global audio_buffer, current_speaker, speech_start_time
    last_user_start_time = None
    user_start_time = None

    try:
        while not stop_event.is_set():
            try:
                message = ws.recv()
                if not message:  # Handle empty message (EOF or connection close)
                    #print('🔵 Received empty message (possibly EOF or WebSocket closing).')
                    break

                # Now handle valid JSON messages only
                message = json.loads(message)
                event_type = message['type']
                # print(f'⚡️ Received WebSocket event: {event_type}')

                if event_type == 'input_audio_buffer.speech_started':
                    clear_audio_buffer()
                    stop_audio_playback()
                    user_start_time = time.time()

                if event_type == 'session.created':
                    send_fc_session_update(ws)

                elif event_type == 'response.audio.delta':
                    llm_start_time = time.time()
                    audio_content = base64.b64decode(message['delta'])
                    audio_buffer.extend(audio_content)
                    #print(f'🔵 Received {len(audio_content)} bytes, total buffer size: {len(audio_buffer)}')

                elif event_type == 'conversation.item.input_audio_transcription.completed':
                    user_text = message.get('transcript', '')
                    if user_text and user_start_time:
                        duracion = round(time.time() - user_start_time, 2)
                        user_start_time = None
                        print('========= Usuario =========')
                        print(user_text)
                        print(f"(duración: {duracion}s)\n")
                        print('\n')
                        conversation_log.append({
                            "speaker": "user",
                            "text": user_text,
                            "duracion": round(duracion, 2)
                        })
                        # Detectar final de conversación
                        if any(phrase in user_text.lower() for phrase in ['gracias', 'hasta luego', 'adiós']):
                            print("💬 Conversación final detectada. Cerrando sesión...")
                            stop_event.set()
                        elif len(conversation_log) // 2 >= MAX_TURNS:
                            print("💬 Límite de turnos alcanzado. Cerrando sesión...")
                            stop_event.set()
                        elif duracion > MAX_SILENCE_SECONDS:
                            print("💬 Duración de silencio excedida. Cerrando sesión...")
                            stop_event.set()

                        last_user_end_time = time.time()

                elif event_type == 'response.audio_transcript.done':
                    llm_text = message.get('transcript', '')
                    if llm_text:
                        duracion = round(time.time() - last_user_end_time + 5, 2)
                        last_user_end_time = None
                        print('========= LLM =========')
                        print(llm_text)
                        print(f"(duración: {duracion}s)\n")
                        print('\n')
                        conversation_log.append({
                            "speaker": "assistant",
                            "text": llm_text,
                            "duracion": round(duracion, 2)
                        })

                        # Detectar final de conversación
                        if any(phrase in llm_text.lower() for phrase in ['gracias', 'hasta luego', 'adiós']):
                            print("💬 Conversación final detectada. Cerrando sesión...")
                            stop_event.set()
                        elif len(conversation_log) // 2 >= MAX_TURNS:
                            print("💬 Límite de turnos alcanzado. Cerrando sesión...")
                            stop_event.set()
                        elif duracion > MAX_SILENCE_SECONDS:
                            print("💬 Duración de silencio excedida. Cerrando sesión...")
                            stop_event.set()


                elif event_type == 'input_audio_buffer.speech_started':
                    clear_audio_buffer()
                    stop_audio_playback()

                #elif event_type == 'response.audio.done':
                    #print('🔵 AI finished speaking.')
                
            except Exception as e:
                print(f'Error receiving audio: {e}')
    except Exception as e:
        print(f'Exception in receive_audio_from_websocket thread: {e}')
    finally:
        print('Exiting receive_audio_from_websocket thread.')


# Function to send session configuration updates to the server
def send_fc_session_update(ws):
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
                "model": "whisper-1",#"gpt-4o-transcribe", #"whisper-1"
                #"prompt": "",
                #"language": "es"
            },
            "input_audio_noise_reduction": {
                "type": "near_field"
            },
            "include": [
                "item.input_audio_transcription.logprobs"
            ],
            
        }
    }
    # Convert the session config to a JSON string
    session_config_json = json.dumps(session_config)
    # print(f"Send FC session update: {session_config_json}")

    # Send the JSON configuration through the WebSocket
    try:
        ws.send(session_config_json)
    except Exception as e:
        print(f"Failed to send session update: {e}")



# Function to create a WebSocket connection using IPv4
def create_connection_with_ipv4(*args, **kwargs):
    # Enforce the use of IPv4
    original_getaddrinfo = socket.getaddrinfo

    def getaddrinfo_ipv4(host, port, family=socket.AF_INET, *args):
        return original_getaddrinfo(host, port, socket.AF_INET, *args)

    socket.getaddrinfo = getaddrinfo_ipv4
    try:
        return websocket.create_connection(*args, **kwargs)
    finally:
        # Restore the original getaddrinfo method after the connection
        socket.getaddrinfo = original_getaddrinfo

# Function to establish connection with OpenAI's WebSocket API
def connect_to_openai():
    ws = None
    try:
        ws = create_connection_with_ipv4(
            WS_URL,
            header=[
                f'Authorization: Bearer {API_KEY}',
                'OpenAI-Beta: realtime=v1'
            ]
        )
        # print('Connected to OpenAI WebSocket.')


        # Start the recv and send threads
        receive_thread = threading.Thread(target=receive_audio_from_websocket, args=(ws,))
        receive_thread.start()

        mic_thread = threading.Thread(target=send_mic_audio_to_websocket, args=(ws,))
        mic_thread.start()

        # Wait for stop_event to be set
        while not stop_event.is_set():
            time.sleep(0.1)

        # Send a close frame and close the WebSocket gracefully
        # print('Sending WebSocket close frame.')
        ws.send_close()

        receive_thread.join()
        mic_thread.join()

        # print('WebSocket closed and threads terminated.')
    except Exception as e:
        print(f'Failed to connect to OpenAI: {e}')
    finally:
        if ws is not None:
            try:
                ws.close()
                # print('WebSocket connection closed.')
            except Exception as e:
                print(f'Error closing WebSocket connection: {e}')


# Main function to start audio streams and connect to OpenAI
def start_conver_and_get_transcript():
    p = pyaudio.PyAudio()

    mic_stream = p.open(
        format=FORMAT,
        channels=1,
        rate=RATE,
        input=True,
        stream_callback=mic_callback,
        frames_per_buffer=CHUNK_SIZE
    )

    speaker_stream = p.open(
        format=FORMAT,
        channels=1,
        rate=RATE,
        output=True,
        stream_callback=speaker_callback,
        frames_per_buffer=CHUNK_SIZE
    )

    try:
        mic_stream.start_stream()
        speaker_stream.start_stream()

        connect_to_openai()

        # Esperar hasta que stop_event esté activado
        while not stop_event.is_set():
            time.sleep(0.1)

    except KeyboardInterrupt:
        print('🟥 Interrupción manual detectada.')
        stop_event.set()

    finally:
        # Detener streams y liberar recursos
        mic_stream.stop_stream()
        mic_stream.close()
        speaker_stream.stop_stream()
        speaker_stream.close()
        p.terminate()

        print('\n🎧 Streams cerrados correctamente.')
        print('🧠 Sesión finalizada.\n')

        # Mostrar el transcript completo
        if conversation_log:
            print("\n========================")
            print("📜 TRANSCRIPT COMPLETO")
            print("========================\n")
            for turno in conversation_log:
                speaker = turno["speaker"]
                text = turno["text"]
                duracion = turno["duracion"]
                print(f"{speaker.upper()} ({duracion}s): {text}\n")

            # print(conversation_log)

            # Guardar JSON
            # with open("transcript.json", "w", encoding="utf-8") as f:
            #     json.dump(conversation_log, f, ensure_ascii=False, indent=4)
            # print("💾 Transcript guardado en 'transcript.json'")

        else:
            print("No se registraron mensajes en la conversación.")
        
        return conversation_log

def send_transcript_to_db(transcript):

    # --- 1. Load Environment Variables ---
    # This looks for a .env file and loads its contents into os.environ
    load_dotenv()

    # --- 2. Retrieve Connection Variables ---
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_PORT = os.getenv("DB_PORT")

    """Establishes a connection to the pgEdge Cloud database."""
    conn = None
    cur = None

    #conversation_id = 'sdjlkfsdlfdks'
    
    try:
        print("Attempting to connect to pgEdge Cloud...")
        
        # Connect to the Database using retrieved environment variables
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        
        # Create a cursor object to execute SQL commands
        cur = conn.cursor()
        
        print("✅ Connection successful!")
        
        # --- 3. Execute SQL Query ---
        insert_query = """
            insert into conversaapp.messages (role, content)
            values (%s, %s)
        """

        cur.executemany(
            insert_query,
            [(m["speaker"], m["text"]) for m in transcript]
        )
        conn.commit()
        
    except psycopg2.Error as e:
        # Handle specific PostgreSQL errors
        print(f"❌ Database Error: {e}")
        
    except Exception as e:
        # Handle other general errors
        print(f"❌ An unexpected error occurred: {e}")
        
    finally:
        # --- 4. Close the Connection and Cursor ---
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    transcript = start_conver_and_get_transcript()
    send_transcript_to_db(transcript)
