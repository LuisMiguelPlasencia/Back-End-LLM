def key_themes(transcript, key_themes_list):
    # Fetch key themes for the course/stage; returns a string or None
    
    prompt = f"""
    Actúa como un experto en comunicación y negociación. Estás evaluando el desempeño de un vendedor basándote en la transcripción de su llamada.
    
    # TU OBJETIVO:
    Determinar si el vendedor (al que te dirigirás como "tú") cubrió los TEMAS CLAVE obligatorios.
    
    # CRITERIO DE EXIGENCIA: 
    Para considerar un tema como "abordado", NO basta con mencionar la palabra clave. Tuviste que haber desarrollado un mínimo argumento sobre ello. 

    # TEMAS CLAVE: 
    {key_themes_list}

    # TRANSCRIPCIÓN:
    {transcript}

    # FORMATO DE TU RESPUESTA
    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato:
    {{"n_temas_abordados": "numero entero mencionando el numero de temas clave abordados",
      "n_temas_olvidados": "numero entero mencionando el numero de temas clave olvidados",
     "señales": "Señales donde se identifican temas claves abordados. Se lo más breve y conciso posible",
     "feedback": "Temas claves que no se han abordado. Se lo más breve y conciso posible. Habla en segunda persona. Si se abordaron todos los temas, felicita por la cobertura completa."}}
    """
    return prompt