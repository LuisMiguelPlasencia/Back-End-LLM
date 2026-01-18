# KPIs Perfil
import json
from typing import Dict, Any

from app.prompting_templates.profiling.call_gpt_utils import call_gpt
from app.prompting_templates.profiling.evaluate_prospection import evaluate_prospection
from app.prompting_templates.profiling.evaluate_empathy import evaluate_empathy
from app.prompting_templates.profiling.evaluate_technical_domain import evaluate_technical_domain
from app.prompting_templates.profiling.evaluate_negociation import evaluate_negociation
from app.prompting_templates.profiling.evaluate_resilience import evaluate_resilience

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

# Note: If your evaluate functions are async, remember to add 'await'
# e.g., await evaluate_prospection(transcript)

async def get_conver_skills(transcript: str) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates a transcript across all defined skills.
    Returns a dictionary structured by skill containing score and justification.
    
    Return format:
    {
        "skill_name": { "score": int, "justification": str },
        ...
    }
    """

    palabras_totales = sum(len(turn["text"].split()) for turn in transcript)
        
    if palabras_totales > 100:
    
        # We parse each result safely
        prospection_data = safe_parse_json(evaluate_prospection(transcript), "prospection")
        empathy_data = safe_parse_json(evaluate_empathy(transcript), "empathy")
        technical_domain_data = safe_parse_json(evaluate_technical_domain(transcript), "technical_domain")
        negociation_data = safe_parse_json(evaluate_negociation(transcript), "negociation")
        resilience_data = safe_parse_json(evaluate_resilience(transcript), "resilience")

        # We return the structure exactly as the consumer function expects it
        # (Keys are the skill names, containing both score and justification)
        return {
            "prospection": prospection_data,
            "empathy": empathy_data,
            "technical_domain": technical_domain_data,
            "negociation": negociation_data,
            "resilience": resilience_data,
        }
    else: 
        return {
            "prospection": { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}, 
            "empathy":  { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}, 
            "technical_domain":  { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}, 
            "negociation":  { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}, 
            "resilience":  { "score": 1, "justification": "No se alcanzó el mínimo de palabras para evaluar"}
        }

