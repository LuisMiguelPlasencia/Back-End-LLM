def goal(transcript, goal_description):
    prompt = f"""
    Vas a actuar como un auditor de ventas estricto e imparcial. Tu tarea es evaluar exclusivamente si el vendedor logra cumplir TODOS los parámetros del OBJETIVO PRINCIPAL basándote únicamente en lo que está explícitamente dicho en la transcripción.

    # INSTRUCCIONES:
    - REGLA DE ORO: El objetivo es un "Todo o Nada". Si el objetivo pide vender un producto X y el vendedor ofrece el producto Y, el objetivo NO se cumple. Si falta uno solo de los requisitos del objetivo, es false.
    - Intenciones, promesas futuras, evasivas o si el vendedor abandona la conversación (ej: "lo dejamos aquí"), equivale a NO cumplido.
    - Solo es true si hay confirmación verbal clara por ambas partes en la transcripción.

    # OBJETIVO PRINCIPAL: 
    {goal_description} 

    # TRANSCRIPCIÓN:
    {transcript}

    # FORMATO DE RESPUESTA (IMPORTANTE):
    1. Responde ÚNICAMENTE con un JSON válido.
    2. NO uses bloques de código markdown (```json).
    3. Si citas palabras, USA COMILLAS SIMPLES ('ejemplo'). Escapa comillas dobles si es necesario.
    4. ESTRUCTURA DEL JSON:
    - "analisis": (Máximo 40 palabras). Razona paso a paso si se cumplieron TODAS las partes del objetivo. Sé muy crítico.
    - "señales": (Máximo 30 palabras). Si es true, cita la frase exacta del cierre. Si es false, explica el fallo o cita la frase donde se pierde la venta.
    - "indicador": true o false (booleano).

    EJEMPLO DE RESPUESTA DE FRACASO:
    {{
    "analisis": "El vendedor no ofreció las 20 unidades de la 3500i ni el contrato de 2 años. Además, el vendedor abandonó la conversación sin dar argumentos técnicos válidos.",
    "señales": "Fracaso evidente. El vendedor se rinde diciendo: 'Yo lo dejaría aquí'.",
    "indicador": false
    }}
    """
    return prompt