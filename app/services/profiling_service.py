# this program will be imported in realtime_bridge and added to the stop() method (????)
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from app.services.conversations_service import set_conversation_profiling
from scoring_scripts.get_conver_skills import get_conver_skills

load_dotenv()

# --- DB CONFIG ---
DB_NAME = os.getenv("DB_NAME")
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")

def read_msg(conv_id):
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

    # read from db
    # output: dict with conv 
    query = f"""
    SELECT 
        role,
        content,
        created_at
    FROM conversaapp.messages 
    WHERE conversation_id = '{conv_id}'
    ORDER BY created_at ASC
    """

    df = pd.read_sql(query, conn)

    role_map = {"user": "vendedor", "assistant": "cliente"}
    
    conversation = [
        {
            "speaker": role_map.get(row["role"], row["role"]),
            "text": row["content"],
            "duracion": 10
        }
        for _, row in df.iterrows()
    ]

    # --- CLOSE CONNECTION ---
    conn.close()
    return conversation

async def profiling(conv_id, course_id, stage_id):
    transcript = read_msg(conv_id)

    if not transcript:
        print(f"No messages found for conversation_id: {conv_id}")
        return
    profiling = await get_conver_skills(transcript, course_id, stage_id)

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


if __name__ == "__main__":
    import sys
    import uuid
    
    print("=" * 60)
    print("Scoring Service - Test Mode")
    print("=" * 60)
    
    conv_id = '5f3ab585-9269-4779-aec4-a31d6ec9d559'
    course_id = 'f5950497-103a-47b9-bd76-566da96ac030'
    stage_id  = 'fb3b890c-2255-438c-b49a-d1a81cd68eff'
    try:
        # Validate UUID format
        uuid.UUID(conv_id)
        print(f"\n🚀 Running scoring for conversation_id: {conv_id}\n")
        import asyncio
        asyncio.run(profiling(conv_id, course_id, stage_id))
    except ValueError:
        print(f"❌ Error: '{conv_id}' is not a valid UUID")
        sys.exit(1)

