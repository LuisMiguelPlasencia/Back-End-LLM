def active_listening(transcript):
    prompt = f"""
    # CONTEXTO
    Eres un experto en comunicación y negociación. Tu tarea es analizar una conversación entre un vendedor y su potencial cliente para medir la calidad de la escucha del vendedor.

    ## TU OBJETIVO:
    Detectar las interacciones, si las hay, en las que el vendedor demuestra ESCUCHA ACTIVA genuina.
    
    ## CRITERIO DE EXIGENCIA:
    - NO cuentes simples confirmaciones o muletillas como "sí", "ajá", "vale", "correcto". Eso es escucha pasiva.
    - Para contar como punto, tuviste que haber REPETIDO o PARAFRASEADO lo que dijo el cliente para confirmar que lo entendiste (por ejemplo: "Si te he entendido bien, lo que te preocupa es...").

    # TRANSCRIPCIÓN (analízala atentamente en base a los criterios anteriores):
    {transcript}

    Ahora que la has analizado, debes dar una respuesta siguiendo las instrucciones a continuación:

    # INSTRUCCIONES DE FORMATO (IMPORTANTE):
    1. Responde SIEMPRE en español usando la segunda persona del singular (ej: "parafraseaste", "validaste", "repetiste").
    2. Responde ÚNICAMENTE con un JSON válido.
    3. NO uses bloques de código markdown.
    4. Usa COMILLAS SIMPLES para citar texto de la transcripción.
    5. Escapa comillas dobles internas si es necesario.
    6. LONGITUD: Máximo 40 palabras. Sé directo.

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
    {{
     "n": "número entero con la cantidad de veces que hiciste escucha activa (parafraseo/validación)",
     "señales": "Justifica brevemente. Si hubo escucha activa, cita el momento (ej: 'Parafraseaste su queja sobre el precio'). Si la cuenta es 0, explica por qué (ej: 'Solo respondiste con monosílabos sin validar la información')."
    }}
    """
    
    return prompt
