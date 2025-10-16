# KPIs & Scoring function

## KPIs
from collections import Counter
import string
import re
import numpy as np

### Muletillas
def calcular_muletillas(transcript, duracion=None, muletillas=None):
    if muletillas is None:
        muletillas = ["eh", "em", "este", "pues", "entonces", "bueno", "mmm", "osea", "en plan"] 
        pausas = ["ppausaa"] # La pausa deberá ser detectada por el whisper/gpt de turno   

    vendedor_texto = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "vendedor")

    # Eliminar signos de puntuación y tokenizar
    translator = str.maketrans('', '', string.punctuation)
    palabras_limpias = [word.translate(translator) for word in vendedor_texto.split()]

    # Contar muletillas y pausas
    muletillas_usadas = [word for word in palabras_limpias if word in muletillas]
    total_muletillas = len(muletillas_usadas)
    total_pausas = sum(1 for word in palabras_limpias if word in pausas)

    penalizacion = total_muletillas // 5 + total_pausas*10

    # Penalización extra si más del 70% de las muletillas son la misma
    if total_muletillas > 2:
        conteo = Counter(muletillas_usadas)
        muletilla_mas_frecuente, frecuencia = conteo.most_common(1)[0]
        if frecuencia / total_muletillas > 0.7:
            penalizacion += 10

    puntuacion = max(0, 100 - penalizacion)  # nunca bajar de 0

    return  {
        "puntuacion": puntuacion, 
        "penalizacion": penalizacion,
        "total_muletillas": total_muletillas,
        "total_pausas": total_pausas,
        "muletillas_usadas": muletillas_usadas
    }
    
### Claridad y complejidad
def calcular_claridad(transcript):
    # Lista de tecnicismos a detectar
    tecnicismos = [
        "kpi", "roi", "funnel", "pipeline", "crm", "saas", "onboarding", "cloud computing", "escalabilidad", 
        "benchmarking", "sla", "bant", "mql", "sql", "tco", "erp", "seo", "api", "throughput", 
        "lead nurturing", "proof of concept", "poc", "framework"
    ]
    
    # Expresiones de lenguaje positivo
    lenguaje_positivo = [
        "absolutamente", "excelente pregunta", "me encanta esa idea", "claro que sí", "con gusto", 
        "es un placer", "podemos lograr", "le aseguro", "le confirmo", "fantástico", "maravilloso", 
        "por supuesto", "genial", "tiene razón", "lo valoro mucho", "vamos a avanzar", 
        "estoy seguro de que", "lo conseguiremos", "gran punto"
    ]
    
    # Unir todo el texto del vendedor
    vendedor_texto = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "vendedor")

    # Eliminar signos de puntuación para facilitar análisis
    translator = str.maketrans('', '', string.punctuation + "¿¡")
    texto_limpio = vendedor_texto.translate(translator)

    # Dividir en frases por punto, ? o !
    frases = [f.strip() for f in texto_limpio.replace("?", ".").replace("!", ".").split(".") if f.strip()]

    # Inicializar métricas
    penalizacion = 0
    bonificacion = 0
    
    # ---- Penalización por tecnicismos ----
    for term in tecnicismos:
        count = vendedor_texto.count(term)
        penalizacion += 15 * count

    # ---- Penalización por frases largas ----
    for frase in frases:
        palabras = frase.split()
        if len(palabras) > 25:
            penalizacion += 10

    # ---- Bonificación por lenguaje positivo ----
    for expresion in lenguaje_positivo:
        if expresion in vendedor_texto:
            bonificacion += 10
            break  # solo bonificamos una vez aunque haya varias

    # ---- Calcular puntuación final ----
    puntuacion = max(0, min(100, 100 - penalizacion + bonificacion))

    return {
        "puntuacion": puntuacion,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion,
        "num_frases_largas": sum(1 for f in frases if len(f.split()) > 25)
    }
### Participación y dinámica
def calcular_participacion_dinamica(transcript):
    # Heurísticas de interrupciones (puedes ampliar con más expresiones típicas)
    patrones_interrupcion = ["sí", "claro", "vale", "déjame", "espera", "pero"]
    
    # Heurísticas de escucha activa
    patrones_escucha_activa = [
        "como me dijiste", "entiendo que", "lo que comentabas", "si no me equivoco", 
        "resumiendo", "entonces lo que", "si entiendo bien", "según lo que me dices"
    ]
    
    # ---- Calcular palabras totales por speaker ----
    palabras_vendedor = 0
    palabras_cliente = 0
    interrupciones = 0
    escucha_activa = False
    
    for i, turno in enumerate(transcript):
        texto = turno["text"].lower()
        palabras = len(texto.split())
        
        if turno["speaker"] == "vendedor":
            palabras_vendedor += palabras
            
            # Buscar escucha activa
            if any(pat in texto for pat in patrones_escucha_activa):
                escucha_activa = True
                
            # Detectar interrupciones: vendedor habla justo después del cliente con patrón
            if i > 0 and transcript[i-1]["speaker"] == "cliente":
                if any(texto.startswith(pat) for pat in patrones_interrupcion):
                    interrupciones += 1
                    
        elif turno["speaker"] == "cliente":
            palabras_cliente += palabras
    
    total_palabras = palabras_vendedor + palabras_cliente
    
    # ---- Penalizaciones y bonificaciones ----
    penalizacion = 0
    bonificacion = 0
    
    # Interrupciones
    penalizacion += interrupciones * 20
    
    # Monólogo: más del 70% de las palabras
    if total_palabras > 0 and (palabras_vendedor / total_palabras) > 0.7:
        penalizacion += 25
    
    # Escucha activa
    if escucha_activa:
        bonificacion += 15
    
    # ---- Puntuación final ----
    puntuacion = max(0, min(100, 100 - penalizacion + bonificacion))
    
    return {
        "puntuacion": puntuacion,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion,
        "interrupciones": interrupciones,
        "monologo": (palabras_vendedor / total_palabras > 0.7 if total_palabras > 0 else False),
        "escucha_activa": escucha_activa
    }

### Cobertura de temas y palabras clave
def calcular_cobertura_temas(transcript, temas_clave=None):
    # Temas clave esperados. Aquí habrá que hacer un trabajo de customización 
    temas_clave = {
        "siguiente paso": ["siguiente paso", "next step", "seguimiento"],
        "propuesta de valor": ["propuesta de valor", "beneficio", "ventaja competitiva"],
        "precio": ["precio", "coste", "inversión", "tarifa"]
    }
    
    # Palabras clave de "next step"
    palabras_next_step = [
        "agendemos", "enviar", "revisaremos", "próximo", "¿cuándo?", "¿qué día?", "confirmar",
        "¿de acuerdo?", "siguientes pasos", "coordinemos", "pongamos", "paso a seguir", 
        "formalizar", "¿cuál es el mejor momento?", "le parece si", "¿puede usted?", "¿a qué hora?"
    ]
    
    vendedor_texto = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "vendedor")
    cliente_texto  = " ".join(t["text"].lower() for t in transcript if t["speaker"] == "cliente")

    penalizacion = 0
    bonificacion = 0
    
    # ---- Temas clave olvidados ----
    temas_olvidados = []
    for tema, keywords in temas_clave.items():
        if not any(k in vendedor_texto for k in keywords):
            penalizacion += 15
            temas_olvidados.append(tema)
    
    # ---- Objeciones críticas no resueltas ----
    objeciones_cliente = ["precio", "coste", "caro", "elevado", "demasiado"]
    objecion_detectada = any(word in cliente_texto for word in objeciones_cliente)
    
    if objecion_detectada:
        # ¿Responde el vendedor?
        respuesta = any(word in vendedor_texto for word in ["precio", "coste", "inversión", "valor"])
        if not respuesta:
            penalizacion += 30
    
    # ---- Definición de próximo paso ----
    if any(exp in vendedor_texto for exp in palabras_next_step):
        bonificacion += 15
    
    # ---- Puntuación final ----
    puntuacion = max(0, min(100, 100 - penalizacion + bonificacion))
    
    return {
        "puntuacion": puntuacion,
        "penalizacion": penalizacion,
        "bonificacion": bonificacion,
        "temas_olvidados": temas_olvidados,
        "objecion_no_resuelta": objecion_detectada and not respuesta,
        "next_step_definido": bonificacion > 0
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
    
    # Penalización por velocidad extrema
    if media_ppm < 120 or media_ppm > 170:
        penalizacion += 10
    
    # Penalización por variabilidad extrema
    if variabilidad > 30:  # umbral configurable
        penalizacion += 15
    
    # Bonificación por ritmo ideal
    if 130 <= media_ppm <= 150:
        bonificacion += 10
    
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
def evaluar_transcript_global(transcript):
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
    {"speaker": "vendedor", "text": "Buenas tardes Juan, ¿qué tal? ¿Cómo estás? Te llamo a ver para seguir con el tema de la reunión de la semana pasada, que... quedamos en que te llamaría para ver qué te había parecido la propuesta. ¿Qué tal te ha ido la semana? ¿Alguna novedad? Me imagino que sí, claro. Y bueno, supongo que habrás visto los auriculares y todo lo que te mandé, ¿verdad? Y este... a ver, quiero saber qué opinas, porque la verdad es que estamos muy contentos con el producto que tenemos entre manos y bueno, creemos que tiene un potencial increíble para vuestra marca. Ya te comenté que la experiencia de usuario que ofrecemos es superior a todo lo que hay en el mercado, este... a ver, en cuanto a calidad y prestaciones. Y... ¿y bueno, qué me dices?", "duracion": 10},
    {"speaker": "cliente", "text": "Buenas tardes Pedro. Pues la verdad es que...", "duracion": 10},
    {"speaker": "vendedor", "text": "Sí, claro, dime, dime, te escucho. Seguro que tienes alguna pregunta sobre el coste, ¿verdad? A ver, es lo más habitual, porque entiendo que el precio puede parecer un poco elevado a primera vista, pero... y bueno, como te dije, es una inversión que realmente merece la pena. No estamos hablando de unos auriculares más. A ver, estamos hablando de un producto de muy alta gama, con unas características que no vas a encontrar en ningún otro sitio. Me imagino que, este, a ver, lo habrás pensado y... y bueno, seguro que tienes alguna duda concreta. Yo, la verdad, estoy convencido de que os va a encantar. Y bueno, de que vuestros clientes van a estar fascinados con la calidad del sonido, que es, este, a ver, es espectacular.", "duracion": 10},
    {"speaker": "cliente", "text": "Sí, de hecho el precio...", "duracion": 10},
    {"speaker": "vendedor", "text": "Claro, el precio. Y bueno, déjame que te recuerde los puntos clave. A ver, la gran diferencia es el volumen de escucha. Te lo comenté, pero, este, a ver, quiero que te quede claro. Tenemos un 20% más de volumen que la competencia. Es, este, a ver, es una barbaridad. Y bueno, eso permite que el usuario escuche su música, sus podcasts, lo que sea. Este, a ver, en cualquier entorno, sin que le moleste el ruido de fuera. Y sin perder, este, a ver, ni una pise de calidad. Y bueno, eso es una ventaja competitiva muy importante que, este, a ver, os va a diferenciar mucho. Además, este, a ver, si ves cómo está el mercado ahora, todo mundo busca algo que le haga destacar. Y bueno, la calidad de nuestros auriculares es, a ver, es inigualable. Y bueno, es un valor seguro para vosotros. Además, este, a ver, también está el tema de la resistencia al agua. Nuestros auriculares son subacuáticos. Sí, sí, como lo oyes, se pueden sumergir. Y bueno, esto es una maravilla para, a ver, para los deportistas. Y para la gente que vive en zonas con mucha lluvia. Y bueno, para, este, a ver, para cualquier persona que, que quiera que tenga la tranquilidad de que sus auriculares no se van a estropear con este, con un poco de agua. Y bueno, la batería también es un, este, a ver, un punto muy fuerte. Tenemos 12 horas de duración. Eso es el doble de la media. O sea, este, a ver, es que no hay comparación. Es, a ver, la mejor opción del mercado. Y bueno, ¿qué te parece? ¿Verdad que es increíble?", "duracion": 10},
    {"speaker": "cliente", "text": "Sí, la verdad me parece muy bien. Pero tengo una pregunta sobre el...", "duracion": 10},
    {"speaker": "vendedor", "text": "Seguro que sobre las condiciones de pago. Y este, a ver, no te preocupas por eso, lo podemos negociar. Y bueno, estamos abiertos a, este, hablar de los plazos y de los, a ver, de los volúmenes de compra. Sí, este, a ver, si te interesa un pedido grande, podemos, este, a ver, hacer un descuento especial. Y bueno, la idea es que todos salgamos ganando. Y bueno, ¿qué te parece? ¿Verdad que es una propuesta muy, este, muy atractiva? Ya te digo, ¿eh? Con un pedido grande, podríamos, este, a ver, ofrecer un precio por unidad que se ajuste más a vuestro presupuesto inicial. Y bueno, te aseguro que, este, la calidad del producto y, a ver, la satisfacción del cliente compensa, eh, con creces esa inversión. Y, y bueno, además, este, a ver, la marca de auriculares que ofreces dice mucho de ti. Y bueno, ofrecer unos auriculares con estas prestaciones es, a ver, es proyectar una imagen de marca de, de alta calidad y, este, de innovación.", "duracion": 10},
    {"speaker": "cliente", "text": "Sí", "duracion": 10},
    {"speaker": "vendedor", "text": "Me alegro de que lo vías así. Y bueno, mira, para no, eh, para no alargarnos más, ¿qué te parece si te envió la propuesta de nuevo? Pero, este, a ver, con un pequeño resumen de las ventajas competitivas, este, a ver, en Negrita, para que se lo puedas enseñar a tu equipo y, y bueno, que vean que la inversión está más que justificada. Y este, a ver, te aseguro que no os vais a arrepentir. Y, y bueno, podríamos, eh, concertar una reunión con tu equipo si quieres, para, este, a ver, para resolver cualquier duda que tengan. Y, y bueno, si lo ven con más detalle.", "duracion": 10},
    {"speaker": "cliente", "text": "Me parece bien, pero me gustaría...", "duracion": 10},
    {"speaker": "vendedor", "text": "Perfecto, Juan. Y bueno, quedemos así. Te lo envío ahora mismo y, este, a ver, me llama si tienes alguna otra pregunta y, bueno, hablamos la semana que viene para cerrar los, los detalles. Y este, a ver, seguro que todo sale bien. Y, y bueno, un placer.", "duracion": 10},
    {"speaker": "cliente", "text": "Igualmente, Pedro. Hasta el martes.", "duracion": 10}
    ]

    output = evaluar_transcript_global(transcript_demo)
    print(output)
