# Conversation service for managing user conversations
# Handles conversation creation and retrieval from conversaApp.conversations
# Note: course_id is accepted in payload but not stored (no field in table)

from .db import execute_query, execute_query_one
from uuid import UUID
from typing import List, Dict, Optional

async def get_user_conversations(user_id: UUID) -> List[Dict]:
    """Get all conversations for a user, ordered by start time (newest first)"""
    query = """
    SELECT conversation_id, user_id, start_timestamp, end_timestamp, status, created_at, updated_at
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
    INSERT INTO conversaApp.conversations (user_id, conversation_id, start_timestamp, status, created_at, updated_at)
    VALUES ($1, gen_random_uuid(), now(), 'open', now(), now())
    RETURNING conversation_id, user_id, start_timestamp, status, created_at
    """
    
    result = await execute_query_one(query, user_id)
    
    if result:
        return dict(result)
    return None
