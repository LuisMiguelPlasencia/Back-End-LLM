from typing import Tuple
from .call_gpt_utils import call_gpt


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
