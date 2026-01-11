import math
from app.services.conversations_service import set_user_profile
from app.services.messages_service import get_user_profiling
# 1. Definimos los profilees base con sus "notas numéricas"
# (usamos escala: Bajo=1, Medio-Bajo=2, Medio=3, Medio-Alto=4, Alto=5)
profiles = {
    "Conector": {"prospection": 2, "empathy": 5, "technical_domain": 1, "negociation": 3, "resilience": 5},
    "Especialista": {"prospection": 1, "empathy": 1, "technical_domain": 5, "negociation": 3, "resilience": 3},
    "Cazador": {"prospection": 5, "empathy": 1, "technical_domain": 1, "negociation": 5, "resilience": 5},
    "Negociador": {"prospection": 3, "empathy": 3, "technical_domain": 4, "negociation": 5, "resilience": 3},
    "Vendedor Integral": {"prospection": 5, "empathy": 5, "technical_domain": 5, "negociation": 5, "resilience": 5},
    "Asistente": {"prospection": 2, "empathy": 5, "technical_domain": 1, "negociation": 1, "resilience": 2},
    "Consultor": {"prospection": 3, "empathy": 5, "technical_domain": 4, "negociation": 5, "resilience": 3},
    "Vendedor Persuasivo": {"prospection": 3, "empathy": 1, "technical_domain": 3, "negociation": 5, "resilience": 5},
    "Constructor de Relaciones": {"prospection": 2, "empathy": 5, "technical_domain": 1, "negociation": 1, "resilience": 3},
    "Emprendedor": {"prospection": 5, "empathy": 3, "technical_domain": 2, "negociation": 3, "resilience": 3}
}

async def user_clasiffier(user_id):
    """Clasifica un vendedor al profile más cercano basado en distancia euclidiana."""
    
    profiling = await get_user_profiling(user_id)
    input_vector = {
            "prospection": profiling.get('prospection_scoring') or None,
            "empathy": profiling.get('empathy_scoring') or None,
            "technical_domain": profiling.get('technical_domain_scoring') or None,
            "negociation": profiling.get('negotiation_scoring') or None,
            "resilience": profiling.get('resilience_scoring') or None,
        }
    # Obtenemos los valores numéricos del vector
    valores_scores = list(input_vector.values())
    
    if len(valores_scores) > 0:
        general_score = sum(valores_scores) / len(valores_scores)
    else:
        general_score = 0
     
    general_score = round(general_score, 2)
    
    best_profile = None
    menor_distancia = float("inf")
    
    for profile, valores in profiles.items():
        # calcular distancia euclidiana
        dist = math.sqrt(sum((input_vector[k] - valores[k])**2 for k in input_vector))
        
        if dist < menor_distancia:
            menor_distancia = dist
            best_profile = profile

    await set_user_profile(profiling.get('user_id'), general_score, best_profile)

