def next_steps(transcript):
    prompt = f"""
    Eres un experto en comunicación y negociación. Tu tarea es analizar la transcripción de una conversación entre un vendedor y su potencial cliente.
    
    # TU OBJETIVO:

    Determinar si el vendedor (al que te dirigirás como "tú") estableció "Próximos Pasos" CONCRETOS antes de colgar.
    
    # CRITERIO DE EXIGENCIA:
    
    Para considerar que el vendedor ha cumplido su objetivo, NO basta con una despedida educada o un vago "ya vamos hablando". Tuvo que haber propuesto una acción específica: agendar fecha/hora, enviar un presupuesto, programar una demo o definir quién contactará a quién y cuándo. Si no hay compromiso claro, no lo des por conseguido.

    # TRANSCRIPCIÓN:
    
    {transcript}

    # INSTRUCCIONES DE FORMATO (IMPORTANTE):

    1. Responde SIEMPRE en español usando la segunda persona del singular (ej: "propusiste", "agendaste", "olvidaste").
    2. Responde ÚNICAMENTE con un JSON válido.
    3. NO uses bloques de código markdown.
    4. Usa COMILLAS SIMPLES para citar texto de la transcripción.
    5. "indicador" debe ser un booleano puro (true/false) sin comillas.

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
    
    {{
     "señales": "En caso de existir señales de próximos pasos por parte del vendedor, resúmelos (ej: 'Propusiste una reunión para el martes'). Si no, indica brevemente qué faltó (ej: 'Te despediste sin concretar fecha para el siguiente contacto'). Máximo 40 palabras.",
     "indicador": true/false, 
     }}
    """
    return prompt