import pandas as pd
import psycopg2
import os
import numpy as np
from dotenv import load_dotenv
from app.services.conversations_service import get_user_profiling_by_conversations, set_conversation_profiling, set_general_profiling
from scoring_scripts.get_conver_skills import get_conver_skills
from app.services.messages_service import get_conversation_transcript, get_user_profiling_feedbacks
from app.prompting_templates.profiling.general_feedback import (
    general_feedback_empathy,
    general_feedback_prospection,
    general_feedback_negotiation,
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
    negotiation_scoring = profiling.get("negotiation")['score']
    resilience_scoring = profiling.get("resilience")['score']


    # Get feedback
    prospection_feedback = profiling.get("prospection")['justification']
    empathy_feedback = profiling.get("empathy")['justification']
    technical_domain_feedback = profiling.get("technical_domain")['justification']
    negotiation_feedback = profiling.get("negotiation")['justification']
    resilience_feedback = profiling.get("resilience")['justification']

    print("\n👥 Computed Profiling:")
    print(f"   Prospection: {prospection_scoring}")
    print(f"   Empathy: {empathy_scoring}")
    print(f"   Technical domain: {technical_domain_scoring}")
    print(f"   negotiation: {negotiation_scoring}")
    print(f"   Resilience: {resilience_scoring}\n")

    # Update database
    await set_conversation_profiling(
        prospection_scoring,
        empathy_scoring,
        technical_domain_scoring,
        negotiation_scoring,
        resilience_scoring,
        prospection_feedback,
        empathy_feedback,
        technical_domain_feedback,
        negotiation_feedback,
        resilience_feedback,
        conv_id,  # UUID ok
    )

async def general_profiling(user_id):
    client = get_openai_client() # would be interesting to explore how to refactor this so that there is a single client for every operation, instead of initializing it every time that we need it
    
    individual_feedbacks = await get_user_profiling_by_conversations(user_id)
    
    if individual_feedbacks:
        individual_feedbacks_prospection = individual_feedbacks["prospection_feedback"]
        individual_feedbacks_empathy = individual_feedbacks["empathy_feedback"]
        individual_feedbacks_resilience = individual_feedbacks["resilience_feedback"]
        individual_feedbacks_negotiation = individual_feedbacks["negotiation_feedback"]
        individual_feedbacks_technical_domain = individual_feedbacks["technical_domain_feedback"]
        avg_prospection_score = np.mean(individual_feedbacks["prospection_scoring"])
        avg_empathy_score = np.mean(individual_feedbacks["empathy_scoring"])
        avg_resilience_score = np.mean(individual_feedbacks["resilience_scoring"])
        avg_negotiation_score = np.mean(individual_feedbacks["negotiation_scoring"])
        avg_technical_domain_score = np.mean(individual_feedbacks["technical_domain_scoring"])
    else:
        individual_feedbacks_prospection = []
        individual_feedbacks_empathy = []
        individual_feedbacks_resilience = []
        individual_feedbacks_negotiation = []
        individual_feedbacks_technical_domain = []
        avg_prospection_score = 0
        avg_empathy_score = 0
        avg_resilience_score = 0
        avg_negotiation_score = 0
        avg_technical_domain_score = 0

    min_list_size = min(
        len(individual_feedbacks_prospection),
        len(individual_feedbacks_empathy),
        len(individual_feedbacks_resilience),
        len(individual_feedbacks_negotiation),
        len(individual_feedbacks_technical_domain)
    )
    if min_list_size > 0:
        prospection_feedback = call_gpt(client, general_feedback_prospection(individual_feedbacks_prospection), ensure_json=False)
        empathy_feedback = call_gpt(client, general_feedback_empathy(individual_feedbacks_empathy), ensure_json=False)
        negotiation_feedback = call_gpt(client, general_feedback_negotiation(individual_feedbacks_negotiation), ensure_json=False)
        resilience_feedback = call_gpt(client, general_feedback_resilience(individual_feedbacks_resilience), ensure_json=False)
        technical_domain_feedback = call_gpt(client, general_feedback_technical_domain(individual_feedbacks_technical_domain), ensure_json=False)
    else:
        print(f"No individual feedbacks found for user_id: {user_id}. Setting general feedbacks to empty strings.")
        prospection_feedback = ""
        empathy_feedback = ""
        negotiation_feedback = ""
        resilience_feedback = ""
        technical_domain_feedback = ""
    
    await set_general_profiling(
        avg_prospection_score,
        avg_empathy_score,
        avg_technical_domain_score,
        avg_negotiation_score,
        avg_resilience_score,
        prospection_feedback,
        empathy_feedback,
        technical_domain_feedback,
        negotiation_feedback,
        resilience_feedback,
        user_id
    )
    # return {
    #     "general_feedback_prospection": prospection_feedback,
    #     "general_feedback_empathy": empathy_feedback,
    #     "general_feedback_negotiation": negotiation_feedback,
    #     "general_feedback_resilience": resilience_feedback,
    #     "general_feedback_technical_domain": technical_domain_feedback,
    #     "avg_prospection_score": avg_prospection_score,
    #     "avg_empathy_score": avg_empathy_score,
    #     "avg_negotiation_score": avg_negotiation_score,
    #     "avg_resilience_score": avg_resilience_score,
    #     "avg_technical_domain_score": avg_technical_domain_score,
    # }
    
if __name__ == "__main__":
    # Example usage of general_profiling function
    import asyncio
    user_ids = [
        "d7be611e-f739-4656-bba8-a0b9e49dc8ec",
        # "87294667-86b2-4f73-9393-568a21b107f1",
        # "6e5efe10-0150-4b40-9d2a-50a11172c1b3",
        # "ae1ed3b5-0ea0-4ad5-9565-fec1e4ef1ee7",
        # "811f8c85-8b9e-4da4-878d-10b43ab54ef4",
        # "84d5caca-b336-4d34-bf38-3ae9bc621c5f"
    ]
    for user_id in user_ids:
        print(f"Running general profiling for user_id: {user_id}")
        asyncio.run(general_profiling(user_id))