# KPIs Perfil
import re 
import subprocess
import json
from typing import List, Dict, Tuple, Any
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

INSTRUCCIONES DE FORMATO (IMPORTANTE):
1. Responde en español empleando la segunda persona del singular.
2. Responde ÚNICAMENTE con un JSON válido.
3. NO uses bloques de código markdown (```json).
4. Si citas palabras de la transcripción en la justificación, USA COMILLAS SIMPLES ('ejemplo') en lugar de dobles para no romper el formato JSON.
5. Asegúrate de escapar cualquier comilla doble interna si es estrictamente necesario.
6. LONGITUD Y ESTILO: Nunca mas de 300 caracteres de longitud. La justificación debe ser un resumen ejecutivo, directo y profesional. MÁXIMO 2 oraciones o 40 palabras. Evita palabras de relleno.

El formato exacto es:
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

INSTRUCCIONES DE FORMATO (IMPORTANTE):
1. Responde en español empleando la segunda persona del singular.
2. Responde ÚNICAMENTE con un JSON válido.
3. NO uses bloques de código markdown (```json).
4. Si citas palabras de la transcripción en la justificación, USA COMILLAS SIMPLES ('ejemplo') en lugar de dobles para no romper el formato JSON.
5. Asegúrate de escapar cualquier comilla doble interna si es estrictamente necesario.
6. LONGITUD Y ESTILO: Nunca mas de 300 caracteres de longitud. La justificación debe ser un resumen ejecutivo, directo y profesional. MÁXIMO 2 oraciones o 40 palabras. Evita palabras de relleno.

El formato exacto es:

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

INSTRUCCIONES DE FORMATO (IMPORTANTE):
1. Responde en español empleando la segunda persona del singular.
2. Responde ÚNICAMENTE con un JSON válido.
3. NO uses bloques de código markdown (```json).
4. Si citas palabras de la transcripción en la justificación, USA COMILLAS SIMPLES ('ejemplo') en lugar de dobles para no romper el formato JSON.
5. Asegúrate de escapar cualquier comilla doble interna si es estrictamente necesario.
6. LONGITUD Y ESTILO: Nunca mas de 300 caracteres de longitud. La justificación debe ser un resumen ejecutivo, directo y profesional. MÁXIMO 2 oraciones o 40 palabras. Evita palabras de relleno.

El formato exacto es:
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

INSTRUCCIONES DE FORMATO (IMPORTANTE):
1. Responde ÚNICAMENTE con un JSON válido.
2. NO uses bloques de código markdown (```json).
3. Si citas palabras de la transcripción en la justificación, USA COMILLAS SIMPLES ('ejemplo') en lugar de dobles para no romper el formato JSON.
4. Asegúrate de escapar cualquier comilla doble interna si es estrictamente necesario.
5. LONGITUD Y ESTILO: La justificación debe ser un resumen ejecutivo, directo y profesional. MÁXIMO 2 oraciones o 40 palabras. Evita palabras de relleno.

El formato exacto es:
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

INSTRUCCIONES DE FORMATO (IMPORTANTE):
1. Responde ÚNICAMENTE con un JSON válido.
2. NO uses bloques de código markdown (```json).
3. Si citas palabras de la transcripción en la justificación, USA COMILLAS SIMPLES ('ejemplo') en lugar de dobles para no romper el formato JSON.
4. Asegúrate de escapar cualquier comilla doble interna si es estrictamente necesario.
5. LONGITUD Y ESTILO: La justificación debe ser un resumen ejecutivo, directo y profesional. MÁXIMO 2 oraciones o 40 palabras. Evita palabras de relleno.

El formato exacto es:
{{
  "score": "numero entero indicando la puntuación segun la rubrica.",
  "justification": "Explicación específica con ejemplos de la transcripción"
}}
"""
    output = call_gpt(prompt) 
    
    return output

async def get_conver_skills(transcript: str) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates a transcript across all defined skills.
    Returns a dictionary structured by skill containing score and justification.
    
    Return format:
    {
        "skill_name": { "score": int, "justification": str },
        ...
    }
    """

    # Helper function to prevent JSON errors from crashing the app
    def safe_parse_json(json_str: str, skill_name: str) -> Dict[str, Any]:
        try:
            if not json_str:
                raise ValueError("Empty response from AI")
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"⚠️ Error decoding JSON for {skill_name}: {e}")
            # Return default values so the code doesn't break downstream
            return {"score": 0, "justification": "Error during AI evaluation"}

    # Note: If your evaluate functions are async, remember to add 'await'
    # e.g., await evaluate_prospection(transcript)
    
    # We parse each result safely
    prospection_data = safe_parse_json(evaluate_prospection(transcript), "prospection")
    empathy_data = safe_parse_json(evaluate_empathy(transcript), "empathy")
    technical_domain_data = safe_parse_json(evaluate_technical_domain(transcript), "technical_domain")
    negociation_data = safe_parse_json(evaluate_negociation(transcript), "negociation")
    resilience_data = safe_parse_json(evaluate_resilience(transcript), "resilience")

    # We return the structure exactly as the consumer function expects it
    # (Keys are the skill names, containing both score and justification)
    return {
        "prospection": prospection_data,
        "empathy": empathy_data,
        "technical_domain": technical_domain_data,
        "negociation": negociation_data,
        "resilience": resilience_data,
    }

