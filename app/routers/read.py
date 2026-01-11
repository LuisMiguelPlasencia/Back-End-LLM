# Read routes for data retrieval
# Handles GET requests for courses, conversations, and messages
# Examples:
# curl "http://localhost:8000/read/courses?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/conversation?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/messages?conversation_id=123e4567-e89b-12d3-a456-426614174000"

from fastapi import APIRouter, Query, HTTPException
from uuid import UUID
from ..services.courses_service import get_user_courses, get_user_courses_stages, get_courses_details
from ..services.conversations_service import get_conversation_details, get_user_conversations
from ..services.messages_service import get_all_user_conversation_average_scoring_by_stage_company, get_all_user_conversation_scoring_by_stage_company, get_all_user_profiling_by_company, get_conversation_messages, get_all_user_scoring_by_company, get_user_profiling
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

@router.get("/userProfiling")
async def get_user_profilingAPI(user_id: UUID = Query(..., description="User ID to get profiling for")):
    """Get the user profiling score"""
    try:
        # 1. Get the data. Based on your function:
        # - Success (found): returns a dict {...}
        # - Success (not found): returns empty dict {}
        # - Error (exception): returns empty list []
        profiling = await get_user_profiling(user_id)
        
        # 2. Safety check: Handle the case where the DB function returned a list (the error case)
        if isinstance(profiling, list):
            profiling = {}
            
        # 3. Now 'profiling' is guaranteed to be a dictionary, so .get() will work
        result = {
            "name": profiling.get('name') or None,
            "user_id": profiling.get('user_id') or user_id, # Fallback to input user_id
            "general_score": profiling.get('general_score') or None,
            "profile_type": profiling.get('profile_type') or None,
            "empathy_scoring": profiling.get('empathy_scoring') or None,
            "negotiation_scoring": profiling.get('negotiation_scoring') or None,
            "prospection_scoring": profiling.get('prospection_scoring') or None,
            "resilience_scoring": profiling.get('resilience_scoring') or None,
            "technical_domain_scoring": profiling.get('technical_domain_scoring') or None
        }
        return result
        
    except Exception as e:
        # Log the error and return a 500 response
        print(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve profiling: {str(e)}")
## Advanced Routes
##-------------------------------------------------------------
@router.get("/allUserScoreByCompany")
async def get_all_user_score_by_company(company_id: str = Query(..., description="Company ID to get the list of user scores for")):
    """Get all user scores for a company"""
    try:
        user_scores_list = await get_all_user_scoring_by_company(company_id)
        return user_scores_list
    except Exception as e:
        error(500, f"Failed to retrieve messages: {str(e)}")

@router.get("/allUserConversationScoresByStageCompany")
async def get_all_user_conversation_scores_by_stage_company(stage_id: str = Query(..., description="Stage ID to get the list of user scores for"), company_id: str = Query(..., description="Company ID to get the list of user scores for")):
    """Get all user conversation scores for a stage and company"""
    try:
        user_scores_list = await get_all_user_conversation_scoring_by_stage_company(stage_id, company_id)
        return user_scores_list
    except Exception as e:
        error(500, f"Failed to retrieve messages: {str(e)}")

@router.get("/allUserConversationAverageScoresByStageCompany")
async def get_all_user_conversation_average_scores_by_stage_company(stage_id: str = Query(..., description="Stage ID to get the list of user scores for"), company_id: str = Query(..., description="Company ID to get the list of user scores for")):
    """Get all user conversation average scores for a stage and company"""
    try:
        user_scores_list = await get_all_user_conversation_average_scoring_by_stage_company(stage_id, company_id)
        return user_scores_list
    except Exception as e:
        error(500, f"Failed to retrieve messages: {str(e)}")

@router.get("/allUserProfilingByCompany")
async def get_all_user_profiling_by_companyAPI(company_id: str = Query(..., description="Company ID to get the list of user scores for")):
    """Get all user profiling scores for a company"""
    try:
        user_profiling_list = await get_all_user_profiling_by_company(company_id)
        return user_profiling_list
    except Exception as e:
        error(500, f"Failed to retrieve messages: {str(e)}")
