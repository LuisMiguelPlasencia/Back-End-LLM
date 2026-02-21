"""Conversation profiling (skills) scoring.

This module follows the same structure as the scoring pipeline:
- prompt builders are pure functions (in app.prompting_templates.profiling)
- OpenAI calls are centralized (app.utils.call_gpt)
- OpenAI client creation is centralized (app.utils.openai_client)
"""

import json
from typing import Any, Dict, List

from openai import OpenAI

from app.prompting_templates.profiling.evaluate_prospection import evaluate_prospection
from app.prompting_templates.profiling.evaluate_empathy import evaluate_empathy
from app.prompting_templates.profiling.evaluate_technical_domain import evaluate_technical_domain
from app.prompting_templates.profiling.evaluate_negociation import evaluate_negociation
from app.prompting_templates.profiling.evaluate_resilience import evaluate_resilience
from app.utils.call_gpt import call_gpt
from app.utils.openai_client import get_openai_client

# Helper function to prevent JSON errors from crashing the app
def safe_parse_json(json_str: str, skill_name: str) -> Dict[str, Any]:
    try:
        if not json_str:
            raise ValueError("Empty response from AI")
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"⚠️ Error decoding JSON for {skill_name}: {e}")
        # Return default values so the code doesn't break downstream
        return {"score": 0, "justification": "Error during AI evaluation"}

def _call_and_parse_json(
    client: OpenAI,
    prompt: str,
    skill_name: str,
    *,
    max_retries: int = 3,
    model: str = "gpt-4.1-nano-2025-04-14",
) -> Dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(max_retries):
        try:
            raw = call_gpt(client, prompt, model=model)
            parsed = safe_parse_json(raw, skill_name)
            if parsed.get("justification") != "Error during AI evaluation":
                return parsed
        except Exception as e:
            last_error = e

    if last_error:
        print(f"⚠️ AI evaluation failed for {skill_name}: {last_error}")
    return {"score": 0, "justification": "Error during AI evaluation"}


async def get_conver_skills(
    transcript: List[Dict[str, Any]],
    *,
    client: OpenAI | None = None,
    model: str = "gpt-4.1-nano-2025-04-14",
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates a transcript across all defined skills.
    Returns a dictionary structured by skill containing score and justification.
    
    Return format:
    {
        "skill_name": { "score": int, "justification": str },
        ...
    }
    """

    palabras_totales = sum(len(turn.get("text", "").split()) for turn in transcript)
        
    if palabras_totales > 100:
    
        resolved_client = client or get_openai_client()

        # Build prompts (pure) then call the model (centralized)
        prospection_data = _call_and_parse_json(
            resolved_client,
            evaluate_prospection(transcript),
            "prospection",
            model=model,
        )
        empathy_data = _call_and_parse_json(
            resolved_client,
            evaluate_empathy(transcript),
            "empathy",
            model=model,
        )
        technical_domain_data = _call_and_parse_json(
            resolved_client,
            evaluate_technical_domain(transcript),
            "technical_domain",
            model=model,
        )
        negociation_data = _call_and_parse_json(
            resolved_client,
            evaluate_negociation(transcript),
            "negociation",
            model=model,
        )
        resilience_data = _call_and_parse_json(
            resolved_client,
            evaluate_resilience(transcript),
            "resilience",
            model=model,
        )

        def _truncate(data: Dict[str, Any], limit: int = 499) -> Dict[str, Any]:
            justification = data.get("justification", "")
            return {**data, "justification": justification[:limit]}

        # We return the structure exactly as the consumer function expects it
        # (Keys are the skill names, containing both score and justification)
        return {
            "prospection": _truncate(prospection_data),
            "empathy": _truncate(empathy_data),
            "technical_domain": _truncate(technical_domain_data),
            "negociation": _truncate(negociation_data),
            "resilience": _truncate(resilience_data),
        }
    else:
        return {
            "prospection": { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}, 
            "empathy":  { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}, 
            "technical_domain":  { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}, 
            "negociation":  { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}, 
            "resilience":  { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}
        }


if __name__ == "__main__":
    # Simple test harness
    import asyncio

    sample_transcript = [
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

    async def test():
        skills = await get_conver_skills(sample_transcript)
        print(json.dumps(skills, indent=2))

    asyncio.run(test())