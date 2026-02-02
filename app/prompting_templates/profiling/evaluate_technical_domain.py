def evaluate_technical_domain(transcript) -> str:
  
    prompt = f"""
# CONTEXTO Y TAREA
Eres un experto en comunicación, negociación y ventas. Tu tarea es analizar una conversación entre un vendedor y su potencial cliente. A continuación encontrarás las pautas que debes seguir para dar una puntuación u otra, y después recibirás la transcripción de la conversaciónAnaliza la siguiente transcripción. En este caso, debes evaluar el DOMINIO TÉCNICO del vendedor sobre el producto o servicio que ofrece, en una escala del 1 al 5, evaluándolo en base a las siguientes pautas:

# RÚBRICA DETALLADA
## 5 – Dominio técnico avanzado
El vendedor cumple todas las siguientes condiciones:
- Describe características técnicas con detalle específico (funcionamiento, límites, condiciones).
- Traduce esas características en beneficios operativos o económicos concretos para el cliente.
- Utiliza datos verificables: cifras, porcentajes, tiempos, capacidades, comparaciones técnicas.
- Responde directamente a preguntas técnicas sin evasivas.

## 4 – Dominio técnico sólido
El vendedor cumple al menos 3 de las siguientes condiciones:
- Explica correctamente características técnicas relevantes.
- Relaciona esas características con beneficios para el cliente.
- Responde preguntas técnicas de forma correcta pero sin datos cuantitativos o ejemplos detallados.
- Usa ejemplos genéricos pero coherentes.

## 3 – Dominio técnico básico
El vendedor cumple al menos 1 de las siguientes condiciones:
- Enumera características técnicas correctas sin explicar su impacto en el cliente.
- Usa terminología técnica sin contextualizarla.
- Responde preguntas técnicas de forma superficial o incompleta.

## 2 – Dominio técnico insuficiente
El vendedor:
- Menciona características vagas o genéricas sin detalle técnico.
- No demuestra comprensión del funcionamiento del producto.
- Evita profundizar cuando surge un aspecto técnico.

## 1 – Sin dominio técnico
El vendedor:
- No menciona características técnicas identificables.
- No responde preguntas técnicas o deriva la respuesta a terceros.
- Usa únicamente valoraciones subjetivas sin contenido técnico.


# TRANSCRIPCIÓN DE LA CONVERSACIÓN A EVALUAR
{transcript}

# INSTRUCCIONES FINALES
Debes justificar brevemente tu puntuación con ejemplos concretos extraídos de la transcripción, y responder con una puntuación del 1 al 5 según las pautas anteriores. REGLA DE DESEMPATE: en caso de duda, si la evaluación cae entre dos puntuaciones de la rúbrica, el vendedor recibirá la puntuación inferior. Darás tu respuesta en formato JSON, ajustándote estrictamente a las siguientes instrucciones de formato:

# INSTRUCCIONES DE FORMATO (IMPORTANTE):
1. Responde en español empleando la segunda persona del singular.
2. Responde ÚNICAMENTE con un JSON válido.
3. NO uses bloques de código markdown (```json).
4. Si citas palabras de la transcripción en la justificación, USA COMILLAS SIMPLES ('ejemplo') en lugar de dobles para no romper el formato JSON.
5. Asegúrate de escapar cualquier comilla doble interna si es estrictamente necesario.
6. LONGITUD Y ESTILO: Nunca mas de 300 caracteres de longitud. La justificación debe ser un resumen ejecutivo, directo y profesional. MÁXIMO 2 oraciones o 40 palabras. Evita palabras de relleno.

El formato exacto es:
{{
  "justification": "Feedback con ejemplos de la transcripción que justifiquen la nota obtenida",
  "score": "numero entero indicando la puntuación segun la rubrica.",
}}
"""
    return prompt
