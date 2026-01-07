import math

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

def user_clasiffier(prospection, empathy, technical_domain, negociation, resilience):
    """Clasifica un vendedor al profile más cercano basado en distancia euclidiana."""
    input_vector = {
        "prospection": prospection,
        "empathy": empathy,
        "technical_domain": technical_domain,
        "negociation": negociation,
        "resilience": resilience
    }
    
    best_profile = None
    menor_distancia = float("inf")
    
    for profile, valores in profiles.items():
        # calcular distancia euclidiana
        dist = math.sqrt(sum((input_vector[k] - valores[k])**2 for k in input_vector))
        
        if dist < menor_distancia:
            menor_distancia = dist
            best_profile = profile
    
    return best_profile

