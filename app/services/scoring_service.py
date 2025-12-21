# this program will be imported in realtime_bridge and added to the stop() method (????)
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from app.services.conversations_service import set_conversation_scoring
from scoring_scripts.get_conver_scores import get_conver_scores

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

async def scoring(conv_id, course_id, stage_id):
    transcript = read_msg(conv_id)

    if not transcript:
        print(f"No messages found for conversation_id: {conv_id}")
        return
    scores_detail =  get_conver_scores(transcript, course_id, stage_id)["detalle"]
    feedback = get_conver_scores(transcript, course_id, stage_id)["feedback"]
    puntuacion_global =  get_conver_scores(transcript, course_id, stage_id)["puntuacion_global"]
    objetivo_json =  get_conver_scores(transcript, course_id, stage_id)["objetivo"]
    # Get scores
    fillerwords_scoring = scores_detail.get("muletillas_pausas")
    clarity_scoring = scores_detail.get("claridad")
    participation_scoring = scores_detail.get("participacion")
    keythemes_scoring = scores_detail.get("cobertura")
    indexofquestions_scoring = scores_detail.get("preguntas")
    rhythm_scoring = scores_detail.get("ppm")

    # Get feedback
    fillerwords_feedback = feedback.get("muletillas_pausas")
    clarity_feedback = feedback.get("claridad")
    participation_feedback = feedback.get("participacion")
    keythemes_feedback = feedback.get("cobertura")
    indexofquestions_feedback = feedback.get("preguntas")
    rhythm_feedback = feedback.get("ppm")

    objetivo = objetivo_json.get("puntuacion")

    print("\n📊 Computed Scores:")
    print(f"   Fillerwords: {fillerwords_scoring}")
    print(f"   Clarity: {clarity_scoring}")
    print(f"   Participation: {participation_scoring}")
    print(f"   Key Themes: {keythemes_scoring}")
    print(f"   Index of Questions: {indexofquestions_scoring}")
    print(f"   Rhythm: {rhythm_scoring}\n")

    # Update database
    await set_conversation_scoring(
        fillerwords_scoring,
        clarity_scoring,
        participation_scoring,
        keythemes_scoring,
        indexofquestions_scoring,
        rhythm_scoring,
        fillerwords_feedback, 
        clarity_feedback,
        participation_feedback,
        keythemes_feedback,
        indexofquestions_feedback,
        rhythm_feedback,
        puntuacion_global,
        objetivo,
        conv_id
    )


if __name__ == "__main__":
    import sys
    import uuid
    
    print("=" * 60)
    print("Scoring Service - Test Mode")
    print("=" * 60)
    
    conv_id = '776babce-8bc3-4fa8-ad3c-6e06ce6fb2a3'
    try:
        # Validate UUID format
        uuid.UUID(conv_id)
        print(f"\n🚀 Running scoring for conversation_id: {conv_id}\n")
        scoring(conv_id)
    except ValueError:
        print(f"❌ Error: '{conv_id}' is not a valid UUID")
        sys.exit(1)

