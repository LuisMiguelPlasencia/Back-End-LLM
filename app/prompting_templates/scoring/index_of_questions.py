def index_of_questions(transcript):
    prompt = f"""
    Actúa como un experto en comunicación y negociación. Estás analizando una llamada para darle feedback DIRECTO al vendedor.
    
    # TU OBJETIVO:
    Analiza la transcripción adjunta donde participan un "Vendedor" y un cliente. Debes dirigirte al "Vendedor" como "tú". Identifica las preguntas del vendedor y clasifícalas.

    # TRANSCRIPCIÓN:
    {transcript}

    # INSTRUCCIONES DE FORMATO (IMPORTANTE):
    1. Responde SIEMPRE en español empleando la segunda persona del singular (ej: "hiciste", "preguntaste", "deberías").
    2. NUNCA te refieras al usuario como "el vendedor", refiérete a él como "tú".
    3. Responde ÚNICAMENTE con un JSON válido.
    4. NO uses bloques de código markdown (```json).
    5. Si citas palabras de la transcripción, USA COMILLAS SIMPLES ('ejemplo') para no romper el JSON.
    6. LONGITUD: Feedback máximo de 2 oraciones o 40 palabras. Directo y al grano.

    # Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato:
    {{
     "señales": "Lista breve de momentos clave donde identificas estos tipos de preguntas",
     "n_total": "número entero con el total de preguntas que hiciste (tú, el vendedor)",
     "n_cerradas": "número entero con tus preguntas cerradas",
     "n_sondeo": "número entero con tus preguntas de sondeo", 
     "n_irrelevantes": "número entero con tus preguntas irrelevantes",
     "feedback": "Háblale directamente al vendedor (tú) y explícale qué preguntas sobraron o cómo formular mejor las siguientes para tener más impacto. Sé crítico pero constructivo. Usa ejemplos concretos."
    }}
    """
    return prompt