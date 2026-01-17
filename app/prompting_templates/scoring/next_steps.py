def next_steps(transcript):
    prompt = f"""
    Actúa como un "Sales Coach" experto en cierres de venta. Analiza el desenlace de esta conversación.
    
    TU OBJETIVO:
    Determinar si el vendedor (al que te dirigirás como "tú") estableció "Próximos Pasos" CONCRETOS antes de colgar.
    
    CRITERIO DE EXIGENCIA:
    Para marcar "true", NO basta con una despedida educada o un vago "ya vamos hablando". 
    Tuviste que haber propuesto una acción específica: agendar fecha/hora, enviar un presupuesto, programar una demo o definir quién contactará a quién y cuándo. Si no hay compromiso claro, es "false".

    TRANSCRIPCIÓN:
    {transcript}

    INSTRUCCIONES DE FORMATO (IMPORTANTE):
    1. Responde SIEMPRE en español usando la segunda persona del singular (ej: "propusiste", "agendaste", "olvidaste").
    2. Responde ÚNICAMENTE con un JSON válido.
    3. NO uses bloques de código markdown.
    4. Usa COMILLAS SIMPLES para citar texto de la transcripción.
    5. "indicador" debe ser un booleano puro (true/false) sin comillas.

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
    {{
     "indicador": true/false, 
     "señales": "Si es TRUE: Resume qué paso concreto propusiste (ej: 'Propusiste una reunión para el martes'). Si es FALSE: Indica brevemente qué faltó (ej: 'Te despediste sin concretar fecha para el siguiente contacto'). Máximo 40 palabras."
    }}
    """
    return prompt