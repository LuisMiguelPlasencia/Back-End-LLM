import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from app.services.conversations_service import set_conversation_profiling
from scoring_scripts.get_conver_skills import get_conver_skills
from app.services.messages_service import get_conversation_transcript
from app.prompting_templates.profiling.general_feedback import (
    general_feedback_empathy,
    general_feedback_prospection,
    general_feedback_negociation,
    general_feedback_resilience,
    general_feedback_technical_domain,
)
from app.utils.call_gpt import call_gpt
from app.utils.openai_client import get_openai_client

load_dotenv(override=True)

async def profiling(conv_id, course_id, stage_id):
    transcript = await get_conversation_transcript(conv_id)

    if not transcript:
        print(f"No messages found for conversation_id: {conv_id}")
        return
    profiling = await get_conver_skills(transcript)

    # Get scores
    prospection_scoring = profiling.get("prospection")['score']
    empathy_scoring = profiling.get("empathy")['score']
    technical_domain_scoring = profiling.get("technical_domain")['score']
    negociation_scoring = profiling.get("negociation")['score']
    resilience_scoring = profiling.get("resilience")['score']


    # Get feedback
    prospection_feedback = profiling.get("prospection")['justification']
    empathy_feedback = profiling.get("empathy")['justification']
    technical_domain_feedback = profiling.get("technical_domain")['justification']
    negociation_feedback = profiling.get("negociation")['justification']
    resilience_feedback = profiling.get("resilience")['justification']

    print("\n👥 Computed Profiling:")
    print(f"   Prospection: {prospection_scoring}")
    print(f"   Empathy: {empathy_scoring}")
    print(f"   Technical domain: {technical_domain_scoring}")
    print(f"   Negociation: {negociation_scoring}")
    print(f"   Resilience: {resilience_scoring}\n")

    # Update database
    await set_conversation_profiling(
        prospection_scoring,
        empathy_scoring,
        technical_domain_scoring,
        negociation_scoring,
        resilience_scoring,
        prospection_feedback,
        empathy_feedback,
        technical_domain_feedback,
        negociation_feedback,
        resilience_feedback,
        conv_id,  # UUID ok
    )

async def general_profiling(user_id):
    client = get_openai_client() # would be interesting to explore how to refactor this so that there is a single client for every operation, instead of initializing it every time that we need it
    
    # retrieve all individual feedbacks for prospection, empathy, technical domain, negociation and resilience for the given user
        # -> individual_feedbacks_prospection (list) , individual_feedbacks_empathy (list) , ...
    
    individual_feedbacks_prospection = []
    individual_feedbacks_empathy = []
    individual_feedbacks_resilience = []
    individual_feedbacks_negociation = []
    individual_feedbacks_technical_domain = []

    min_list_size = min(
        len(individual_feedbacks_prospection),
        len(individual_feedbacks_empathy),
        len(individual_feedbacks_resilience),
        len(individual_feedbacks_negociation),
        len(individual_feedbacks_technical_domain)
    )
    
    if min_list_size > 0:
        prospection_feedback = call_gpt(client, general_feedback_prospection(individual_feedbacks_prospection), ensure_json=False)
        empathy_feedback = call_gpt(client, general_feedback_empathy(individual_feedbacks_empathy), ensure_json=False)
        negociation_feedback = call_gpt(client, general_feedback_negociation(individual_feedbacks_resilience), ensure_json=False)
        resilience_feedback = call_gpt(client, general_feedback_resilience(individual_feedbacks_negociation), ensure_json=False)
        technical_domain_feedback = call_gpt(client, general_feedback_technical_domain(individual_feedbacks_technical_domain), ensure_json=False)
    else:
        prospection_feedback = ""
        empathy_feedback = ""
        negociation_feedback = ""
        resilience_feedback = ""
        technical_domain_feedback = ""
        
    return {
        "general_feedback_prospection": prospection_feedback,
        "general_feedback_empathy": empathy_feedback,
        "general_feedback_negociation": negociation_feedback,
        "general_feedback_resilience": resilience_feedback,
        "general_feedback_technical_domain": technical_domain_feedback,
    }
    
