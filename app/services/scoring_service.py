# this program will be imported in realtime_bridge and added to the stop() method (????)
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
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

def scoring(conv_id):
    transcript = read_msg(conv_id)
    if not transcript:
        print(f"No messages found for conversation_id: {conv_id}")
        return
    scores_detail = get_conver_scores(transcript)["detalle"]

    fillerwords_scoring = scores_detail.get("muletillas_pausas")
    clarity_scoring = scores_detail.get("claridad")
    participation_scoring = scores_detail.get("participacion")
    keythemes_scoring = scores_detail.get("cobertura")
    indexofquestions_scoring = scores_detail.get("preguntas")
    rhythm_scoring = scores_detail.get("ppm")

    print("\n📊 Computed Scores:")
    print(f"   Fillerwords: {fillerwords_scoring}")
    print(f"   Clarity: {clarity_scoring}")
    print(f"   Participation: {participation_scoring}")
    print(f"   Key Themes: {keythemes_scoring}")
    print(f"   Index of Questions: {indexofquestions_scoring}")
    print(f"   Rhythm: {rhythm_scoring}\n")

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE conversaapp.conversations
                SET
                    fillerwords_scoring = %s,
                    clarity_scoring = %s,
                    participation_scoring = %s,
                    keythemes_scoring = %s,
                    indexofquestions_scoring = %s,
                    rhythm_scoring = %s,
                    updated_at = now()
                WHERE conversation_id = %s
                """,
                (
                    fillerwords_scoring,
                    clarity_scoring,
                    participation_scoring,
                    keythemes_scoring,
                    indexofquestions_scoring,
                    rhythm_scoring,
                    conv_id,
                ),
            )
            rows_affected = cur.rowcount
            conn.commit()
            
            if rows_affected == 0:
                print(f"⚠️  Warning: No rows updated. Conversation_id '{conv_id}' may not exist in the database.")
                return
            else:
                print(f"✅ Successfully updated {rows_affected} row(s) for conversation_id: {conv_id}")
                print(f"   Fillerwords: {fillerwords_scoring}")
                print(f"   Clarity: {clarity_scoring}")
                print(f"   Participation: {participation_scoring}")
                print(f"   Key Themes: {keythemes_scoring}")
                print(f"   Index of Questions: {indexofquestions_scoring}")
                print(f"   Rhythm: {rhythm_scoring}")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Database error occurred: {e}")
        raise
    except Exception as e:
        conn.rollback()
        print(f"❌ Unexpected error occurred: {e}")
        raise
    finally:
        conn.close()


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

