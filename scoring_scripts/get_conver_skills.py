# KPIs Perfil
import re 
import subprocess
import json
from typing import List, Dict, Tuple
import sys
import os 
from dotenv import load_dotenv

sys.path.insert(0, "../../src")
load_dotenv()
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
from openai import OpenAI

client = OpenAI(api_key=OPENAI_TOKEN)

def call_gpt(prompt: str) -> str:
    response = client.responses.create(
        model="gpt-4.1-nano-2025-04-14",
        input=prompt,
        
    )
    return response.output_text


## 1. Prospección
def evaluate_prospection(transcript) -> Tuple[int, str]:
  
    prompt = f"""
Analiza la siguiente transcripción de una llamada de ventas y evalúa la PROSPECCIÓN del vendedor según esta rúbrica:

ALTA (5 puntos): El vendedor demuestra investigación previa específica y relevante sobre el cliente, la empresa o la situación. Ejemplos: menciona artículos, publicaciones en LinkedIn, eventos recientes, hitos de la empresa, ascensos de personas clave.

MEDIO-ALTO (4 puntos): El vendedor personaliza parcialmente su aproximación, muestra cierto contexto del cliente, pero no llega a un nivel de investigación profunda. Ejemplos: referencia a la industria del cliente, tendencias generales del sector, retos habituales en su tipo de empresa.

MEDIA (3 puntos): El vendedor hace preguntas generales de descubrimiento, sin personalización ni conexión con información previa. Ejemplos: "cuéntame sobre tu empresa", "qué retos enfrentan", "qué soluciones usan".

MEDIO-BAJO (2 puntos): El vendedor hace preguntas mínimas o muy superficiales antes de pasar al pitch, con escasa exploración real. Ejemplos: "ustedes trabajan con software, ¿verdad?", "entiendo que usan herramientas digitales".

BAJA (1 punto): El vendedor va directo al pitch sin fase de descubrimiento ni interés por conocer al cliente. Ejemplos: "te llamo para presentar nuestro producto", "permíteme explicarte las ventajas".


TRANSCRIPCIÓN:
{transcript}

Responde ÚNICAMENTE devolviendo un JSON válido, sin texto adicional, sin markdown y sin explicaciones fuera del JSON, con el siguiente formato exacto:

{{
  "score": "numero entero indicando la puntuación segun la rubrica.",
  "justification": "Explicación específica con ejemplos de la transcripción"
}}
"""
    output = call_gpt(prompt)
    
    return output
    
## 2. Empatía
def evaluate_empathy(transcript) -> Tuple[int, str]:
  
    prompt = f"""
Analiza la siguiente transcripción y evalúa la EMPATÍA del vendedor:

**ALTA (5 puntos)**: Valida activamente emociones del cliente, demuestra escucha genuina, parafrasea lo dicho, usa frases como "entiendo perfectamente tu preocupación", "si te entiendo bien", "te agradezco que seas sincero". Muestra comprensión profunda y conexión emocional.

**MEDIA-ALTA (4 puntos)**: Valida emociones y preocupaciones del cliente, demuestra escucha activa, usa lenguaje empático, pero puede ser menos consistente o profundo.

**MEDIA (3 puntos)**: Validación genérica o superficial. Respuestas como "ok, entiendo", "claro", "sí, es importante" pero sin profundizar.

**MEDIA-BAJA (2 puntos)**: Poca validación emocional, respuestas mecánicas, no demuestra comprensión de las preocupaciones del cliente.

**BAJA (1 punto)**: Ignora preocupaciones, interrumpe frecuentemente, descarta objeciones con frases como "el precio no es problema", "sí, pero déjame decirte", "volviendo al tema".

TRANSCRIPCIÓN:
{transcript}

Presta especial atención a:
- ¿El vendedor interrumpe al cliente?
- ¿Valida las preocupaciones antes de responder?
- ¿Usa un lenguaje empático y de comprensión?

Responde ÚNICAMENTE devolviendo un JSON válido, sin texto adicional, sin markdown y sin explicaciones fuera del JSON, con el siguiente formato exacto:

{{
  "score": "numero entero indicando la puntuación segun la rubrica.",
  "justification": "Explicación específica con ejemplos de la transcripción"
}}
"""
    text = call_gpt(prompt)
    return text
    
## 3. Dominio técnico
def evaluate_technical_domain(transcript) -> Tuple[int, str]:
  
    prompt = f"""
Analiza la siguiente transcripción y evalúa el DOMINIO TÉCNICO del vendedor:

**ALTA (5 puntos)**: Traduce características técnicas en beneficios específicos para el cliente con ejemplos concretos. Responde con confianza a preguntas técnicas complejas, usa datos específicos y métricas. Ejemplos: "nuestra batería dura 12 horas, lo que significa que tus clientes no tendrán que recargarla durante un vuelo transatlántico", "la tecnología X reduce el procesamiento en 30%, permitiéndote ahorrar costes operativos".

**MEDIA-ALTA (4 puntos)**: Conecta características técnicas con beneficios del cliente, responde bien a preguntas técnicas, pero puede ser menos específico en ejemplos o métricas.

**MEDIA (3 puntos)**: Menciona características técnicas pero sin conectarlas claramente con beneficios específicos para el cliente. Ejemplos: "tiene batería de 12 horas", "es resistente al agua", "utiliza tecnología X".

**MEDIA-BAJA (2 puntos)**: Menciona algunas características básicas pero sin profundidad técnica o conexión con beneficios.

**BAJA (1 punto)**: No menciona características específicas o no puede responder preguntas técnicas. Ejemplos: "es muy bueno", "funciona bien", "déjame preguntar a mi superior".

TRANSCRIPCIÓN:
{transcript}

Evalúa si el vendedor:
- Conoce las características técnicas del producto
- Las conecta con beneficios específicos
- Responde con confianza a preguntas técnicas

Responde ÚNICAMENTE devolviendo un JSON válido, sin texto adicional, sin markdown y sin explicaciones fuera del JSON, con el siguiente formato exacto:

{{
  "score": "numero entero indicando la puntuación segun la rubrica.",
  "justification": "Explicación específica con ejemplos de la transcripción"
}}
"""
    output = call_gpt(prompt)
    
    return output
    
## 4. Negociación
def evaluate_negociation(transcript) -> Tuple[int, str]:
  
    prompt = f"""
Analiza la siguiente transcripción y evalúa la NEGOCIACIÓN del vendedor:

**BUENA (5 puntos)**: Aborda objeciones justificando el valor con argumentos sólidos, es firme pero flexible en condiciones, propone próximos pasos claros y específicos. Maneja múltiples objeciones de forma constructiva. Ejemplos: "entiendo que el precio es superior, pero es una inversión que se justifica por el ahorro a largo plazo", "podríamos ajustar las condiciones de pago en cuotas", "el siguiente paso sería programar una demo con tu equipo técnico".

**MEDIA-BUENA (4 puntos)**: Aborda objeciones justificando el valor, propone próximos pasos, pero puede ser menos específico o flexible en las condiciones.

**MEDIA (3 puntos)**: Aborda algunas objeciones pero puede ceder demasiado pronto o no justificar adecuadamente el valor.

**MEDIA-BAJA (2 puntos)**: Evita objeciones o cede demasiado pronto, ofrece descuentos sin que se los pidan, no propone próximos pasos claros. Ejemplos: "el precio es negociable", "te mando la propuesta otra vez", "veo si puedo ofrecerte descuento".

**BAJA (1 punto)**: Se rinde ante la primera objeción, no intenta cerrar, deja decisión en manos del cliente. Ejemplos: "avísame si te interesa", "llámame si te decides", "no te preocupes, lo entiendo".

TRANSCRIPCIÓN:
{transcript}

Evalúa:
- ¿Cómo maneja las objeciones?
- ¿Justifica el valor o solo ofrece descuentos?
- ¿Propone próximos pasos concretos?

Responde ÚNICAMENTE devolviendo un JSON válido, sin texto adicional, sin markdown y sin explicaciones fuera del JSON, con el siguiente formato exacto:

{{
  "score": "numero entero indicando la puntuación segun la rubrica.",
  "justification": "Explicación específica con ejemplos de la transcripción"
}}

"""
    output = call_gpt(prompt)
    
    return output
    
## 5. Resiliencia
def evaluate_resilience(transcript) -> Tuple[int, str]:

    prompt = f"""
Analiza la siguiente transcripción y evalúa la RESILIENCIA del vendedor:

**BUENA (5 puntos)**: Mantiene tono positivo y enérgico durante toda la llamada, se recupera rápidamente de objeciones, usa lenguaje constructivo y motivador. Mantiene energía constante incluso tras múltiples objeciones. Ejemplos: "aprecio tu franqueza, permíteme explicarte", mantiene energía constante incluso tras objeciones de precio.

**MEDIA-BUENA (4 puntos)**: Mantiene tono positivo la mayor parte del tiempo, se recupera bien de objeciones, pero puede tener pequeñas fluctuaciones de energía.

**MEDIA (3 puntos)**: El tono puede bajar ligeramente tras objeciones, pequeñas pausas o disminución de energía, pero se recupera y mantiene profesionalismo.

**MEDIA-BAJA (2 puntos)**: Muestra signos de frustración o cansancio, el tono baja notablemente tras objeciones, pero aún intenta continuar.

**BAJA (1 punto)**: Muestra frustración evidente, tono negativo o pasivo, se rinde fácilmente. Ejemplos: suspiros audibles, "entiendo, si no te interesa no pasa nada" con tono monótono.

TRANSCRIPCIÓN:
{transcript}

Presta atención a:
- ¿Mantiene un tono consistente durante toda la llamada?
- ¿Cómo responde a objeciones o rechazos?
- ¿Se detectan cambios de energía o frustración?
- ¿Termina la llamada con próximos pasos o se rinde?

Responde ÚNICAMENTE devolviendo un JSON válido, sin texto adicional, sin markdown y sin explicaciones fuera del JSON, con el siguiente formato exacto:

{{
  "score": "numero entero indicando la puntuación segun la rubrica.",
  "justification": "Explicación específica con ejemplos de la transcripción"
}}
"""
    output = call_gpt(prompt) 
    
    return output

async def get_conver_skills(transcript: str) -> Dict[str, Dict[str, str]]:
    """
    Evalúa un transcript en todas las skills definidas.
    Devuelve un diccionario con las puntuaciones y justificaciones.
    """

    prospection = json.loads(evaluate_prospection(transcript))
    empathy = json.loads(evaluate_empathy(transcript))
    technical_domain = json.loads(evaluate_technical_domain(transcript))
    negociation = json.loads(evaluate_negociation(transcript))
    resilience = json.loads(evaluate_resilience(transcript))

    scores = {
        "prospection": prospection["score"], 
        "empathy": empathy["score"],
        "technical_domain": technical_domain["score"],
        "negociation": negociation["score"],
        "resilience": resilience["score"],
    }

    feedback = {
        "prospection": prospection["justification"],
        "empathy": empathy["justification"],
        "technical_domain": technical_domain["justification"],
        "negociation": negociation["justification"],
        "resilience": resilience["justification"],
    }

    return {
        "scores": scores, 
        "feedback": feedback
    }

if __name__ == "__main__":
    transcript_demo = """
    V: Hola, ¿eh? Soy Ricardo. Mira, mi empresa ayuda a reducir el error de hemólisis en un 60%...
    C: Es una buena pregunta. El reprocesamiento nos cuesta tiempo y reactivos, calculo unos 50€ por caso...
    """

    resultados = get_conver_skills(transcript_demo)
    print(resultados)
