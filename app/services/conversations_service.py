# Conversation service for managing user conversations
# Handles conversation creation and retrieval from conversaApp.conversations
# Note: course_id is accepted in payload but not stored (no field in table)

from tokenize import String
from .db import execute_query, execute_query_one
from uuid import UUID
from typing import List, Dict, Optional

async def get_conversation_details(conversation_id: UUID) -> Optional[Dict]:
    """Get conversation details for a conversation ID"""
    query = """
    SELECT conversation_id, start_timestamp, end_timestamp, status, created_at
    , updated_at, course_id, general_score, fillerwords_scoring, clarity_scoring
    , participation_scoring, keythemes_scoring, indexofquestions_scoring
    , rhythm_scoring, fillerwords_feedback, clarity_feedback, participation_feedback
    , keythemes_feedback, indexofquestions_feedback, rhythm_feedback
    FROM conversaApp.conversations
    WHERE conversation_id = $1
    ORDER BY start_timestamp DESC
    """
    
    results = await execute_query(query, conversation_id)
    return [dict(row) for row in results]

async def get_user_conversations(user_id: UUID) -> List[Dict]:
    """Get all conversations for a user, ordered by start time (newest first)"""
    query = """
    SELECT conversation_id, start_timestamp, end_timestamp, status, created_at
    , updated_at, course_id, fillerwords_scoring, clarity_scoring
    , participation_scoring, keythemes_scoring, indexofquestions_scoring
    , rhythm_scoring, fillerwords_feedback, clarity_feedback, participation_feedback
    , keythemes_feedback, indexofquestions_feedback, rhythm_feedback
    FROM conversaApp.conversations
    WHERE user_id = $1
    ORDER BY start_timestamp DESC
    """
    
    results = await execute_query(query, user_id)
    return [dict(row) for row in results]

async def create_conversation(user_id: UUID, course_id: UUID, stage_id: UUID) -> Optional[Dict]:
    """
    Create new conversation for user
    Note: course_id accepted for compatibility but not stored in DB
    """
    query = """
    INSERT INTO conversaApp.conversations (user_id, course_id, stage_id, conversation_id, start_timestamp, status, created_at, updated_at)
    VALUES ($1,$2,$3, gen_random_uuid(), now(), 'OPEN', now(), now())
    RETURNING conversation_id, user_id, course_id, stage_id, start_timestamp, status, created_at
    """
    
    result = await execute_query_one(query, user_id, course_id, stage_id)
    
    if result:
        return dict(result)
    return None

async def close_conversation(user_id: UUID, conversation_id: UUID) -> Optional[Dict]:
    """
    Close conversation
    """
    query = """
    UPDATE conversaApp.conversations SET status = 'FINISHED', end_timestamp = now()
    WHERE user_id = $1 AND conversation_id = $2
    """
    await execute_query(query, user_id, conversation_id)
    return True

async def get_conversation_status(conversation_id: UUID, user_id: UUID) -> Optional[str]:
    print('Gettin conver status')
    query = """
    SELECT status FROM conversaApp.conversations WHERE conversation_id = $1 AND user_id = $2
    """
    row = await execute_query_one(query, conversation_id, user_id)
    if not row:
        return None
    return row["status"]

async def set_conversation_scoring(
    fillerwords_scoring: float, 
    clarity_scoring: float, 
    participation_scoring: float, 
    keythemes_scoring: float, 
    indexofquestions_scoring: float, 
    rhythm_scoring: float, 
    fillerwords_feedback: str, 
    clarity_feedback: str, 
    participation_feedback: str, 
    keythemes_feedback: str, 
    indexofquestions_feedback: str, 
    rhythm_feedback: str, 
    puntuacion_global: float, 
    conv_id: UUID) -> Optional[str]:
    print('Setting conversation scoring')
    query = """
    UPDATE conversaapp.conversations
    SET
        fillerwords_scoring=$1,
        clarity_scoring=$2,
        participation_scoring=$3,
        keythemes_scoring=$4,
        indexofquestions_scoring=$5,
        rhythm_scoring=$6,
        fillerwords_feedback=$7,
        clarity_feedback=$8,
        participation_feedback=$9,
        keythemes_feedback=$10,
        indexofquestions_feedback=$11,
        rhythm_feedback=$12,
        updated_at=now(),
        general_score=$13
    WHERE conversation_id=$14
    """
    row = await execute_query_one(
        query,
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
        conv_id,  # UUID ok
    )

