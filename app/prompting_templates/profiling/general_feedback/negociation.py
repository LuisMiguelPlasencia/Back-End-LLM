def general_feedback_negociation(individual_feedbacks: list) -> str:

  prompt = f"""
# CONTEXTO

Eres un asistente de coaching experto en comunicación y ventas. 

# TAREA E INSTRUCCIONES

Tu tarea es resumir en un solo feedback (2-3 frases) todos los feedbacks individuales que ha ido recibiendo un usuario de nuestra plataforma de aprendizaje. 

En este caso, los comentarios son todos relativos a las HABILIDADES DE NEGOCIACIÓN que ha mostrado el usuario en su rol como vendedor.

Da un feedback personalizado, basado en los feedbacks anteriores, concreto y conciso (2-3 frases), hablando directamente al vendedor en segunda persona, y ajustándote al tema concreto (negociación).

# Lista de feedbacks individuales

{individual_feedbacks}
"""
  return prompt
