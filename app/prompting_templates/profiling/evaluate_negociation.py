def evaluate_negociation(transcript) -> str:
  
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
  "justification": "Feedback con ejemplos de la transcripción que justifiquen la nota obtenida",
  "score": "numero entero indicando la puntuación segun la rubrica.",
}}

"""
    return prompt
