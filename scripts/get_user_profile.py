import math

# 1. Definimos los perfiles base con sus "notas numéricas"
# (usamos escala: Bajo=1, Medio-Bajo=2, Medio=3, Medio-Alto=4, Alto=5)
perfiles = {
    "Conector": {"prospeccion": 2, "empatia": 5, "dominio": 1, "negociacion": 3, "resiliencia": 5},
    "Especialista": {"prospeccion": 1, "empatia": 1, "dominio": 5, "negociacion": 3, "resiliencia": 3},
    "Cazador": {"prospeccion": 5, "empatia": 1, "dominio": 1, "negociacion": 5, "resiliencia": 5},
    "Negociador": {"prospeccion": 3, "empatia": 3, "dominio": 4, "negociacion": 5, "resiliencia": 3},
    "Vendedor Integral": {"prospeccion": 5, "empatia": 5, "dominio": 5, "negociacion": 5, "resiliencia": 5},
    "Asistente": {"prospeccion": 2, "empatia": 5, "dominio": 1, "negociacion": 1, "resiliencia": 2},
    "Consultor": {"prospeccion": 3, "empatia": 5, "dominio": 4, "negociacion": 5, "resiliencia": 3},
    "Vendedor Persuasivo": {"prospeccion": 3, "empatia": 1, "dominio": 3, "negociacion": 5, "resiliencia": 5},
    "Constructor de Relaciones": {"prospeccion": 2, "empatia": 5, "dominio": 1, "negociacion": 1, "resiliencia": 3},
    "Emprendedor": {"prospeccion": 5, "empatia": 3, "dominio": 2, "negociacion": 3, "resiliencia": 3}
}

def clasificar_vendedor(prospeccion, empatia, dominio, negociacion, resiliencia):
    """Clasifica un vendedor al perfil más cercano basado en distancia euclidiana."""
    input_vector = {
        "prospeccion": prospeccion,
        "empatia": empatia,
        "dominio": dominio,
        "negociacion": negociacion,
        "resiliencia": resiliencia
    }
    
    mejor_perfil = None
    menor_distancia = float("inf")
    
    for perfil, valores in perfiles.items():
        # calcular distancia euclidiana
        dist = math.sqrt(sum((input_vector[k] - valores[k])**2 for k in input_vector))
        
        if dist < menor_distancia:
            menor_distancia = dist
            mejor_perfil = perfil
    
    return mejor_perfil

if __name__ == "__main__":
    perfil = clasificar_vendedor(1, 1, 1, 1, 1)
    print("Perfil detectado:", perfil)
