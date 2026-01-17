import asyncio
import json
import os
import re
import string
import sys
from collections import Counter

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from app.prompting_templates.scoring.active_listening import active_listening
from app.prompting_templates.scoring.clarity import clarity
from app.prompting_templates.scoring.goal import goal
from app.prompting_templates.scoring.index_of_questions import index_of_questions
from app.prompting_templates.scoring.key_themes import key_themes
from app.prompting_templates.scoring.next_steps import next_steps
from app.prompting_templates.scoring.participation import participation
from app.services.courses_service import get_courses_details
from app.services.db import execute_query_one
from app.utils.call_gpt import call_gpt

sys.path.insert(0, "../../src")
load_dotenv()

OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
client = OpenAI(api_key=OPENAI_TOKEN)


async def get_key_themes(course_id, stage_id):
    query = """ 
    SELECT key_themes FROM conversaconfig.course_stages WHERE course_id = $1 AND stage_id = $2
    """
    results = await execute_query_one(query, course_id, stage_id)
    return results['key_themes'] if results else None



# ### Muletillas
def calcular_muletillas(transcript, duracion=None, muletillas=None):
    if muletillas is None:
        muletillas = ["eh", "ehh", "ehhh", "ehhhh", "ehhhhh", "he", "hee", "ehm", "ehmm", "em", "emm", "emmm", "emmmm", "eeem", "eeemm", "e-eh", "hem", "hemm", "uh", "uhh", "uhhh", "uhhhh", "uhhhhh", "uhm", "uhmm", "umm", "ummm", "ummmm", "umh", "hum", "humm", "hummm", "humn", "mmm", "mmmm", "mmmmm", "mmmh", "mmmhh", "mmh", "mm-hm", "mhm", "m-hm", "mjm", "mjum", "m-jm", "ajá", "aja", "ahá", "aha", "aham", "ajam", "ah", "ahh", "ahhh", "ahhhh", "ahhhhh", "oh", "ohh", "ohhh", "ohhhh", "ooh", "oooh", "oho", "o-oh", "wow", "wooo", "wooow", "wou", "wow", "guau", "guaau", "ala", "alaaa", "hala", "halaaa", "uala", "wala", "huala", "anda", "andaa", "andaaa", "ostras", "ostra", "ostia", "ostias", "joder", "jo", "joo", "jooo", "jopé", "jope", "jolines", "jobar", "ay", "ayy", "ayyy", "ayyyy", "ayyyyy", "ayayay", "aiaiai", "uf", "uff", "ufff", "uffff", "buf", "buff", "bufff", "pff", "pfff", "pffff", "pffft", "psch", "pscht", "tch", "tsch", "tsk", "tsk-tsk", "ts", "bah", "bahh", "bahhh", "bua", "buaa", "buaaa", "buaaaa", "puaj", "puaaj", "iugh", "eww", "ewww", "yuck", "yak", "bueno", "bueeeno", "bueeenooo", "buenooo", "buenop", "bue", "bwe", "pues", "pueees", "puuues", "pos", "ps", "pssss", "pus", "este", "esteee", "esteeee", "estem", "estemm", "estep", "osea", "o sea", "osease", "osa", "en plan", "enplan", "enplaaan", "tipo", "tipooo", "es que", "esque", "esqueee", "a ver", "aver", "a veeer", "averrr", "haber", "total", "en fin", "enfiin", "sabes", "saes", "viste", "visteee", "cierto", "claro", "claroo", "clarooo", "ya", "yaa", "yaaa", "yaaaa", "vale", "valee", "valep", "dale", "daale", "dalee", "ok", "okey", "okay", "oki", "okis", "okii", "oki-doki", "sip", "sipi", "sep", "se", "see", "seee", "sizi", "si", "sii", "siii", "siiii", "chi", "shi", "nop", "nopi", "nones", "nanai", "noo", "nooo", "noooo", "ne", "nee", "nel", "ey", "eyy", "eyyy", "hey", "heey", "ei", "eii", "oye", "oyeee", "oyeeee", "escucha", "mira", "mire", "che", "chee", "cheee", "bo", "boludo", "wey", "we", "güey", "guey", "chale", "no mames", "órale", "orale", "híjole", "hijole", "macho", "tío", "tio", "tronco", "cari", "gordi", "bebé", "ups", "uppps", "ops", "oops", "glup", "glups", "argh", "arg", "arghh", "grr", "grrr", "grrrr", "zzz", "zzzz", "muac", "muack", "mwah", "plas", "plof", "pum", "zas", "ja", "jaja", "jajaja", "jajajaja", "je", "jeje", "jejeje", "ji", "jiji", "jijiji", "jo", "jojo", "jojojo", "ju", "juju", "jujuju", "jsjs", "jsjsjs", "kkk", "lol", "lool", "omg", "wtf", "idk", "dunno", "meh", "bleh", "chist", "chis", "shh", "shhh", "shhhh", "silencio", "calla", "ea", "huy", "huyy", "uy", "uyy", "uyyy", "ejem", "ejemejem", "cof", "cofcof", "achís", "ñam", "ñamñam", "gluglu", "hic", "hip", "ding", "dong", "toc", "toc-toc", "ring", "bip", "clic", "click", "pim", "pam", "pum", "bla", "blabla", "blablabla", "etc", "pla", "pli", "plo", "pum", "zasca", "zas", "pimba", "va", "vaaa", "amos", "basicamente", ]
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

    # guarrada temporal para evitar errores cuando gpt devuelve algo que no es un JSON bien formado
    # habrá que pensar una forma mejor de hacerlo o al menos ponerlo más bonito
    def llamar_gpt_hasta_que_este_bien():
        try:
            gpt_clarity = json.loads(call_gpt(client, clarity(transcript)))
        except: 
            print("llamando a gpt otra vez porque no daba un JSON bien formado...")
            llamar_gpt_hasta_que_este_bien()
            
        return gpt_clarity

    gpt_clarity = llamar_gpt_hasta_que_este_bien()

    signals = gpt_clarity['señales']
    feedback = gpt_clarity['feedback']

    number_of_turns_seller = len([t for t in transcript if t["speaker"] == "vendedor"])
    penalty = gpt_clarity['veces_falta_claridad'] / number_of_turns_seller

    # ---- Calcular puntuación final ----
    puntuacion = int(max(100 * (1-penalty), 0))

    return {
        "puntuacion": puntuacion,
        "penalizacion": penalty, 
        "feedback": feedback #f" Señales: {signals}. Feedback: {feedback} "
    }

### Participación y dinámica
def calcular_participacion_dinamica(transcript):

    # guarrada temporal para evitar errores cuando gpt devuelve algo que no es un JSON bien formado
    # habrá que pensar una forma mejor de hacerlo o al menos ponerlo más bonito
    def llamar_gpt_hasta_que_este_bien():
        try:
            gpt_escucha_activa = call_gpt(client, active_listening(transcript))
        except: 
            print("llamando a gpt otra vez porque no daba un JSON bien formado...")
            llamar_gpt_hasta_que_este_bien()
            
        return gpt_escucha_activa

    gpt_escucha_activa = llamar_gpt_hasta_que_este_bien()

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
    bonificacion_escucha_activa = min(num_escucha * 10, 40) # decidimos hacerlo en términos absolutos y no relativos al número de turnos del vendedor ya que hacerlo más de tres veces, por mucho que la conversación sea larga, sería ser un pelota
    penalizacion_ratio_participacion = 0
    
    # Arbol de decision
    if ratio < 0.1: 
        penalizacion_ratio_participacion += 100
    elif 0.1 <= ratio <= 0.2:
        penalizacion_ratio_participacion += 75
    elif 0.2 < ratio <= 0.3:
        penalizacion_ratio_participacion += 25 # no lo penalizamos más porque el bot de momento es bastante pesado
    elif 0.3 < ratio <= 0.4:
        penalizacion_ratio_participacion += 10
    elif 0.4 < ratio <= 0.6:
        penalizacion_ratio_participacion += 0
    elif 0.6 < ratio <= 0.7:
        penalizacion_ratio_participacion += 30
    elif 0.7 < ratio <= 0.8:
        penalizacion_ratio_participacion += 50
    elif 0.8 < ratio <= 0.9:
        penalizacion_ratio_participacion += 75
    elif ratio > 0.9:
        penalizacion_ratio_participacion += 100

    # ---- Interrupciones ---- (lo quitamos de momento porque a partir del transcript, es imposible que un LLM sepa si lo ha interrumpido, ya que se muestra el texto completo del cliente incluso si el vendedor lo corta)
    # guarrada temporal para evitar errores cuando gpt devuelve algo que no es un JSON bien formado
    # habrá que pensar una forma mejor de hacerlo o al menos ponerlo más bonito
    # def llamar_gpt_hasta_que_este_bien():
    #     try:
    #         interrupciones = json.loads(call_gpt(client, participation(transcript)))
    #     except: 
    #         print("llamando a gpt otra vez porque no daba un JSON bien formado...")
    #         llamar_gpt_hasta_que_este_bien()
            
    #     return interrupciones

    # interrupciones = llamar_gpt_hasta_que_este_bien()
    # n_interrupciones = len(interrupciones["señales"])
    # n_turnos_vendedor = len([t for t in transcript if t["speaker"] == "vendedor"])
    # penalizacion_interrupciones = 100*(n_interrupciones/n_turnos_vendedor) if n_interrupciones/n_turnos_vendedor > 0.15 else 0

    # ---- Puntuación final ----
    # puntuacion = max(0, min(100, 70 - penalizacion_ratio_participacion - penalizacion_interrupciones + bonificacion_escucha_activa))
    puntuacion = max(0, min(100, 70 - penalizacion_ratio_participacion + bonificacion_escucha_activa))

    return {
        "palabras_cliente": palabras_cliente, 
        "palabras_vendedor": palabras_vendedor, 
        "ratio": ratio,
        "puntuacion": puntuacion,
        "penalizacion_ratio_participacion": penalizacion_ratio_participacion, 
        # "penalizacion_interrupciones": penalizacion_interrupciones,
        "bonificacion": bonificacion_escucha_activa,
        "escucha_activa": gpt_escucha_activa,
        "n_escuchas": num_escucha,
        # "feedback": f"Tu porcentaje de participación ha sido del {ratio*100:.2f}%. Has mostrado escucha activa en {num_escucha} ocasiones. Has interrumpido al cliente {n_interrupciones} veces."
        "feedback": f"Tu porcentaje de participación ha sido del {ratio*100:.2f}%. Has mostrado escucha activa en {num_escucha} ocasiones."
    }

### Cobertura de temas y palabras clave
async def calcular_cobertura_temas_json(transcript, course_id, stage_id):

    penalizacion = 0
    bonificacion = 0

    ## Detector de palabras clave con GPT
    key_themes_list = await get_key_themes(course_id, stage_id)
    prompt = key_themes(transcript, key_themes_list)

    # guarrada temporal para evitar errores cuando gpt devuelve algo que no es un JSON bien formado
    # habrá que pensar una forma mejor de hacerlo o al menos ponerlo más bonito
    def llamar_gpt_hasta_que_este_bien():
        try:
            gpt_key_themes = json.loads(call_gpt(client, prompt))
        except: 
            print("llamando a gpt otra vez porque no daba un JSON bien formado...")
            llamar_gpt_hasta_que_este_bien()
            
        return gpt_key_themes

    gpt_key_themes = llamar_gpt_hasta_que_este_bien()

    num_temas_olvidados = gpt_key_themes['n_temas_olvidados']
    señales_temas = gpt_key_themes['señales']
    feedback_temas_clave = gpt_key_themes.get('feedback')

    # Puedes usar num_temas_abordados y señales_temas como quieras para penalizar o bonificar
    penalizacion += num_temas_olvidados*20

    ## Detector de proximos pasos con GPT
    def llamar_gpt_hasta_que_este_bien():
        try:
            gpt_next_steps = json.loads(call_gpt(client, next_steps(transcript)))
        except: 
            print("llamando a gpt otra vez porque no daba un JSON bien formado...")
            llamar_gpt_hasta_que_este_bien()
            
        return gpt_next_steps

    gpt_next_steps = llamar_gpt_hasta_que_este_bien()
    
    
    indicador = bool(gpt_next_steps["indicador"])
    señales_proximos_pasos = gpt_next_steps["señales"]
    
    output_gpt = gpt_next_steps  # Store the full GPT response
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

### Indice de preguntas (Aquí hay que darle una pensadica)
def calcular_indice_preguntas(transcript):
    # Definiciones de sets de preguntas
    
    # guarrada temporal para evitar errores cuando gpt devuelve algo que no es un JSON bien formado
    # habrá que pensar una forma mejor de hacerlo o al menos ponerlo más bonito
    def llamar_gpt_hasta_que_este_bien():
        try:
            gpt_index_of_questions = json.loads(call_gpt(client, index_of_questions(transcript)))
        except: 
            print("llamando a gpt otra vez porque no daba un JSON bien formado...")
            llamar_gpt_hasta_que_este_bien()
            
        return gpt_index_of_questions

    gpt_index_of_questions = llamar_gpt_hasta_que_este_bien()
    
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
    penalizacion += count_irrelevantes * 15
    
    # Bonificación por sondeo
    bonificacion = min(count_sondeo * 10,40)
    
    # Score final
    puntuacion = max(0, min(100,  60 - penalizacion + bonificacion))

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
    goal_description = stage_details[0]["stage_objectives"]
    
    # guarrada temporal para evitar errores cuando gpt devuelve algo que no es un JSON bien formado
    # habrá que pensar una forma mejor de hacerlo o al menos ponerlo más bonito
    def llamar_gpt_hasta_que_este_bien():
        try:
            gpt_objetivo = json.loads(call_gpt(client, goal(transcript, goal_description)))
        except: 
            print("llamando a gpt otra vez porque no daba un JSON bien formado...")
            llamar_gpt_hasta_que_este_bien()
            
        return gpt_objetivo

    gpt_objetivo = llamar_gpt_hasta_que_este_bien()
    
    
    indicador = bool(gpt_objetivo["indicador"])
    señales = gpt_objetivo["señales"]

    return {
        "accomplished": indicador,
        "señales": señales
    }

## Scoring function
async def get_conver_scores(transcript, course_id, stage_id):
    # Factores de ponderación
    pesos = {
        "muletillas_pausas": 0.075,
        "claridad": 0.075,
        "participacion": 0.1,
        "cobertura": 0.1,
        "preguntas": 0.075,
        "ppm": 0.075, 
        "objetivo": 0.5

    }

    palabras_totales = sum(len(turn["text"].split()) for turn in transcript)
        
    if palabras_totales > 100:

        # Evaluaciones individuales
        res_muletillas = calcular_muletillas(transcript)
        res_claridad = calcular_claridad(transcript)
        res_participacion = calcular_participacion_dinamica(transcript)
        res_cobertura = await calcular_cobertura_temas_json(transcript, course_id, stage_id)
        res_preguntas = calcular_indice_preguntas(transcript)
        res_ppm = calcular_ppm_variabilidad(transcript) 

        objetivo = await calcular_objetivo_principal(transcript, course_id, stage_id)

        # Extraer puntuaciones
        scores = {
            "muletillas_pausas": res_muletillas["puntuacion"],
            "claridad": res_claridad["puntuacion"],
            "participacion": res_participacion["puntuacion"],
            "cobertura": res_cobertura["puntuacion"],
            "preguntas": res_preguntas["puntuacion"],
            "ppm": res_ppm["puntuacion"], 
            "objetivo": objetivo["accomplished"]
        }
        feedback = { 
            "muletillas_pausas": res_muletillas["feedback"][:499],
            "claridad": res_claridad["feedback"][:499],
            "participacion": res_participacion["feedback"][:499],
            "cobertura": res_cobertura["feedback"][:499],
            "preguntas": res_preguntas["feedback"][:499],
            "ppm": res_ppm["feedback"][:499]
        }
    else: 
        scores = {
            "muletillas_pausas": 0,
            "claridad": 0,
            "participacion": 0,
            "cobertura": 0,
            "preguntas": 0,
            "ppm": 0,
            "objetivo": 0
        } 

        feedback = {
            "muletillas_pausas": "No hay suficientes palabras para evaluar",
            "claridad": "No hay suficientes palabras para evaluar",
            "participacion": "No hay suficientes palabras para evaluar",
            "cobertura": "No hay suficientes palabras para evaluar",
            "preguntas": "No hay suficientes palabras para evaluar",
            "ppm": "No hay suficientes palabras para evaluar"
        }
        objetivo = {
        "accomplished": False,
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
    async def main():
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

        key_themes = await get_key_themes('3eeeda53-7dff-40bc-b036-b608acb89e6f', '1cbbf136-4e7e-49d9-9dec-402d4179bd66')
        print(key_themes)
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

        res_cobertura = await calcular_cobertura_temas_json(
            transcript_demo,
            '3eeeda53-7dff-40bc-b036-b608acb89e6f',
            '1cbbf136-4e7e-49d9-9dec-402d4179bd66'
        )
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

    asyncio.run(main())
