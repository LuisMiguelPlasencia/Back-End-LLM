def evaluate_resilience(transcript) -> str:

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
    return prompt
