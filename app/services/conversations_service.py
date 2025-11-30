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
    , updated_at, couser_id, fillerwords_scoring, clarity_scoring
    , participation_scoring, keythemes_scoring, indexofquestions_scoring
    , rhythm_scoring
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
    , updated_at, couser_id, fillerwords_scoring, clarity_scoring
    , participation_scoring, keythemes_scoring, indexofquestions_scoring
    , rhythm_scoring
    FROM conversaApp.conversations
    WHERE user_id = $1
    ORDER BY start_timestamp DESC
    """
    
    results = await execute_query(query, user_id)
    return [dict(row) for row in results]

async def create_conversation(user_id: UUID, course_id: UUID) -> Optional[Dict]:
    """
    Create new conversation for user
    Note: course_id accepted for compatibility but not stored in DB
    """
    query = """
    INSERT INTO conversaApp.conversations (user_id,couser_id, conversation_id, start_timestamp, status, created_at, updated_at)
    VALUES ($1,$2, gen_random_uuid(), now(), 'open', now(), now())
    RETURNING conversation_id, user_id, start_timestamp, status, created_at
    """
    
    result = await execute_query_one(query, user_id, course_id)
    
    if result:
        return dict(result)
    return None

async def close_conversation(conversation_id: UUID, user_id: UUID) -> Optional[Dict]:
    """
    Close conversation
    """
    query = """
    UPDATE conversaApp.conversations SET status = 'FINISHED', end_timestamp = now()
     WHERE conversation_id = $1 AND user_id = $2
    """
    await execute_query(query, conversation_id, user_id)
    return True

async def get_conversation_status(conversation_id: UUID, user_id: UUID) -> Optional[str]:
    print('Gettin conver status')
    query = """
    SELECT status FROM conversaApp.conversations WHERE conversation_id = $1 AND user_id = $2
    """
    result = await execute_query(query, conversation_id, user_id)
    return result[0]["status"]