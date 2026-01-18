from typing import Tuple
from .call_gpt_utils import call_gpt


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
