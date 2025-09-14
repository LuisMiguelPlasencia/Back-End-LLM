import sounddevice as sd
import wavio
import whisper

def grabar_audio(nombre_archivo="grabacion.wav", duracion=10, fs=16000):
    """
    Graba audio desde el micrófono y lo guarda en un archivo WAV.
    """
    print(f"Grabando {duracion} segundos... (habla ahora)")
    audio = sd.rec(int(duracion * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()  # Esperar a que termine
    wavio.write(nombre_archivo, audio, fs, sampwidth=2)
    print(f"Audio guardado en {nombre_archivo}")
    return nombre_archivo

def transcribir_audio(nombre_archivo="grabacion.wav", modelo="base"):
    """
    Transcribe el archivo de audio usando Whisper.
    Modelos disponibles: tiny, base, small, medium, large
    """
    print("Cargando modelo Whisper...")
    model = whisper.load_model(modelo)  
    print("Transcribiendo...")
    result = model.transcribe(nombre_archivo, language="es")
    return result["text"]

if __name__ == "__main__":
    archivo = grabar_audio(duracion=8)  # graba 8 segundos
    texto = transcribir_audio(archivo, modelo="small")  # puedes usar tiny/base/small
    print("\n--- Transcripción ---\n")
    print(texto)
