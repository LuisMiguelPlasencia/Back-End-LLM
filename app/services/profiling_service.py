# this program will be imported in realtime_bridge and added to the stop() method (????)
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from app.services.conversations_service import set_conversation_profiling
from scoring_scripts.get_conver_skills import get_conver_skills
from app.services.messages_service import get_conversation_transcript

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

