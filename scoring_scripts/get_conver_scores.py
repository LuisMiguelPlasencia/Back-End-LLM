# KPIs & Scoring function

## KPIs
from collections import Counter
import string
import re
import numpy as np
import sys
from dotenv import load_dotenv
import os 
from openai import OpenAI
from wordfreq import zipf_frequency
import pandas as pd

sys.path.insert(0, "../../src")
load_dotenv()
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")

client = OpenAI(api_key=OPENAI_TOKEN)

def call_gpt(prompt: str) -> str:
    response = client.responses.create(
        model="gpt-5-nano",
        input=prompt,
        
    )
    return response.output_text

def escucha_activa(transcript):

    prompt = f"""
    Te voy a pasar la transcripcion de una conversación, presta atención a lo siguiente: Tienes que contar el número de veces en las que el vendedor ha realizado una escucha activa sobre lo que menciona el cliente. Se exigente, puede no haber escuchas activas en una conversacion. Una escucha activa se caracteriza por la repetición o parafraseo de la intervención del otro interlocutor. 

    TRANSCRIPCIÓN:
    {transcript}

    Responde ÚNICAMENTE devolviendo: 
    - Número de veces que ha habido escucha activa (devuelve un numero entero)
    - Señales de escucha activa
    """
    output = call_gpt(prompt)
    
    return output

def proximos_pasos(transcript):
    prompt = f"""
    Te voy a pasar la transcripcion de una conversación, presta atención a lo siguiente: Tienes que identificar si el vendedor al final de la conversación ha establecido o hablado de unos próximos pasos en la interacción con el cliente. Se exigente, puede que el vendedor no mencione nada acerca de próximos pasos. 

    TRANSCRIPCIÓN:
    {transcript}

    Responde ÚNICAMENTE devolviendo: 
    - Un booleano que indique si ha habido una formulación de los siguientes pasos
    - Señales de proximos pasos
    """
    output = call_gpt(prompt)
    
    return output

def temas_clave(transcript):
    prompt = f"""
    Te voy a pasar la transcripcion de una conversación, presta atención a lo siguiente: Tienes que identificar si el vendedor habla acerca de los temas clave que te voy a mandar. Se exigente, hablar de un tema clave no implica solamente mencionar dicha palabra, debe haber un pequeño desarrollo. 

    TRANSCRIPCIÓN:
    {transcript}

    TEMAS CLAVE: 
    Precio (que nuestro precio está por debajo de la competencia), Seguridad (Hemos ganado premios de seguridad), Espacio (somos el único vehículo con 5 asientos), combustible (hablar de que consume menos de 5L por cada 100km), capacidad maletero (mayor que la media de la competencia), llantas (modelo muy atractivo)


    Responde ÚNICAMENTE devolviendo: 
    - Un numero entero mencionando el número de temas clave abordados
    - Para cada tema clave abordado, señalar donde lo has identificado
    """
    output = call_gpt(prompt)
    
    return output

# def calcular_muletillas(transcript):

#     # Contar muletillas y pausas
#     total_muletillas = int(muletillas_gpt(transcript))

#     penalizacion = total_muletillas 

#     puntuacion = max(0, 100 - penalizacion)  # nunca bajar de 0

#     return  {
#         "puntuacion": puntuacion, 
#         "penalizacion": penalizacion,
#     }

# def calcular_claridad(transcript):
#     return {
#         "puntuacion": 50
#     }

# ### Muletillas
def calcular_muletillas(transcript, duracion=None, muletillas=None):
    if muletillas is None:
        muletillas = ["eh", "ehh", "ehhh", "ehhhh", "ehhhhh", "he", "hee", "ehm", "ehmm", "em", "emm", "emmm", "emmmm", "eeem", "eeemm", "e-eh", "hem", "hemm", "uh", "uhh", "uhhh", "uhhhh", "uhhhhh", "uhm", "uhmm", "umm", "ummm", "ummmm", "umh", "hum", "humm", "hummm", "humn", "mmm", "mmmm", "mmmmm", "mmmh", "mmmhh", "mmh", "mm-hm", "mhm", "m-hm", "mjm", "mjum", "m-jm", "ajá", "aja", "ahá", "aha", "aham", "ajam", "ah", "ahh", "ahhh", "ahhhh", "ahhhhh", "oh", "ohh", "ohhh", "ohhhh", "ooh", "oooh", "oho", "o-oh", "wow", "wooo", "wooow", "wou", "wow", "guau", "guaau", "ala", "alaaa", "hala", "halaaa", "uala", "wala", "huala", "anda", "andaa", "andaaa", "ostras", "ostra", "ostia", "ostias", "joder", "jo", "joo", "jooo", "jopé", "jope", "jolines", "jobar", "ay", "ayy", "ayyy", "ayyyy", "ayyyyy", "ayayay", "aiaiai", "uf", "uff", "ufff", "uffff", "buf", "buff", "bufff", "pff", "pfff", "pffff", "pffft", "psch", "pscht", "tch", "tsch", "tsk", "tsk-tsk", "ts", "bah", "bahh", "bahhh", "bua", "buaa", "buaaa", "buaaaa", "puaj", "puaaj", "iugh", "eww", "ewww", "yuck", "yak", "bueno", "bueeeno", "bueeenooo", "buenooo", "buenop", "bue", "bwe", "pues", "pueees", "puuues", "pos", "ps", "pssss", "pus", "este", "esteee", "esteeee", "estem", "estemm", "estep", "osea", "o sea", "osease", "osa", "en plan", "enplan", "enplaaan", "tipo", "tipooo", "es que", "esque", "esqueee", "a ver", "aver", "a veeer", "averrr", "haber", "total", "en fin", "enfiin", "sabes", "saes", "viste", "visteee", "cierto", "claro", "claroo", "clarooo", "ya", "yaa", "yaaa", "yaaaa", "vale", "valee", "valep", "dale", "daale", "dalee", "ok", "okey", "okay", "oki", "okis", "okii", "oki-doki", "sip", "sipi", "sep", "se", "see", "seee", "sizi", "si", "sii", "siii", "siiii", "chi", "shi", "nop", "nopi", "nones", "nanai", "noo", "nooo", "noooo", "ne", "nee", "nel", "ey", "eyy", "eyyy", "hey", "heey", "ei", "eii", "oye", "oyeee", "oyeeee", "escucha", "mira", "mire", "che", "chee", "cheee", "bo", "boludo", "wey", "we", "güey", "guey", "chale", "no mames", "órale", "orale", "híjole", "hijole", "macho", "tío", "tio", "tronco", "cari", "gordi", "bebé", "ups", "uppps", "ops", "oops", "glup", "glups", "argh", "arg", "arghh", "grr", "grrr", "grrrr", "zzz", "zzzz", "muac", "muack", "mwah", "plas", "plof", "pum", "zas", "ja", "jaja", "jajaja", "jajajaja", "je", "jeje", "jejeje", "ji", "jiji", "jijiji", "jo", "jojo", "jojojo", "ju", "juju", "jujuju", "jsjs", "jsjsjs", "kkk", "lol", "lool", "omg", "wtf", "idk", "dunno", "meh", "bleh", "chist", "chis", "shh", "shhh", "shhhh", "silencio", "calla", "ea", "huy", "huyy", "uy", "uyy", "uyyy", "ejem", "ejemejem", "cof", "cofcof", "achís", "ñam", "ñamñam", "gluglu", "hic", "hip", "ding", "dong", "toc", "toc-toc", "ring", "bip", "clic", "click", "pim", "pam", "pum", "bla", "blabla", "blablabla", "etc", "pla", "pli", "plo", "pum", "zasca", "zas", "pimba", "toma", "tomaa", "tomaaa", "venga", "vengaaa", "va", "vaaa", "amos", "vamos", "basicamente", ]
        #pausas = ["ppausaa"] # La pausa deberá ser detectada por el whisper/gpt de turno   

    repeticion_constante = False

    vendedor_texto = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "vendedor")

    # Eliminar signos de puntuación y tokenizar
    translator = str.maketrans('', '', string.punctuation + "¿!")
    palabras_limpias = [word.translate(translator) for word in vendedor_texto.split()]

    # Contar muletillas y pausas
    muletillas_usadas = [word for word in palabras_limpias if word in muletillas]
    total_muletillas = len(muletillas_usadas)
    #total_pausas = sum(1 for word in palabras_limpias if word in pausas)

    penalizacion = total_muletillas * 5 #+ total_pausas*10

    # Penalización extra si más del 70% de las muletillas son la misma
    if total_muletillas > 2:
        conteo = Counter(muletillas_usadas)
        muletilla_mas_frecuente, frecuencia = conteo.most_common(1)[0]

        #TODO: Veamos como podemos adaptar esto para detectar muletillas recurrentes sin perjudicar la puntuación de más
        if (frecuencia / total_muletillas > 0.7 and frecuencia > 5):
            # penalizacion += 10
            repeticion_constante = True

    puntuacion = max(0, 100 - penalizacion)  # nunca bajar de 0

    return  {
        "puntuacion": puntuacion, 
        "penalizacion": penalizacion,
        "total_muletillas": total_muletillas,
        "repeticion_constante": repeticion_constante,
        "porcentaje": frecuencia / total_muletillas,
        #"total_pausas": total_pausas,
        "muletillas_usadas": muletillas_usadas
    }
    
# ### Claridad y complejidad
def calcular_claridad(transcript):
    # Lista de tecnicismos a detectar
    negativas = [ "problema", "gasto", "caro", "barato", "difícil", "complicado", "imposible", "intentar", "tratar", "quizás", "tal vez", "espero", "supongo", "creo", "miedo", "riesgo", "pérdida", "fracaso", "error", "fallo", "defecto", "culpa", "molestia", "interrumpir", "perdón", "honestamente", "sinceramente", "para ser franco", "no le voy a mentir", "obviamente", "básicamente", "obligación", "penalización", "cláusula", "letra pequeña", "deuda", "crisis", "baratija", "chollazo", "engaño", "truco", "manipular", "factura", "impuesto", "multa", "sanción", "demora", "retraso", "espera", "urgencia", "presión", "queja", "reclamo", "disputa", "devolución", "cancelación", "negativo", "malo", "peor", "inferior", "inseguro", "dudoso", "incómodo", "pesado", "lento", "antiguo", "obsoleto", "viejo", "roto", "dañado", "sucio", "feo", "odiar", "detestar", "rechazar", "denegar", "prohibir", "limitar", "restringir", "culpable", "víctima", "mentira", "falso", "barullo", "lío", "desastre", "caos", "confusión", "ignorar", "desconocer", "olvidar", "abandonar"]
    
    # Expresiones de lenguaje positivo
    positivas = ["absolutamente", "excelente pregunta", "me encanta esa idea", "claro que sí", "con gusto", "es un placer", "podemos lograr", "le aseguro", "le confirmo", "fantástico", "maravilloso", "por supuesto", "genial", "tiene razón", "lo valoro mucho", "vamos a avanzar", "estoy seguro de que", "lo conseguiremos", "gran punto", "eficaz", "rentable", "solución", "garantía", "seguridad", "optimizar", "beneficio", "calidad", "éxito", "excelente", "innovador", "profesional", "confiable", "rápido", "sencillo", "vital", "estratégico", "resolver", "facilitar", "lograr", "asegurar", "probado", "certificado", "transparente", "ágil", "potente", "superior", "ventaja", "resultado", "compromiso", "respaldo", "experiencia", "crecimiento", "ahorro", "ganancia", "precisión", "eficiencia", "claridad", "productivo", "funcional", "robusto", "idóneo", "perfecto", "magnífico", "estupendo", "colaborar", "construir", "valor", "liderazgo", "mérito", "comprendo", "entiendo", "correcto", "exacto", "lógico", "sensato", "razonable", "impecable", "soberbio", "brillante", "fenomenal", "asombroso", "crucial", "decisivo", "fundamental", "esencial", "supremo", "óptimo", "máximo", "destacado", "notable", "sobresaliente", "excepcional", "único", "exclusivo", "selecto", "premium", "solidez", "firmeza", "integridad", "lealtad", "dinamismo", "ejecución", "alcance", "desempeño", "capacidad", "inteligente"]

    anglicismos = ["pipeline", "forecast", "lead", "target", "budget", "business", "meeting", "call", "feedback", "report", "follow-up", "deadline", "schedule", "planning", "marketing", "sales", "manager", "ceo", "staff", "stock", "partner", "account", "key account", "stakeholder", "b2b", "b2c", "kick-off", "brainstorming", "networking", "pitch", "speech", "storytelling", "insight", "driver", "gap", "pain point", "focus", "know-how", "expertise", "background", "skill", "mindset", "workflow", "task", "check", "update", "asap", "on hold", "stand by", "briefing", "debriefing", "recap", "forward", "attach", "kpi", "roi", "revenue", "profit", "margin", "cash flow", "churn", "growth", "share", "fee", "pricing", "ticket", "online", "offline", "e-commerce", "mailing", "newsletter", "landing page", "webinar", "demo", "trial", "freemium", "premium", "commodity", "niche", "trend", "hype", "branding", "awareness", "conversion", "traffic", "inbound", "outbound", "cold calling", "cross-selling", "up-selling", "pack", "outsourcing", "junior", "senior", "deal", "closing", "win-win", "engagement", "performance", "ranking", "headhunter", "spam", "dashboard", "crm"] 

    # Unir todo el texto del vendedor
    vendedor_texto = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "vendedor")

    translator = str.maketrans('', '', string.punctuation + "¿!")
    palabras_limpias = [word.translate(translator) for word in vendedor_texto.split()]

    # Dividir en frases por punto, ? o !
    frases = [f.strip() for f in vendedor_texto.replace("?", ".").replace("!", ".").split(".") if f.strip()]

    negativas_texto = []
    positivas_texto = []
    anglicismos_texto = []
    frases_largas_texto = []

    # Inicializar métricas
    penalizacion_negativas = 0
    penalizacion_anglicismos = 0
    penalizacion_frases_largas = 0
    bonificacion = 0
    
    # ---- Penalización por negativas ----
    for palabra in palabras_limpias:
        if palabra in negativas: 
            penalizacion_negativas += 15
            negativas_texto.append(palabra)

    penalizacion_negativas = min(45,penalizacion_negativas)

    # ---- Penalización por frases largas ----
    for frase in frases:
        palabras = frase.split()
        if len(palabras) > 25:
            penalizacion_frases_largas += 15
            frases_largas_texto.append(frase)

    penalizacion_frases_largas = min(45,penalizacion_frases_largas)


    #  ---- Penalización por anglicismos ----
    for palabra in palabras_limpias:
        if palabra in anglicismos: 
            penalizacion_anglicismos += 15 
            anglicismos_texto.append(palabra)

    penalizacion_anglicismos = min(45, penalizacion_anglicismos)
    
    # ---- Bonificación por lenguaje positivo ----
    for palabra in palabras_limpias:
        if palabra in positivas: 
            bonificacion += 10
            positivas_texto.append(palabra)

    bonificacion = min(bonificacion,30)
    penalizacion = penalizacion_anglicismos + penalizacion_frases_largas + penalizacion_negativas

    # ---- Calcular puntuación final ----
    puntuacion = max(0, min(100, 100 - penalizacion + bonificacion))

    return {
        "puntuacion": puntuacion,
        "penalizacion": penalizacion,
        "penalizacion_negativas": penalizacion_negativas, 
        "penalizacion_frases_largas": penalizacion_frases_largas, 
        "penalizacion_anglicismos": penalizacion_anglicismos, 
        "bonificacion": bonificacion,
        "num_frases_largas": sum(1 for f in frases if len(f.split()) > 25), 
        "positivas": positivas_texto, 
        "negativas": negativas_texto, 
        "anglicismos": anglicismos_texto,
        "frases_largas": frases_largas_texto, 
    }

### Participación y dinámica
def calcular_participacion_dinamica(transcript):
    # Heurísticas de interrupciones (puedes ampliar con más expresiones típicas)
    # patrones_interrupcion = ["sí", "claro", "vale", "déjame", "espera", "pero"]

    gpt_escucha_activa = escucha_activa(transcript)
    # Try to extract number from GPT response, default to 0 if pattern doesn't match
    match = re.search(r"escucha activa:\s*(\d+)", gpt_escucha_activa, re.IGNORECASE)
    if match:
        num_escucha = int(match.group(1))
    else:
        # Try to find any number in the response as fallback
        numbers = re.findall(r'\d+', gpt_escucha_activa)
        num_escucha = int(numbers[0]) if numbers else 0
    
    # ---- Calcular palabras totales por speaker ----
    palabras_vendedor = 0
    palabras_cliente = 0
    
    for i, turno in enumerate(transcript):
        texto = turno["text"].lower()
        palabras = len(texto.split())
        
        if turno["speaker"] == "vendedor":
            palabras_vendedor += palabras
                    
        elif turno["speaker"] == "cliente":
            palabras_cliente += palabras
    
    total_palabras = palabras_vendedor + palabras_cliente
    ratio = palabras_vendedor/total_palabras
    
    # ---- Penalizaciones y bonificaciones ----
    penalizacion = 0
    bonificacion = min(num_escucha * 10, 40) 
    
    # Arbol de decision
    if 0.6 < ratio <= 0.7:
        penalizacion += 25
    elif 0.7 < ratio <= 0.8:
        penalizacion += 50
    elif 0.8 < ratio <= 0.9:
        penalizacion += 75
    elif ratio > 0.9:
        penalizacion += 100

    # ---- Puntuación final ----
    puntuacion = max(0, min(100, 100 - penalizacion + bonificacion))
    
    return {
        "palabras_cliente": palabras_cliente, 
        "palabras_vendedor": palabras_vendedor, 
        "ratio": ratio,
        "puntuacion": puntuacion,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion,
        "escucha_activa": gpt_escucha_activa,
        "n_escuchas": num_escucha
    }

### Cobertura de temas y palabras clave
#def calcular_cobertura_temas(transcript, temas_clave=None):

    # Temas clave esperados. Aquí habrá que hacer un trabajo de customización 
    palabras_clave = ["seguridad", "fiabilidad", "garantía", "asistencia", "estabilidad", "eficiencia", "ahorro", "valor de reventa", "financiación", "cuota", "tasación", "confort", "conectividad", "versatilidad", "espacio", "autonomía", "equipamiento"]
    
    
    vendedor_texto = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "vendedor")
    #cliente_texto  = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "cliente")

    penalizacion = 0
    bonificacion = 0

    ## Detector de proximos pasos con GPT
    gpt_proximos_pasos = proximos_pasos(transcript)
    # Try to extract boolean or number from GPT response
    # First try to find a boolean pattern
    bool_match = re.search(r'(true|false|verdadero|falso|sí|si|no)', gpt_proximos_pasos, re.IGNORECASE)
    if bool_match:
        bool_value = bool_match.group(1).lower()
        proximos_pasos_bool = 1 if bool_value in ['true', 'verdadero', 'sí', 'si'] else 0
    else:
        # Try to find a number pattern
        match = re.search(r"señales de proximos pasos:\s*(\d+)", gpt_proximos_pasos, re.IGNORECASE)
        if match:
            proximos_pasos_bool = int(match.group(1))
        else:
            # Try to find any number in the response as fallback
            numbers = re.findall(r'\d+', gpt_proximos_pasos)
            proximos_pasos_bool = int(numbers[0]) if numbers else 0
    
    output_gpt = gpt_proximos_pasos  # Store the full GPT response
    
    # ---- Temas clave olvidados ----
    temas_olvidados = []
    for palabra in palabras_clave:
        if palabra not in vendedor_texto:
            penalizacion += 15
            temas_olvidados.append(palabra)
    
    # # ---- Objeciones críticas no resueltas ----
    # objeciones_cliente = ["precio", "coste", "caro", "elevado", "demasiado"]
    # objecion_detectada = any(word in cliente_texto for word in objeciones_cliente)
    
    # if objecion_detectada:
    #     # ¿Responde el vendedor?
    #     respuesta = any(word in vendedor_texto for word in ["precio", "coste", "inversión", "valor"])
    #     if not respuesta:
    #         penalizacion += 30
    
    
    # ---- Puntuación final ----
    puntuacion = max(0, min(100, 100 - penalizacion + bonificacion))
    
    return {
        "puntuacion": puntuacion,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion,
        "temas_olvidados": temas_olvidados,
        #"objecion_no_resuelta": objecion_detectada and not respuesta,
        "proximos_pasos": proximos_pasos_bool,
        "output_gpt": output_gpt
    }

### Cobertura de temas y palabras clave (mejorado con LLMs)
def calcular_cobertura_temas(transcript,num_temas=6):

    penalizacion = 0
    bonificacion = 0

    ## Detector de palabras clave con GPT
    # INSERT_YOUR_CODE
    gpt_temas_clave = temas_clave(transcript)

    # Intentar extraer el número de temas clave abordados
    match_num = re.search(r"(\d+)", gpt_temas_clave)
    num_temas_abordados = int(match_num.group(1)) if match_num else 0

    # Si no se extrajeron señales explícitas, tomar el resto del output después del número
    if match_num:
        num_pos = gpt_temas_clave.find(match_num.group(1))
        restantes = gpt_temas_clave[num_pos + len(match_num.group(1)) :]
        # Extraer líneas no vacías y quitar espacios extras
        señales_temas = [l.strip() for l in restantes.split('\n') if l.strip()]

    # Puedes usar num_temas_abordados y señales_temas como quieras para penalizar o bonificar
    num_temas_olvidados = num_temas - num_temas_abordados
    penalizacion += num_temas_olvidados*20

    ## Detector de proximos pasos con GPT
    gpt_proximos_pasos = proximos_pasos(transcript)
    # Try to extract boolean or number from GPT response
    # First try to find a boolean pattern
    bool_match = re.search(r'(true|false|verdadero|falso|sí|si|no)', gpt_proximos_pasos, re.IGNORECASE)
    if bool_match:
        bool_value = bool_match.group(1).lower()
        proximos_pasos_bool = 1 if bool_value in ['true', 'verdadero', 'sí', 'si'] else 0
    else:
        # Try to find a number pattern
        match = re.search(r"señales de proximos pasos:\s*(\d+)", gpt_proximos_pasos, re.IGNORECASE)
        if match:
            proximos_pasos_bool = int(match.group(1))
        else:
            # Try to find any number in the response as fallback
            numbers = re.findall(r'\d+', gpt_proximos_pasos)
            proximos_pasos_bool = int(numbers[0]) if numbers else 0
    
    output_gpt = gpt_proximos_pasos  # Store the full GPT response
    bonificacion = 10 * proximos_pasos_bool
    
    
    # # ---- Objeciones críticas no resueltas ----
    # objeciones_cliente = ["precio", "coste", "caro", "elevado", "demasiado"]
    # objecion_detectada = any(word in cliente_texto for word in objeciones_cliente)
    
    # if objecion_detectada:
    #     # ¿Responde el vendedor?
    #     respuesta = any(word in vendedor_texto for word in ["precio", "coste", "inversión", "valor"])
    #     if not respuesta:
    #         penalizacion += 30
    
    
    # ---- Puntuación final ----
    puntuacion = max(0, min(100, 100 - penalizacion + bonificacion))
    
    return {
        "puntuacion": puntuacion,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion,
        "temas_olvidados": num_temas_olvidados,
        #"objecion_no_resuelta": objecion_detectada and not respuesta,
        "proximos_pasos": proximos_pasos_bool,
        "señales_temas": señales_temas,
        "output_gpt": output_gpt
    }

### Indice de preguntas (Aquí hay que darle una pensadica)
def calcular_indice_preguntas(transcript):
    # Definiciones de sets de preguntas
    preguntas_cerradas = [
        "¿necesita una demostración?", "¿le interesa el producto?", "¿está de acuerdo con el precio?", 
        "¿tiene alguna pregunta?", "¿me escucha bien?", "¿terminamos aquí?", "¿lo ve factible?", 
        "¿quiere seguir adelante?", "¿tiene x presupuesto?", "¿le parece bien esto?", 
        "¿podemos empezar mañana?", "¿sí o no?", "¿cuenta con la autoridad?"
    ]
    
    preguntas_sondeo = [
        "¿cómo afecta este problema a su rentabilidad?", "¿cuál es el costo de no resolver esto a tiempo?", 
        "¿qué prioridades tiene para el próximo trimestre?", "¿qué criterios usará para tomar la decisión?", 
        "¿qué alternativas ha evaluado hasta ahora?", "¿qué impacto tendría en su equipo?", 
        "¿qué pasaría si mantiene el status quo?", "¿cómo mide el éxito de este proyecto?", 
        "¿quién más está involucrado en la decisión?", "¿qué le preocupa más de la solución?", 
        "¿por qué es importante esto ahora?"
    ]
    
    preguntas_irrelevantes = [
        "¿hizo buen tiempo hoy?", "¿cómo va el tráfico por su zona?", "¿qué tal su fin de semana?", 
        "¿leyó las noticias de hoy?", "¿qué opina de", "¿tiene planes para las fiestas?", 
        "¿qué equipo de fútbol le gusta?", "¿dónde está ubicado su edificio?", "¿viajó mucho para llegar hoy?"
    ]
    
    # Solo texto del vendedor
    vendedor_texto = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "vendedor")
    
    # Extraer todas las preguntas que hace el vendedor
    preguntas = re.findall(r"¿.*?\?", vendedor_texto, re.DOTALL)
    
    total_preguntas = len(preguntas)
    count_cerradas = 0
    count_sondeo = 0
    count_irrelevantes = 0
    
    for p in preguntas:
        p = p.strip()
        if any(p.startswith(pc) for pc in preguntas_cerradas):
            count_cerradas += 1
        elif any(p.startswith(ps) for ps in preguntas_sondeo):
            count_sondeo += 1
        elif any(p.startswith(pi) for pi in preguntas_irrelevantes):
            count_irrelevantes += 1
    
    penalizacion = 0
    bonificacion = 0
    
    # Penalización si cerradas > 60% del total
    if total_preguntas > 0 and (count_cerradas / total_preguntas) > 0.6:
        penalizacion += 15
    
    # Penalización por irrelevantes
    penalizacion += count_irrelevantes * 10
    
    # Bonificación por sondeo
    bonificacion += count_sondeo * 10
    
    # Score final
    puntuacion = max(0, min(100, 100 - penalizacion + bonificacion))
    
    return {
        "puntuacion": puntuacion,
        "total_preguntas": total_preguntas,
        "preguntas": preguntas,
        "cerradas": count_cerradas,
        "sondeo": count_sondeo,
        "irrelevantes": count_irrelevantes,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion
    }

### PPM y variabilidad
def calcular_ppm_variabilidad(transcript):
    # Consideramos solo al vendedor
    turnos_vendedor = [t for t in transcript if t["speaker"] == "vendedor"]
    
    if not turnos_vendedor:
        return {
            "puntuacion": 100,
            "ppms": [],
            "media_ppm": None,
            "variabilidad": None,
            "penalizacion": 0,
            "bonificacion": 0
        }
    
    ppms = []
    total_palabras = 0
    total_duracion = 0.0
    
    for t in turnos_vendedor:
        palabras = len(t["text"].split())
        duracion = t["duracion"]
        ppm = palabras / (duracion / 60)
        
        ppms.append(ppm)
        total_palabras += palabras
        total_duracion += duracion
    
    media_ppm = total_palabras / (total_duracion / 60)
    variabilidad = np.std(ppms) if len(ppms) > 1 else 0
    
    penalizacion = 0
    bonificacion = 0
    
    # Penalización por rango de velocidad
    # < 100 o > 180: penalización máxima
    # 100-119.9 o 160.1-180: penalización alta
    # 120-129.9 o 150.1-160: penalización media
    # 130-150: sin penalización
    if media_ppm < 100 or media_ppm > 180:
        penalizacion += 100
    elif (100 <= media_ppm < 120) or (160 < media_ppm <= 180):
        penalizacion += 60
    elif (120 <= media_ppm < 130) or (150 < media_ppm <= 160):
        penalizacion += 30

    
    # Penalización por variabilidad extrema
    if variabilidad > 30:  # umbral configurable
        penalizacion += 15
    
    puntuacion = max(0, min(100, 100 - penalizacion + bonificacion))
    
    return {
        "puntuacion": puntuacion,
        "ppms": ppms,
        "media_ppm": round(media_ppm, 1),
        "variabilidad": round(variabilidad, 1),
        "penalizacion": penalizacion,
        "bonificacion": bonificacion
    }

## Scoring function
def get_conver_scores(transcript):
    # Factores de ponderación
    pesos = {
        "muletillas_pausas": 0.15,
        "claridad": 0.15,
        "participacion": 0.25,
        "cobertura": 0.15,
        "preguntas": 0.20,
        "ppm": 0.10
    }
    
    # Evaluaciones individuales
    res_muletillas = calcular_muletillas(transcript)
    res_claridad = calcular_claridad(transcript)
    res_participacion = calcular_participacion_dinamica(transcript)
    res_cobertura = calcular_cobertura_temas(transcript)
    res_preguntas = calcular_indice_preguntas(transcript)
    res_ppm = calcular_ppm_variabilidad(transcript)
    
    # Extraer puntuaciones
    scores = {
        "muletillas_pausas": res_muletillas["puntuacion"],
        "claridad": res_claridad["puntuacion"],
        "participacion": res_participacion["puntuacion"],
        "cobertura": res_cobertura["puntuacion"],
        "preguntas": res_preguntas["puntuacion"],
        "ppm": res_ppm["puntuacion"]
    }
    
    # Calcular puntuación ponderada global
    puntuacion_final = sum(scores[k] * pesos[k] for k in scores)
    
    return {
        "puntuacion_global": round(puntuacion_final, 1),
        "detalle": scores,
    }

if __name__ == "__main__":
    transcript_demo = [
        {
            "speaker": "vendedor", 
            "text": "Hola, buenas tardes. Bienvenido a nuestra exposición, eh... mi nombre es Carlos. Veo que se ha detenido justo delante del nuevo Conversa XL. Tiene buen ojo, es la unidad que acabamos de recibir esta misma mañana desde fábrica.", 
            "duracion": 18
        },
        {
            "speaker": "cliente", 
            "text": "Hola Carlos. Sí, la verdad es que estaba buscando algo más grande porque la familia ha crecido y mi coche actual se nos ha quedado minúsculo.", 
            "duracion": 12
        },
        {
            "speaker": "vendedor", 
            "text": "Le entiendo perfectamente. El espacio es vital. Déjeme decirle que hemos cambiado totalmente el **mindset** de diseño para enfocarnos en familias como la suya. Fíjese en estas líneas laterales, no solo son estética, son refuerzos de acero al boro que absorben impactos. De hecho, quería comentarle que en temas de seguridad somos líderes absolutos; hemos ganado los premios 'Safety Best 2024' y las 5 estrellas Euro NCAP, así que no tendrá ningún miedo al llevar a sus hijos en carretera.", 
            "duracion": 38
        },
        {
            "speaker": "cliente", 
            "text": "La seguridad es importante, claro. Pero mi esposa está obsesionada con el maletero. En el que tenemos ahora, meter el carrito del bebé y la compra es imposible, siempre tenemos que dejar bolsas en los asientos de atrás.", 
            "duracion": 18
        },
        {
            "speaker": "vendedor", 
            "text": "Comprendo. Si le sigo bien, lo que me está diciendo es que su mayor dolor de cabeza actual es la falta de capacidad de carga y necesita garantías de que podrá meter el carrito y las bolsas del supermercado todo junto en el maletero sin invadir los asientos, ¿es eso correcto?", 
            "duracion": 25
        },
        {
            "speaker": "cliente", 
            "text": "Exacto, eso es justo lo que necesito. Que no sea un tetris cada vez que salimos de viaje.", 
            "duracion": 8
        },
        {
            "speaker": "vendedor", 
            "text": "Pues venga por aquí, quiero que vea esto. Abra el portón. Tenemos 650 litros de capacidad real. O sea, aquí le caben dos carritos si hace falta. Además, la boca de carga es muy baja para que no se deje la espalda levantando peso. Y mire los asientos traseros, son individuales. No va a tener problema para colocar tres sillas infantiles, algo que muy pocos coches de la competencia permiten hoy en día.", 
            "duracion": 35
        },
        {
            "speaker": "cliente", 
            "text": "Oye, pues es verdad que se ve inmenso. ¿Y de tecnología qué tal va? Porque no quiero algo que sea muy complicado de usar, la pantalla esa parece una nave espacial.", 
            "duracion": 15
        },
        {
            "speaker": "vendedor", 
            "text": "Parece compleja, pero el **feedback** que recibimos de todos los usuarios es que se aprende a usar en cinco minutos. Mire, le voy a ser sincero, la integración tecnológica hoy en día es algo que no podemos ignorar de ninguna manera porque la conectividad nos facilita la vida y usted necesita saber que puede gestionar las llamadas y el mapa sin soltar el volante en ningún momento bajo ninguna circunstancia.", 
            "duracion": 40
        },
        {
            "speaker": "cliente", 
            "text": "Ya, mientras no se cuelgue... ¿Y el motor? Hago muchos kilómetros para ir al trabajo y la gasolina está carísima.", 
            "duracion": 10
        },
        {
            "speaker": "vendedor", 
            "text": "Esteee... no se preocupe por eso. Montamos un motor híbrido auto-recargable de última generación. El coche gestiona solo cuándo usar la batería y cuándo el motor térmico. Esto significa que en ciudad va a ir casi siempre en eléctrico, reduciendo el gasto de combustible a la mitad comparado con su coche actual. Es eficiencia pura.", 
            "duracion": 28
        },
        {
            "speaker": "cliente", 
            "text": "Suena bien lo del ahorro. Pero vamos a lo doloroso... he estado mirando el modelo similar de la marca alemana y se me va de precio. Imagino que este, siendo nuevo y con tanta tecnología, costará un ojo de la cara.", 
            "duracion": 18
        },
        {
            "speaker": "vendedor", 
            "text": "Para nada, y aquí es donde el Conversa XL realmente brilla. Sabemos que el **budget** familiar es sagrado. Hemos posicionado este vehículo con una estrategia muy agresiva. Si compara equipamiento por equipamiento, nuestro precio final está actualmente un 12% por debajo de la competencia directa alemana o japonesa. Básicamente, se lleva más coche por menos dinero.", 
            "duracion": 32
        },
        {
            "speaker": "cliente", 
            "text": "Un 12% es bastante diferencia... ¿Y tenéis financiación? Porque no quería descapitalizarme ahora mismo pagándolo todo de golpe.", 
            "duracion": 12
        },
        {
            "speaker": "vendedor", 
            "text": "Sí, tenemos un plan flexible. Bueno, podemos ajustar la entrada y dejar una cuota que ni note a fin de mes. Es la mejor solución para tener el coche ya sin agobios financieros.", 
            "duracion": 18
        },
        {
            "speaker": "cliente", 
            "text": "Tendría que consultarlo con mi mujer esta noche, no quiero precipitarme.", 
            "duracion": 8
        },
        {
            "speaker": "vendedor", 
            "text": "Es lógico, consúltelo. Pero déjeme advertirle de una cosa: esta campaña de lanzamiento con el descuento del 12% termina estrictamente este viernes. Si lo deja pasar, corre el riesgo de tener que pagar la tarifa oficial la semana que viene, que son casi 3.000 euros más. ¿Sabes? yo en su lugar dejaría hecha una reserva simbólica hoy, que es totalmente reembolsable, solo para bloquear el precio y las condiciones.", 
            "duracion": 40
        },
        {
            "speaker": "cliente", 
            "text": "Si es reembolsable... supongo que no pierdo nada por dejarlo reservado mientras lo pienso.", 
            "duracion": 10
        }
    ]
    
    # print("*************** MULETILLAS ***************")
    # print(calcular_muletillas(transcript_demo))
    # print("******************************************")
    # print("*************** CLARIDAD ***************")
    # print(calcular_claridad(transcript_demo))
    # print("******************************************")    
    # print("*************** PARTICIPACION ***************")
    # print(calcular_participacion_dinamica(transcript_demo))
    # print("******************************************")
    # print("*************** COBERTURA TEMAS ***************")
    # print(calcular_cobertura_temas(transcript_demo))
    # print("******************************************")
    # print("*************** PPM ***************")
    # print(calcular_ppm_variabilidad(transcript_demo))
    # print("******************************************")

    # INSERT_YOUR_CODE



    # Calcular los resultados para cada métrica y guardar la información relevante
    muletillas_result = calcular_muletillas(transcript_demo)
    claridad_result = calcular_claridad(transcript_demo)
    participacion_result = calcular_participacion_dinamica(transcript_demo)
    cobertura_temas_result = calcular_cobertura_temas(transcript_demo)
    ppm_result = calcular_ppm_variabilidad(transcript_demo)
    # INSERT_YOUR_CODE
 

    # Muletillas dataframe
    df_muletillas = pd.DataFrame([{
        "puntuacion": muletillas_result["puntuacion"],
        "total_muletillas": muletillas_result.get("total_muletillas", None),
        "muletillas_detectadas": muletillas_result.get("muletillas_detectadas", None),
        "penalizacion": muletillas_result.get("penalizacion", None),
        "detalle": muletillas_result
    }])

    # Claridad dataframe
    df_claridad = pd.DataFrame([{
        "puntuacion": claridad_result["puntuacion"],
        "palabras_largas_detectadas": claridad_result.get("palabras_largas_detectadas", None),
        "penalizacion": claridad_result.get("penalizacion", None),
        "detalle": claridad_result
    }])

    # Participación dataframe
    df_participacion = pd.DataFrame([{
        "puntuacion": participacion_result["puntuacion"],
        "cliente": participacion_result.get("cliente", None),
        "vendedor": participacion_result.get("vendedor", None),
        "bonificacion": participacion_result.get("bonificacion", None),
        "penalizacion": participacion_result.get("penalizacion", None),
        "detalle": participacion_result
    }])

    # Cobertura de temas dataframe
    df_cobertura_temas = pd.DataFrame([{
        "puntuacion": cobertura_temas_result["puntuacion"],
        "temas_olvidados": cobertura_temas_result.get("temas_olvidados", None),
        "proximos_pasos": cobertura_temas_result.get("proximos_pasos", None),
        "output_gpt": cobertura_temas_result.get("output_gpt", None),
        "penalizacion": cobertura_temas_result.get("penalizacion", None),
        "bonificacion": cobertura_temas_result.get("bonificacion", None),
        "detalle": cobertura_temas_result
    }])

    # PPM dataframe
    df_ppm = pd.DataFrame([{
        "puntuacion": ppm_result["puntuacion"],
        "ppm_cliente": ppm_result.get("ppm_cliente", None),
        "ppm_vendedor": ppm_result.get("ppm_vendedor", None),
        "variabilidad_cliente": ppm_result.get("variabilidad_cliente", None),
        "variabilidad_vendedor": ppm_result.get("variabilidad_vendedor", None),
        "detalle": ppm_result
    }])

       # Guardar los resultados en ficheros CSV mejorados por cada métrica
    df_muletillas.to_csv("resultados_muletillas.csv", index=False, encoding="utf-8-sig")
    df_claridad.to_csv("resultados_claridad.csv", index=False, encoding="utf-8-sig")
    df_participacion.to_csv("resultados_participacion.csv", index=False, encoding="utf-8-sig")
    df_cobertura_temas.to_csv("resultados_cobertura_temas.csv", index=False, encoding="utf-8-sig")
    df_ppm.to_csv("resultados_ppm.csv", index=False, encoding="utf-8-sig")
    print("Se guardaron los resultados mejorados en archivos CSV.")


    
    print("DataFrame Muletillas:\n", df_muletillas)
    print("DataFrame Claridad:\n", df_claridad)
    print("DataFrame Participación:\n", df_participacion)
    print("DataFrame Cobertura Temas:\n", df_cobertura_temas)
    print("DataFrame PPM:\n", df_ppm)