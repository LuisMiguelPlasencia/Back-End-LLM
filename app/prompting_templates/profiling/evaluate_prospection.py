from typing import Tuple
from .call_gpt_utils import call_gpt


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
