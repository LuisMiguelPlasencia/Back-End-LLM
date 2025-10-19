import whisper
import sys
import os

'''
Enlaces de interés:
 - https://pypi.org/project/openai-whisper
 - https://platform.openai.com/docs/guides/speech-to-text/prompting#prompting
 - https://github.com/openai/whisper 
'''

def transcribe_audio(file_path: str, 
                     model_size: str = 'small', 
                     initial_prompt: str = 'Voy a contarte una cosa en español yyy... emmm.. igual a veces no me expreso muy bien, pero bueno, no pasaría nada, ¿eh?.'):
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

    print("\n--- Transcripción ---")
    print(result["text"])
    return result["text"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Modo de uso: python voice-to-text.py <ruta_archivo_audio> [tamaño_modelo]")
    else:
        audio_path = sys.argv[1]
        model_size = sys.argv[2] if len(sys.argv) > 2 else "small" 
        transcribe_audio(audio_path, model_size)