def clarity(transcript):
    prompt = f"""
    Actúa como un experto analista de comunicación y oratoria. Te mostraremos una transcripción de una conversacion y tu tarea es evaluar la "Claridad del Discurso" del vendedor.

    A continuación, recibirás una transcripción de una conversación en formato JSON.

    ### TUS INSTRUCCIONES:

    1.  **Identificar al objetivo:** Debes analizar únicamente las intervenciones del rol identificado como "vendedor" . Ignora la claridad del cliente, úsalo solo para contexto.
    2.  **Detectar falta de claridad:** Analiza cada intervención buscando:
        * **Ambigüedad:** Uso de términos vagos sin concretar.
        * **Desorganización:** Ideas desordenadas, digresiones innecesarias o "irse por las ramas".
        * **Frases inconclusas:** Oraciones que se cortan y cambian de tema abruptamente sin cerrar la idea anterior.
        * **Contradicciones:** Afirmaciones que chocan con lo dicho anteriormente en la misma intervención.
    3.  **Formato de Salida:** Tu respuesta debe ser ESTRICTAMENTE un objeto JSON válido. No añadas texto introductorio ni conclusiones fuera del JSON.

    ### ESTRUCTURA DEL JSON DE RESPUESTA:

    * `"señales"`: (String) Cita las frases textuales exactas entre comillas o resume brevemente el momento donde se perdió la claridad. Si hay varias, sepáralas por punto y coma. Si el valor de "Veces_falta_claridad" es 0, escribe exactamente "Ninguna".
    * `"veces_falta_claridad"`: (Int) Número total de veces que detectaste un problema de claridad. Si todo fue perfecto, pon 0.
    * `"feedback"`: (String) Proporciona consejos tácticos y directos para mejorar la claridad basándote en los errores encontrados. Si no hubo errores, felicita por la estructura clara.

    ### DATOS DE ENTRADA:

    Aquí está la transcripción de la conversación:

    {transcript}
    """
    return prompt