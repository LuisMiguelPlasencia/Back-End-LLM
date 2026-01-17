def goal(transcript, goal_description):
    prompt = f"""
    Vas a analizar la transcripción de una conversación comercial entre un vendedor y un cliente.
    Tu tarea es evaluar exclusivamente si el vendedor logra cumplir el OBJETIVO PRINCIPAL, basándote únicamente en lo que está explícitamente dicho en la transcripción.

    # INSTRUCCIONES:
        -El objetivo solo se considera cumplido si el vendedor lo ejecuta de forma clara, directa y verificable dentro de la conversación.
        -Intenciones, promesas futuras, suposiciones o respuestas ambiguas NO cuentan como cumplimiento del objetivo.
        -Si el cliente acepta algo pero el vendedor no realiza la acción correspondiente, el objetivo NO se considera cumplido.
        -Si el objetivo se cumple, debes identificar exactamente la intervención del vendedor (frase literal) que demuestra dicho cumplimiento.
        -Si no se cumple, el indicador debe ser false y las señales deben explicar brevemente por qué no hay evidencia suficiente.

    # OBJETIVO PRINCIPAL: 
    {goal_description} 

    # TRANSCRIPCIÓN:
    {transcript}
    
    # FORMATO DE RESPUESTA (IMPORTANTE):
    1. Responde ÚNICAMENTE con un JSON válido.
    2. NO uses bloques de código markdown (```json).
    3. Si citas palabras de la transcripción en la justificación, USA COMILLAS SIMPLES ('ejemplo') en lugar de dobles para no romper el formato JSON.
    4. Asegúrate de escapar cualquier comilla doble interna si es estrictamente necesario.
    5. LONGITUD Y ESTILO: Nunca mas de 300 caracteres de longitud. La justificación debe ser un resumen ejecutivo, directo y profesional. MÁXIMO 2 oraciones o 40 palabras. Evita palabras de relleno.

        RESPONDE ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
        {{
        "señales": "Indica la intervención en la que el vendedor cumple el objetivo, acompañado de la frase exacta. Por ejemplo: '¡Fantástico! Le acabo de enviar un enlace seguro a su correo... . Se lo más breve y conciso posible'. Habla en segunda persona." ,
        "indicador": true/false, 
        }}
        """

    return prompt