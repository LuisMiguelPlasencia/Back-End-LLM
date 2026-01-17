def participation(transcript):
    prompt = f"""
    Eres un experto en comunicación y negociación. Tu tarea es analizar la transcripción de una conversación entre un vendedor y su potencial cliente. 
    
    # OBJETIVO:
    Detectar si el vendedor INTERRUMPIÓ al cliente de forma abrupta, cortando su flujo de pensamiento.
    
    # CRITERIO DE EXIGENCIA:
    - Diferencia entre un "asentimiento" (cooperativo) y una INTERRUPCIÓN (negativo).
    - Marca como falta si el cliente estaba hablando y tú entraste a hablar antes de que terminara su idea, pisando su audio.
    - Si la conversación fue fluida y respetuosa, no inventes interrupciones.

    # TRANSCRIPCIÓN:
    {transcript}

    # INSTRUCCIONES DE FORMATO (IMPORTANTE):
    1. Responde SIEMPRE en español usando la segunda persona del singular (ej: "interrumpiste", "cortaste", "respetaste").
    2. Responde ÚNICAMENTE con un JSON válido.
    3. NO uses bloques de código markdown.
    4. Usa COMILLAS SIMPLES para citar texto de la transcripción.
    5. "hubo_interrupcion" debe ser un booleano (true/false) sin comillas.

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
    {{
     "señales": "Cita el momento exacto donde el vendedor interrumpió al cliente (ej: 'El cliente decía X y lo cortaste diciendo Y'). En caso de no haber interrupciones, pon 'Ninguna'",
     "hubo_interrupcion": true/false,
     "feedback": "Si es TRUE: Aconseja dejar terminar las frases (ej: 'Deja que el cliente termine antes de rebatir'). Si es FALSE: Felicita por respetar los turnos de palabra. Habla en segunda persona."
    }}
    """
    
    return prompt