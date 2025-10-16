# Read routes for data retrieval
# Handles GET requests for courses, conversations, and messages
# Examples:
# curl "http://localhost:8000/read/courses?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/conversation?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/messages?conversation_id=123e4567-e89b-12d3-a456-426614174000"

from fastapi import APIRouter, Query
from uuid import UUID
from ..services.courses_service import get_user_courses
from ..services.conversations_service import get_user_conversations
from ..services.messages_service import get_conversation_messages
from ..utils.responses import error

router = APIRouter(prefix="/read", tags=["read"])

@router.get("/courses")
async def get_courses(user_id: UUID = Query(..., description="User ID to get courses for")):
    """Get courses available to user based on their user type"""
    try:
        courses = await get_user_courses(user_id)
        return courses
    except Exception as e:
        error(500, f"Failed to retrieve courses: {str(e)}")

@router.get("/conversation")
async def get_conversations(user_id: UUID = Query(..., description="User ID to get conversations for")):
    """Get all conversations for a user"""
    try:
        conversations = await get_user_conversations(user_id)
        return conversations
    except Exception as e:
        error(500, f"Failed to retrieve conversations: {str(e)}")

@router.get("/messages")
async def get_messages(conversation_id: UUID = Query(..., description="Conversation ID to get messages for")):
    """Get all messages for a conversation"""
    try:
        messages = await get_conversation_messages(conversation_id)
        return messages
    except Exception as e:
        error(500, f"Failed to retrieve messages: {str(e)}")
