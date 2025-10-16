# Message service for handling conversation messages
# Manages user messages and generates simple assistant responses
# Note: assistant messages have user_id = NULL (system messages)

from .db import execute_query, execute_query_one
from uuid import UUID
from typing import List, Dict, Optional, Tuple

async def get_conversation_messages(conversation_id: UUID) -> List[Dict]:
    """Get all messages for a conversation, ordered by creation time"""
    query = """
    SELECT id, user_id, conversation_id, role, content, created_at
    FROM conversaApp.messages
    WHERE conversation_id = $1
    ORDER BY created_at ASC
    """
    
    results = await execute_query(query, conversation_id)
    return [dict(row) for row in results]

async def send_message(user_id: UUID, conversation_id: UUID, message: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Send user message and generate assistant response
    Returns tuple of (user_message, assistant_response)
    """
    # Insert user message
    user_query = """
    INSERT INTO conversaApp.messages (id, user_id, conversation_id, role, content, created_at)
    VALUES (gen_random_uuid(), $1, $2, 'user', $3, now())
    RETURNING id, user_id, conversation_id, role, content, created_at
    """
    
    user_message = await execute_query_one(user_query, user_id, conversation_id, message)
    
    if not user_message:
        return None, None
    
    # Generate simple assistant response (static for now)
    assistant_content = f"Received: {message}"
    
    # Insert assistant message (user_id = NULL for system messages)
    assistant_query = """
    INSERT INTO conversaApp.messages (id, user_id, conversation_id, role, content, created_at)
    VALUES (gen_random_uuid(), NULL, $1, 'assistant', $2, now())
    RETURNING id, role, content, created_at
    """
    
    assistant_message = await execute_query_one(assistant_query, conversation_id, assistant_content)
    
    # Update conversation updated_at timestamp
    await execute_query_one(
        "UPDATE conversaApp.conversations SET updated_at = now() WHERE conversation_id = $1",
        conversation_id
    )
    
    return dict(user_message) if user_message else None, dict(assistant_message) if assistant_message else None

