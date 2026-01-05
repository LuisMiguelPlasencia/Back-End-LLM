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
import time
from app.services.courses_service import get_courses_details
import json

sys.path.insert(0, "../../src")
load_dotenv()
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")

client = OpenAI(api_key=OPENAI_TOKEN)

def call_gpt(prompt: str, model="gpt-4.1-nano-2025-04-14") -> str:
    response = client.responses.create(
        model=model,
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
    Te voy a pasar la transcripcion de una conversación, presta atención a lo siguiente: Tienes que identificar si el vendedor al final de la conversación ha establecido o hablado de unos próximos pasos en la interacción con el cliente. Por ejemplo, el vendedor puede intentar agendar una segunda llamada, una prueba del producto o un futuro contacto. Se exigente, puede que el vendedor no mencione nada acerca de próximos pasos. 
    TRANSCRIPCIÓN:
    {transcript}

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
    {{"indicador": true/false, 
     "señales": "Indica la intervención en la que el vendedor habla de proximos pasos. Se lo más breve y conciso posible"
    }}
    """
    output = call_gpt(prompt)
    return output

def temas_clave(transcript, temas_clave="Precio, Seguridad, capacidad maletero, plazas, combustible y llantas"): #"Precio (que nuestro precio está por debajo de la competencia), Seguridad (Hemos ganado premios de seguridad), Espacio (somos el único vehículo con 5 asientos), combustible (hablar de que consume menos de 5L por cada 100km), capacidad maletero (mayor que la media de la competencia), llantas (modelo muy atractivo)"
    prompt = f"""
    Te voy a pasar la transcripcion de una conversación, haz lo siguiente: Tienes que identificar si el vendedor habla acerca de los temas clave que te voy a mandar. Se exigente, hablar de un tema clave no implica solamente mencionar dicha palabra, debe haber un pequeño desarrollo. 

    TRANSCRIPCIÓN:
    {transcript}

    TEMAS CLAVE: 
    {temas_clave}

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato:
    {{"n": "numero entero mencionando el numero de temas clave abordados", 
     "señales": "Señales donde se identifican temas claves abordados. Se lo más breve y conciso posible",
     "feedback": "Temas claves que no se han abordado. Se lo más breve y conciso posible"}}
    """
    output = call_gpt(prompt)
    
    return output

def index_of_questions(transcript):
    prompt = f"""
    Te voy a pasar la transcripcion de una conversación, haz lo siguiente: Tienes que identificar las preguntas que realiza el vendedor y detectar las preguntas cerradas, preguntas de sondeo/impacto y preguntas irrelevantes. 

    TRANSCRIPCIÓN:
    {transcript}

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato:
    {{
     "n_total": "numero entero mencionando el numero total de preguntas que hace el vendedor",
     "n_cerradas": "numero entero mencionando el numero preguntas cerradas que hace el vendedor",
     "n_sondeo": "numero entero mencionando el numero de preguntas de sondeo que hace el vendedor", 
     "n_irrelevantes": "numero entero mencionando el numero de preguntas irrelevantes que hace el vendedor"
     "señales": "Señales donde se identifican los distintos tipos de preguntas que hace el vendedor",
     "feedback": "Explica como se podrían formular mejores preguntas"}}
    """
    output = call_gpt(prompt)
    
    return output

def objetivo(transcript, objetivo):


    prompt = f"""
    Vas a analizar la transcripción de una conversación comercial entre un vendedor y un cliente.
    Tu tarea es evaluar exclusivamente si el vendedor logra cumplir el OBJETIVO PRINCIPAL, basándote únicamente en lo que está explícitamente dicho en la transcripción.

    Instrucciones clave:
        -El objetivo solo se considera cumplido si el vendedor lo ejecuta de forma clara, directa y verificable dentro de la conversación.
        -Intenciones, promesas futuras, suposiciones o respuestas ambiguas NO cuentan como cumplimiento del objetivo.
        -Si el cliente acepta algo pero el vendedor no realiza la acción correspondiente, el objetivo NO se considera cumplido.
        -Si el objetivo se cumple, debes identificar exactamente la intervención del vendedor (frase literal) que demuestra dicho cumplimiento.
        -Si no se cumple, el indicador debe ser false y las señales deben explicar brevemente por qué no hay evidencia suficiente.

    TRANSCRIPCIÓN:
    {transcript}

    OBJETIVO PRINCIPAL: 
    {objetivo} 

    RESPONDE ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
    {{"indicador": true/false, 
     "señales": "Indica la intervención en la que el vendedor cumple el objetivo, acompañado de la frase exacta. Por ejemplo: '¡Fantástico! Le acabo de enviar un enlace seguro a su correo... . Se lo más breve y conciso posible'" 
    }}
    """

    #print(prompt)
    output = call_gpt(prompt)
    
    return output

def feedback_muletillas(transcript, ratio_muletilla):
    prompt = f"""
    Te voy a pasar la transcripcion de una conversación, presta atención a lo siguiente: Tienes que identificar si el vendedor utiliza muletillas 

    TRANSCRIPCIÓN:
    {transcript}

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
    {{
     "señales": "Indica la intervención en la que el vendedor usa muletillas. Ejemplo: Ehh, digamos que, mmmm ..."
     "feedback": "Has utilizado las siguientes muletillas: "señales". El ratio de muletillas respecto al total de palabras es {ratio_muletilla:.2f}, lo cual indica un uso si {ratio_muletilla} > 0.1 'excesivo', 'moderado' si {ratio_muletilla} > 0.05 y < 0.1, 'bajo' si {ratio_muletilla} < 0.05."
    }}
    """
    output = call_gpt(prompt)
    
    return output

def feedback_claridad(transcript):
    prompt = f"""
    Te voy a pasar la transcripcion de una conversación, presta atención a lo siguiente: Tienes que identificar momentos en los que el vendedor no es claro en sus propuestas.

    TRANSCRIPCIÓN:
    {transcript}

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
    {{
     "señales": "Indica la intervención en la que el vendedor no es claro en su propuesta. Se lo más breve y conciso posible"
    }}
    """
    output = call_gpt(prompt)
    
    return output

def feedback_participacion(transcript):
    prompt = f"""
    Te voy a pasar la transcripcion de una conversación, presta atención a lo siguiente: Tienes que identificar si el vendedor interrumpe al cliente o presenta heuristicas de escucha activa. 

    TRANSCRIPCIÓN:
    {transcript}

    Responde ÚNICAMENTE devolviendo un JSON con el siguiente formato: 
    {{
     "señales": "Indica las señales en la que el vendedor interrumpe al cliente o presenta heuristicas de escucha activa. Se breve"
    }}
    """
    output = call_gpt(prompt)
    
    return output

# ### Muletillas
def calcular_muletillas(transcript, duracion=None, muletillas=None):
    if muletillas is None:
        muletillas = ["eh", "ehh", "ehhh", "ehhhh", "ehhhhh", "he", "hee", "ehm", "ehmm", "em", "emm", "emmm", "emmmm", "eeem", "eeemm", "e-eh", "hem", "hemm", "uh", "uhh", "uhhh", "uhhhh", "uhhhhh", "uhm", "uhmm", "umm", "ummm", "ummmm", "umh", "hum", "humm", "hummm", "humn", "mmm", "mmmm", "mmmmm", "mmmh", "mmmhh", "mmh", "mm-hm", "mhm", "m-hm", "mjm", "mjum", "m-jm", "ajá", "aja", "ahá", "aha", "aham", "ajam", "ah", "ahh", "ahhh", "ahhhh", "ahhhhh", "oh", "ohh", "ohhh", "ohhhh", "ooh", "oooh", "oho", "o-oh", "wow", "wooo", "wooow", "wou", "wow", "guau", "guaau", "ala", "alaaa", "hala", "halaaa", "uala", "wala", "huala", "anda", "andaa", "andaaa", "ostras", "ostra", "ostia", "ostias", "joder", "jo", "joo", "jooo", "jopé", "jope", "jolines", "jobar", "ay", "ayy", "ayyy", "ayyyy", "ayyyyy", "ayayay", "aiaiai", "uf", "uff", "ufff", "uffff", "buf", "buff", "bufff", "pff", "pfff", "pffff", "pffft", "psch", "pscht", "tch", "tsch", "tsk", "tsk-tsk", "ts", "bah", "bahh", "bahhh", "bua", "buaa", "buaaa", "buaaaa", "puaj", "puaaj", "iugh", "eww", "ewww", "yuck", "yak", "bueno", "bueeeno", "bueeenooo", "buenooo", "buenop", "bue", "bwe", "pues", "pueees", "puuues", "pos", "ps", "pssss", "pus", "este", "esteee", "esteeee", "estem", "estemm", "estep", "osea", "o sea", "osease", "osa", "en plan", "enplan", "enplaaan", "tipo", "tipooo", "es que", "esque", "esqueee", "a ver", "aver", "a veeer", "averrr", "haber", "total", "en fin", "enfiin", "sabes", "saes", "viste", "visteee", "cierto", "claro", "claroo", "clarooo", "ya", "yaa", "yaaa", "yaaaa", "vale", "valee", "valep", "dale", "daale", "dalee", "ok", "okey", "okay", "oki", "okis", "okii", "oki-doki", "sip", "sipi", "sep", "se", "see", "seee", "sizi", "si", "sii", "siii", "siiii", "chi", "shi", "nop", "nopi", "nones", "nanai", "noo", "nooo", "noooo", "ne", "nee", "nel", "ey", "eyy", "eyyy", "hey", "heey", "ei", "eii", "oye", "oyeee", "oyeeee", "escucha", "mira", "mire", "che", "chee", "cheee", "bo", "boludo", "wey", "we", "güey", "guey", "chale", "no mames", "órale", "orale", "híjole", "hijole", "macho", "tío", "tio", "tronco", "cari", "gordi", "bebé", "ups", "uppps", "ops", "oops", "glup", "glups", "argh", "arg", "arghh", "grr", "grrr", "grrrr", "zzz", "zzzz", "muac", "muack", "mwah", "plas", "plof", "pum", "zas", "ja", "jaja", "jajaja", "jajajaja", "je", "jeje", "jejeje", "ji", "jiji", "jijiji", "jo", "jojo", "jojojo", "ju", "juju", "jujuju", "jsjs", "jsjsjs", "kkk", "lol", "lool", "omg", "wtf", "idk", "dunno", "meh", "bleh", "chist", "chis", "shh", "shhh", "shhhh", "silencio", "calla", "ea", "huy", "huyy", "uy", "uyy", "uyyy", "ejem", "ejemejem", "cof", "cofcof", "achís", "ñam", "ñamñam", "gluglu", "hic", "hip", "ding", "dong", "toc", "toc-toc", "ring", "bip", "clic", "click", "pim", "pam", "pum", "bla", "blabla", "blablabla", "etc", "pla", "pli", "plo", "pum", "zasca", "zas", "pimba", "toma", "tomaa", "tomaaa", "venga", "vengaaa", "va", "vaaa", "amos", "vamos", "basicamente", ]
        #pausas = ["ppausaa"] # La pausa deberá ser detectada por el whisper/gpt de turno   

    repeticion_constante = False
    top_2_muletillas = ''

    vendedor_texto = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "vendedor")

    # Eliminar signos de puntuación y tokenizar
    translator = str.maketrans('', '', string.punctuation + "¿!")
    palabras_limpias = [word.translate(translator) for word in vendedor_texto.split()]

    # Contar muletillas y pausas
    muletillas_usadas = [word for word in palabras_limpias if word in muletillas]
    total_muletillas = len(muletillas_usadas)
    total_palabras = len(palabras_limpias)
    porcentaje_muletillas = (total_muletillas / total_palabras * 100)
    #total_pausas = sum(1 for word in palabras_limpias if word in pausas)
    frecuencia = 0
    penalizacion = total_muletillas * 5 #+ total_pausas*10

    # Get top 3 most used filler words
    top_2_muletillas = Counter(muletillas_usadas).most_common(2)

    # Penalización extra si más del 70% de las muletillas son la misma
    if total_muletillas > 1:
        conteo = Counter(muletillas_usadas)
        muletilla_mas_frecuente, frecuencia = conteo.most_common(1)[0]

        #TODO: Veamos como podemos adaptar esto para detectar muletillas recurrentes sin perjudicar la puntuación de más
        ratio_muletilla = frecuencia / total_muletillas if total_muletillas > 0 else 0
        if (ratio_muletilla > 0.7 and frecuencia > 5):
            # penalizacion += 10
            repeticion_constante = True
    

    puntuacion = max(0, 100 - penalizacion)  # nunca bajar de 0


    #feedback = json.loads(feedback_muletillas(transcript,ratio_muletilla))

    return  {
        "puntuacion": puntuacion, 
        "penalizacion": penalizacion,
        "total_muletillas": total_muletillas,
        "repeticion_constante": repeticion_constante,
        "porcentaje": porcentaje_muletillas,
        #"total_pausas": total_pausas,
        "muletillas_usadas": ", ".join(muletillas_usadas),
        "feedback": f"El porcentaje de muletillas empleadas es {porcentaje_muletillas:.2f}%, siendo las muletillas mas repetidas: {', '.join(m[0] for m in top_2_muletillas)} "
    }
    
# ### Claridad y complejidad
def calcular_claridad(transcript):
    # Lista de tecnicismos a detectar
    negativas = [ "problema", "gasto", "caro", "barato", "difícil", "complicado", "imposible", "intentar", "tratar", "quizás", "tal vez", "espero", "supongo", "creo", "miedo", "riesgo", "pérdida", "fracaso", "error", "fallo", "defecto", "culpa", "molestia", "interrumpir", "perdón", "honestamente", "sinceramente", "para ser franco", "no le voy a mentir", "obviamente", "básicamente", "obligación", "penalización", "cláusula", "letra pequeña", "deuda", "crisis", "baratija", "chollazo", "engaño", "truco", "manipular", "factura", "impuesto", "multa", "sanción", "demora", "retraso", "espera", "urgencia", "presión", "queja", "reclamo", "disputa", "devolución", "cancelación", "negativo", "malo", "peor", "inferior", "inseguro", "dudoso", "incómodo", "pesado", "lento", "antiguo", "obsoleto", "viejo", "roto", "dañado", "sucio", "feo", "odiar", "detestar", "rechazar", "denegar", "prohibir", "limitar", "restringir", "culpable", "víctima", "mentira", "falso", "barullo", "lío", "desastre", "caos", "confusión", "ignorar", "desconocer", "olvidar", "abandonar"]
    
    # Expresiones de lenguaje positivo
    positivas = ["absolutamente", "excelente pregunta", "me encanta esa idea", "claro que sí", "con gusto", "es un placer", "podemos lograr", "le aseguro", "le confirmo", "fantástico", "maravilloso", "por supuesto", "genial", "tiene razón", "lo valoro mucho", "vamos a avanzar", "estoy seguro de que", "lo conseguiremos", "gran punto", "eficaz", "rentable", "solución", "garantía", "seguridad", "optimizar", "beneficio", "calidad", "éxito", "excelente", "innovador", "profesional", "confiable", "rápido", "sencillo", "vital", "estratégico", "resolver", "facilitar", "lograr", "asegurar", "probado", "certificado", "transparente", "ágil", "potente", "superior", "ventaja", "resultado", "compromiso", "respaldo", "experiencia", "crecimiento", "ahorro", "ganancia", "precisión", "eficiencia", "claridad", "productivo", "funcional", "robusto", "idóneo", "perfecto", "magnífico", "estupendo", "colaborar", "construir", "valor", "liderazgo", "mérito", "comprendo", "entiendo", "correcto", "exacto", "lógico", "sensato", "razonable", "impecable", "soberbio", "brillante", "fenomenal", "asombroso", "crucial", "decisivo", "fundamental", "esencial", "supremo", "óptimo", "máximo", "destacado", "notable", "sobresaliente", "excepcional", "único", "exclusivo", "selecto", "premium", "solidez", "firmeza", "integridad", "lealtad", "dinamismo", "ejecución", "alcance", "desempeño", "capacidad", "inteligente"]

    anglicismos = ["pipeline", "forecast", "lead", "target", "budget", "business", "meeting", "call", "feedback", "report", "follow-up", "deadline", "schedule", "planning", "marketing", "sales", "manager", "ceo", "staff", "stock", "partner", "account", "key account", "stakeholder", "b2b", "b2c", "kick-off", "brainstorming", "networking", "pitch", "speech", "storytelling", "insight", "driver", "gap", "pain point", "focus", "know-how", "expertise", "background", "skill", "mindset", "workflow", "task", "check", "update", "asap", "on hold", "stand by", "briefing", "debriefing", "recap", "forward", "attach", "kpi", "roi", "revenue", "profit", "margin", "cash flow", "churn", "growth", "share", "fee", "pricing", "ticket", "online", "offline", "e-commerce", "mailing", "newsletter", "landing page", "webinar", "demo", "trial", "freemium", "premium", "commodity", "niche", "trend", "hype", "branding", "awareness", "conversion", "traffic", "inbound", "outbound", "cold calling", "cross-selling", "up-selling", "pack", "outsourcing", "junior", "senior", "deal", "closing", "win-win", "engagement", "performance", "ranking", "headhunter", "spam", "dashboard", "crm"] 

    # Unir todo el texto del vendedor
    # vendedor_texto as array of phrases (split by '.' for now, lower)
    vendedor_texto = [f.strip() for t in transcript if t["speaker"] == "vendedor" for f in t["text"].lower().replace("?", ".").replace("!", ".").split(".") if f.strip()]

    translator = str.maketrans('', '', string.punctuation + "¿!")
    palabras_limpias = [word.translate(translator) for frase in vendedor_texto for word in frase.split()]

    # Now frases == vendedor_texto (already split by punctuation, stripped, lower)
    frases = vendedor_texto

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
    puntuacion = max(0, min(100, 70 - penalizacion + bonificacion))

    # ---- Calcular feedback -----
    feedback = json.loads(feedback_claridad(transcript))

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
        "feedback": feedback['señales']
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
    if ratio < 0.1: 
        penalizacion += 100
    elif 0.1 <= ratio <= 0.2:
        penalizacion += 50
    elif 0.2 < ratio <= 0.3:
        penalizacion += 25
    elif 0.3 < ratio <= 0.4:
        penalizacion += 10
    elif 0.4 < ratio <= 0.5:
        penalizacion += 10
    elif 0.5 < ratio <= 0.6:
        penalizacion += 10
    elif 0.6 < ratio <= 0.7:
        penalizacion += 25
    elif 0.7 < ratio <= 0.8:
        penalizacion += 50
    elif 0.8 < ratio <= 0.9:
        penalizacion += 75
    elif ratio > 0.9:
        penalizacion += 100

    # ---- Puntuación final ----
    puntuacion = max(0, min(100, 70 - penalizacion + bonificacion))

    # ---- Feedback ----
    feedback = json.loads(feedback_participacion(transcript))
    
    return {
        "palabras_cliente": palabras_cliente, 
        "palabras_vendedor": palabras_vendedor, 
        "ratio": ratio,
        "puntuacion": puntuacion,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion,
        "escucha_activa": gpt_escucha_activa,
        "n_escuchas": num_escucha,
        "feedback": f"El porcentaje de participación del vendedor es del {ratio*100:.2f}%. Interrupciones: {feedback['señales']}"
    }

### Cobertura de temas y palabras clave
def calcular_cobertura_temas_json(transcript,num_temas=6):

    penalizacion = 0
    bonificacion = 0

    ## Detector de palabras clave con GPT
    # INSERT_YOUR_CODE
    gpt_temas_clave = json.loads(temas_clave(transcript))

    num_temas_abordados = gpt_temas_clave['n']
    señales_temas = gpt_temas_clave['señales']
    feedback_temas_clave = gpt_temas_clave.get('feedback')

    # Puedes usar num_temas_abordados y señales_temas como quieras para penalizar o bonificar
    num_temas_olvidados = num_temas - num_temas_abordados
    penalizacion += num_temas_olvidados*20

    ## Detector de proximos pasos con GPT
    gpt_proximos_pasos = json.loads(proximos_pasos(transcript))
    
    indicador = bool(gpt_proximos_pasos["indicador"])
    señales_proximos_pasos = gpt_proximos_pasos["señales"]
    
    output_gpt = gpt_proximos_pasos  # Store the full GPT response
    bonificacion = 10 * indicador
    
    
    # ---- Puntuación final ----
    puntuacion = max(0, min(100, 90 - penalizacion + bonificacion))
    
    return {
        "puntuacion": puntuacion,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion,
        "temas_olvidados": num_temas_olvidados,
        #"objecion_no_resuelta": objecion_detectada and not respuesta,
        "proximos_pasos": indicador,
        "señales_temas": señales_temas,
        "señales_proximos_pasos": señales_proximos_pasos,
        "output_gpt": output_gpt,
        "feedback": feedback_temas_clave
    }

# ### Cobertura de temas y palabras clave (mejorado con LLMs)
def calcular_cobertura_temas_old(transcript,num_temas=6):
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
    gpt_proximos_pasos = json.loads(proximos_pasos(transcript))
    # Try to extract boolean or number from GPT response
    # First try to find a boolean pattern
    bool_match = re.search(r'(true|false)', gpt_proximos_pasos, re.IGNORECASE)
    if bool_match:
        bool_value = bool_match.group(1).lower()
        proximos_pasos_bool = 1 if bool_value in ['true'] else 0
        señales_proximos_pasos = []
    else:
        # Try to find a number pattern
        match = re.search(r"señales de proximos pasos:\s*(\d+)", gpt_proximos_pasos, re.IGNORECASE)
        if match:
            proximos_pasos_bool = int(match.group(1))
            # Extraer las señales concretas si están listadas tras los dos puntos
            sig_pos = gpt_proximos_pasos.find(match.group(1)) + len(match.group(1))
            restantes = gpt_proximos_pasos[sig_pos:].strip()
            señales_proximos_pasos = [l.strip() for l in restantes.split('\n') if l.strip()]
        else:
            # Try to find any number in the response as fallback
            numbers = re.findall(r'\d+', gpt_proximos_pasos)
            proximos_pasos_bool = int(numbers[0]) if numbers else 0
            # Como señales, tomar todas las líneas no vacías tras cualquier "proximos pasos:" o después de los números encontrados
            señales_proximos_pasos = []
            fallback_match = re.search(r"proximos pasos:([^\n]*)", gpt_proximos_pasos, re.IGNORECASE)
            if fallback_match:
                after_header = fallback_match.group(1)
                señales_proximos_pasos = [l.strip() for l in after_header.split('\n') if l.strip()]
            elif numbers:
                idx = gpt_proximos_pasos.find(numbers[0]) + len(numbers[0])
                restantes = gpt_proximos_pasos[idx:].strip()
                señales_proximos_pasos = [l.strip() for l in restantes.split('\n') if l.strip()]
    
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
        "bool_value": bool_value,
        "proximos_pasos": proximos_pasos_bool,
        "señales_temas": señales_temas,
        "señales_proximos_pasos": señales_proximos_pasos,
        "output_gpt": output_gpt
    }

### Indice de preguntas (Aquí hay que darle una pensadica)
def calcular_indice_preguntas(transcript):
    # Definiciones de sets de preguntas

    gpt_index_of_questions = json.loads(index_of_questions(transcript))
    
    total_preguntas = gpt_index_of_questions['n_total']
    count_cerradas = gpt_index_of_questions['n_cerradas']
    count_sondeo = gpt_index_of_questions['n_sondeo']
    count_irrelevantes = gpt_index_of_questions['n_irrelevantes']
    
    penalizacion = 0
    bonificacion = 0
    
    # Penalización si cerradas > 60% del total
    if total_preguntas > 0 and (count_cerradas / total_preguntas) > 0.6:
        penalizacion += 15
    
    # Penalización por irrelevantes
    penalizacion += count_irrelevantes * 10
    
    # Bonificación por sondeo
    bonificacion = min(count_sondeo * 10,40)
    
    # Score final
    puntuacion = max(0, min(100,  70 - penalizacion + bonificacion))

    # Feedback
    feedback = gpt_index_of_questions['feedback']
    
    return {
        "puntuacion": puntuacion,
        "total_preguntas": total_preguntas,
        #"preguntas": preguntas,
        "cerradas": count_cerradas,
        "sondeo": count_sondeo,
        "irrelevantes": count_irrelevantes,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion,
        "feedback": feedback
    }

### PPM y variabilidad
def calcular_ppm_variabilidad(transcript):
    # Consideramos solo al vendedor
    turnos_vendedor = [t for t in transcript if t["speaker"] == "vendedor"]    
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
    if media_ppm < 100:
        penalizacion += 100
        feedback_ppm = f"Velocidad de habla demasiado lenta ({media_ppm:.1f} PPM). Intenta aumentar el ritmo para mantener la atención del cliente."
    elif 100 <= media_ppm < 120:
        penalizacion += 60
        feedback_ppm = f"Velocidad de habla lenta ({media_ppm:.1f} PPM). Considera acelerar hacia el rango óptimo (130-150 PPM)."
    elif 120 <= media_ppm < 130:
        penalizacion += 30
        feedback_ppm = f"Velocidad de habla cercana al óptimo ({media_ppm:.1f} PPM), pero con margen de mejora. Intenta acercarte más al rango de 130-150 PPM."
    elif 130 <= media_ppm <= 150:
        penalizacion += 0
        feedback_ppm = f"Excelente velocidad de habla ({media_ppm:.1f} PPM). Te encuentras en el rango óptimo (130-150 PPM) para una comunicación clara y efectiva."
    elif 150 < media_ppm <= 160:
        penalizacion += 30
        feedback_ppm = f"Velocidad de habla cercana al óptimo ({media_ppm:.1f} PPM), pero con margen de mejora. Intenta acercarte más al rango de 130-150 PPM."
    elif 160 < media_ppm <= 180:
        penalizacion += 60
        feedback_ppm = f"Velocidad de habla rápida ({media_ppm:.1f} PPM). Considera desacelerar hacia el rango óptimo (130-150 PPM)."
    else:  # media_ppm > 180
        penalizacion += 100
        feedback_ppm = f"Velocidad de habla demasiado rápida ({media_ppm:.1f} PPM). Intenta disminuir el ritmo para asegurar claridad y comprensión."

    
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
        "bonificacion": bonificacion,
        "feedback": feedback_ppm
    }

async def calcular_objetivo_principal(transcript, course_id, stage_id):

    stage_details = await get_courses_details(course_id, stage_id)
    gpt_objetivo = json.loads(objetivo(transcript, objetivo=stage_details[0]["stage_objectives"]))

    indicador = bool(gpt_objetivo["indicador"])
    señales = gpt_objetivo["señales"]

    return {
        "accompplished": indicador,
        "señales": señales
    }

## Scoring function
async def get_conver_scores(transcript, course_id, stage_id):
    # Factores de ponderación
    pesos = {
        "muletillas_pausas": 0.15,
        "claridad": 0.15,
        "participacion": 0.25,
        "cobertura": 0.15,
        "preguntas": 0.20,
        "ppm": 0.10
    }

    palabras_totales = sum(len(turn["text"].split()) for turn in transcript)
        
    if palabras_totales > 20:

        # Evaluaciones individuales
        res_muletillas = calcular_muletillas(transcript)
        res_claridad = calcular_claridad(transcript)
        res_participacion = calcular_participacion_dinamica(transcript)
        res_cobertura = calcular_cobertura_temas_json(transcript)
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
        feedback = { 
            "muletillas_pausas": res_muletillas["feedback"],
            "claridad": res_claridad["feedback"],
            "participacion": res_participacion["feedback"],
            "cobertura": res_cobertura["feedback"],
            "preguntas": res_preguntas["feedback"],
            "ppm": res_ppm["feedback"]
        }
        objetivo = await calcular_objetivo_principal(transcript, course_id, stage_id)
    else: 
        scores = {
            "muletillas_pausas": 0,
            "claridad": 0,
            "participacion": 0,
            "cobertura": 0,
            "preguntas": 0,
            "ppm": 0
        } 

        feedback = {"feedback": "No hay suficientes palabras para evaluar"}
        objetivo = {
        "accompplished": False,
        "señales": "Objetivo no Cumplido"
    }
    # Calcular puntuación ponderada global
    puntuacion_final = sum(scores[k] * pesos[k] for k in scores)
    return {
        "puntuacion_global": round(puntuacion_final, 1),
        "detalle": scores,
        "feedback": feedback,
        "objetivo": objetivo
    }

if __name__ == "__main__":
    transcript_demo = [
    {
        "speaker": "vendedor", 
        "text": "Hola, buenas tardes. Bienvenido a nuestra exposición virtual, eh... mi nombre es Carlos. Veo que se ha interesado justo por el nuevo Conversa XL a través de la web. Tiene buen ojo, es la unidad que acabamos de recibir esta misma mañana y ya está disponible para reserva inmediata.", 
        "duracion": 18
    },
    {
        "speaker": "cliente", 
        "text": "Hola Carlos. Sí, la verdad es que estaba buscando algo más grande porque la familia ha crecido y mi coche actual se nos ha quedado minúsculo.", 
        "duracion": 12
    },
    {
        "speaker": "vendedor", 
        "text": "Le entiendo perfectamente. El espacio es vital. Déjeme decirle que hemos cambiado totalmente el **mindset** de diseño para enfocarnos en familias como la suya. Fíjese en las fotos del catálogo que le acabo de compartir; esas líneas no solo son estética, son refuerzos de acero al boro. En seguridad somos líderes: 5 estrellas Euro NCAP para que no tenga ningún miedo al llevar a sus hijos.", 
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
        "text": "Pues mire los datos técnicos que le envío. Tenemos 650 litros de capacidad real. Aquí le caben dos carritos si hace falta. Además, la boca de carga es muy baja para que no se deje la espalda levantando peso. Y los asientos traseros son individuales; no va a tener problema para colocar tres sillas infantiles.", 
        "duracion": 35
    },
    {
        "speaker": "cliente", 
        "text": "Oye, pues es verdad que se ve inmenso. ¿Y de tecnología qué tal va? Porque no quiero algo que sea muy complicado de usar, la pantalla esa parece una nave espacial.", 
        "duracion": 15
    },
    {
        "speaker": "vendedor", 
        "text": "Parece compleja, pero el **feedback** que recibimos es que se aprende a usar en cinco minutos. Mire, le voy a ser sincero, la conectividad hoy en día nos facilita la vida y usted necesita gestionar las llamadas y el mapa por voz, sin soltar el volante en ningún momento bajo ninguna circunstancia.", 
        "duracion": 40
    },
    {
        "speaker": "cliente", 
        "text": "Ya, mientras no se cuelgue... ¿Y el motor? Hago muchos kilómetros para ir al trabajo y la gasolina está carísima.", 
        "duracion": 10
    },
    {
        "speaker": "vendedor", 
        "text": "No se preocupe por eso. Montamos un motor híbrido auto-recargable. El coche gestiona solo cuándo usar la batería. En ciudad va a ir casi siempre en eléctrico, reduciendo el gasto de combustible a la mitad comparado con su coche actual. Es eficiencia pura.", 
        "duracion": 28
    },
    {
        "speaker": "cliente", 
        "text": "Suena bien lo del ahorro. Pero vamos a lo doloroso... he estado mirando el modelo similar de la marca alemana y se me va de precio. Imagino que este, siendo nuevo y con tanta tecnología, costará un ojo de la cara.", 
        "duracion": 18
    },
    {
        "speaker": "vendedor", 
        "text": "Mmmmm, eehhh, Para nada, ahí es donde el Conversa XL brilla. Sabemos que el **budget** familiar es sagrado. Al ser una gestión online, nuestro precio final está actualmente un 12% por debajo de la competencia directa. Básicamente, se lleva más coche por menos dinero.", 
        "duracion": 32
    },
    {
        "speaker": "cliente", 
        "text": "Un 12% es bastante diferencia... ¿Y tenéis financiación? Porque no quería descapitalizarme ahora mismo pagándolo todo de golpe.", 
        "duracion": 12
    },
    {
        "speaker": "vendedor", 
        "text": "Sí, tenemos un plan flexible totalmente digital. Podemos ajustar la entrada y dejar una cuota muy cómoda. De hecho, si lo tramitamos ahora por el portal, le incluyo el envío a domicilio sin coste adicional.", 
        "duracion": 22
    },
    {
        "speaker": "cliente", 
        "text": "Pues con ese descuento y el envío a casa me habéis convencido. Me cuadra todo. ¿Qué tengo que hacer para confirmar la compra ahora mismo?", 
        "duracion": 12
    },
    {
        "speaker": "vendedor", 
        "text": "¡Fantástico! Le acabo de enviar un enlace seguro a su correo. Solo tiene que subir una foto de su DNI y completar el formulario de la financiera. En cuanto lo reciba, bloqueamos el coche para usted y empezamos con la gestión del envío.", 
        "duracion": 25
    }]

    # Evaluaciones individuales

    res_muletillas = calcular_muletillas(transcript_demo)
    print("\n" + "="*50)
    print("MULETILLAS Y PAUSAS")
    print("="*50)
    print(res_muletillas)

    res_claridad = calcular_claridad(transcript_demo)
    print("\n" + "="*50)
    print("CLARIDAD")
    print("="*50)
    print(res_claridad)

    res_participacion = calcular_participacion_dinamica(transcript_demo)
    print("\n" + "="*50)
    print("PARTICIPACIÓN Y DINÁMICA")
    print("="*50)
    print(res_participacion)

    res_cobertura = calcular_cobertura_temas_json(transcript_demo)
    print("\n" + "="*50)
    print("COBERTURA DE TEMAS")
    print("="*50)
    print(res_cobertura)

    res_preguntas = calcular_indice_preguntas(transcript_demo)
    print("\n" + "="*50)
    print("ÍNDICE DE PREGUNTAS")
    print("="*50)
    print(res_preguntas)

    res_ppm = calcular_ppm_variabilidad(transcript_demo)
    print("\n" + "="*50)
    print("PPM Y VARIABILIDAD")
    print("="*50)
    print(res_ppm)
    
    print("\n" + "="*50)
