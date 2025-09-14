import sounddevice as sd
import wavio
import whisper
import re

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

def respuesta_tree(texto, contador):
    """
    Por cada palabra en el texto, verifica si la palabra 'hola' está dentro.
    Devuelve una lista de booleanos indicando si 'hola' está en cada palabra.
    """
    breaker = False
    palabras = texto.split()
    palabras = [palabra.lower() for palabra in palabras]
    # Dividir el texto en palabras separando también por signos de puntuación
    palabras = re.findall(r'\w+|[^\w\s]', texto.lower(), re.UNICODE)
    respuesta = ""
    if contador == 0:
        if "hola" in palabras:
            respuesta= "Hola buenas tardes"
        else:
            respuesta = "No me saludaste wey"
    else:
        if "adios" in palabras:
            respuesta = "Adios muy buenas"
            breaker = True

    return (respuesta,breaker)

def conversacion(transcript):
    contador = 0
    while contador < 10:
        archivo = grabar_audio(duracion=8)  # graba 8 segundos
        texto = transcribir_audio(archivo, modelo="small")  # puedes usar tiny/base/small
        respuesta,breaker = respuesta_tree(texto,contador)
        print("\n--- Transcripción ---\n")
        print(texto)
        print("\n--- Respuesta ---\n")
        print(respuesta)
        transcript.append({"speaker": "vendedor", "text": texto})
        transcript.append({"speaker": "cliente", "text": respuesta})

        if breaker:
            break

        contador += 1


if __name__ == "__main__":
    transcript = []
    conversacion(transcript)
