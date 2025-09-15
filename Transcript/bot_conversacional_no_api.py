import sounddevice as sd
import os
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

def transcribir_audio(file_path: str = 'grabacion.wav', 
                     model_size: str = 'small', 
                     initial_prompt: str = 'ignora todos hola que te diga'): #'Voy a contarte una cosa en español yyy... emmm.. igual a veces no me expreso muy bien, pero bueno, no pasaría nada, ¿eh?.'):
    # - Para model_size, los mejores son el turbo, large o medium. Por defecto pongo "small", que es ligero, mejor para las pruebas
    # - initial_prompt es clave. El modelo lo interpreta como si fuesen las primeras líneas de la transcripción, por lo que condiciona completamente el resultado.
    #   La que he puesto hace que detecte el lenguaje y haga una transcripción natural (si no, muchas veces autocorrige las frases para que sean gramaticalmente correctas).

    if not os.path.isfile(file_path):
        print(f"Error: archivo no encontrado - {file_path}")
        return

    print(f"Cargando modelo whisper ({model_size})...")
    model = whisper.load_model(model_size)

    print(f"Transcribiendo {file_path}...")
    result = model.transcribe(file_path, initial_prompt=initial_prompt)
    print(result["text"])
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
            respuesta= "Hola buenas, Me gustaría hacerte una serie de preguntas para asegurarme de que el producto sea un buen fit para mi empresa"
        else:
            respuesta = "No me saludaste wey. Me gustaría hacerte una serie de preguntas para asegurarme de que el producto sea un buen fit para mi empresa"
      
    if "adios" in palabras or "adiós" in palabras:
        respuesta = "Adios muy buenas"
        breaker = True

    if contador == 3: 
        respuesta = "Eso es todo lo que quería saber, muchas gracias!"
        breaker = True

    return (respuesta,breaker)

def conversacion(transcript):
    preguntas = [
        "Cual es el ROI esperado?",
        "Cuanto tiempo se tardaría en implementar la solucion?",
        "Como ha funcionado el producto en otras empresas?",
        ""
    ]

    i = 0
    while i < 4:
        archivo = grabar_audio(duracion=8)  # graba 8 segundos
        texto = transcribir_audio(file_path=archivo, model_size="small")  # puedes usar medium o large
        respuesta,breaker = respuesta_tree(texto,i)
        if breaker:
            print("\n--- Respuesta ---\n")
            print(respuesta)
            break
        respuesta += preguntas[i]
        print("\n--- Transcripción ---\n")
        print(texto)
        print("\n--- Respuesta ---\n")
        print(respuesta)
        transcript.append({"speaker": "vendedor", "text": texto})
        transcript.append({"speaker": "cliente", "text": respuesta})

        i += 1
    
    with open("transcript.txt", "w", encoding="utf-8") as f:
        for entrada in transcript:
            f.write(f"{entrada['speaker']}: {entrada['text']}\n")



if __name__ == "__main__":
    transcript = []
    conversacion(transcript)
