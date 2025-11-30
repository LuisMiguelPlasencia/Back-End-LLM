# Read routes for data retrieval
# Handles GET requests for courses, conversations, and messages
# Examples:
# curl "http://localhost:8000/read/courses?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/conversation?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/messages?conversation_id=123e4567-e89b-12d3-a456-426614174000"

from fastapi import APIRouter, Query
from uuid import UUID
from ..services.courses_service import get_user_courses, get_user_courses_stages, get_courses_details
from ..services.conversations_service import get_conversation_details, get_user_conversations
from ..services.messages_service import get_conversation_messages
from ..utils.responses import error

router = APIRouter(prefix="/read", tags=["read"])

@router.get("/courses")
async def get_courses(user_id: UUID = Query(..., description="User ID to get courses for")):
    """Get courses available to user based on their user type"""
    try:
        print("Fetching courses for user:", user_id)
        courses = await get_user_courses(user_id)
        return courses
    except Exception as e:
        error(500, f"Failed to retrieve courses: {str(e)}")

@router.get("/courses_stages")
async def get_courses_stages(course_id: UUID = Query(..., description="Course ID to get stages for")):
    """Get stages available for a course"""
    try:
        print("Fetching stages for course:", course_id)
        stages = await get_user_courses_stages(course_id)
        return stages
    except Exception as e:
        error(500, f"Failed to retrieve stages: {str(e)}")

@router.get("/courses_details")
async def get_user_courses_details(course_id: UUID = Query(..., description="Course ID to get details for"), stage_id: UUID = Query(..., description="Stage ID to get details for")):
    """Get details for a course and stage"""
    try:
        print("Fetching details for course:", course_id, "and stage:", stage_id)
        details = await get_courses_details(course_id, stage_id)
        return details
    except Exception as e:
        error(500, f"Failed to retrieve details: {str(e)}")

@router.get("/conversation")
async def get_conversation(conversation_id: UUID = Query(..., description="Conversation ID to get conversation details for")):
    """Get conversation details for a conversation ID"""
    try:
        conversation = await get_conversation_details(conversation_id)
        return conversation
    except Exception as e:
        error(500, f"Failed to retrieve conversations: {str(e)}")

@router.get("/conversations")
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
