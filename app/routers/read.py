# Read routes for data retrieval
# Handles GET requests for courses, conversations, and messages
# Examples:
# curl "http://localhost:8000/read/courses?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/conversation?user_id=123e4567-e89b-12d3-a456-426614174000"
# curl "http://localhost:8000/read/messages?conversation_id=123e4567-e89b-12d3-a456-426614174000"

from fastapi import APIRouter, Query, HTTPException, Depends
from uuid import UUID
from ..services.courses_service import get_all_courses, get_all_stages, get_user_courses, get_user_courses_stages, get_courses_details
from ..services.conversations_service import get_conversation_details, get_user_conversations
from ..services.messages_service import get_all_user_conversation_average_scoring_by_stage_company, get_all_user_conversation_scoring_by_stage_company, get_all_user_profiling_by_company, get_conversation_messages, get_all_user_scoring_by_company, get_user_profiling, get_company_dashboard_stats, get_user_journey, get_dashboard_stats, get_company_announcements
from ..utils.responses import error
from app.services.auth_service import validate_user
from app.services.payments_service import get_billing_plans, validate_coupon


router = APIRouter(prefix="/read", tags=["read"])

@router.get("/all_courses")
async def get_all_coursesAPI(_: dict = Depends(validate_user)):
    """Get courses available to user based on their user type"""
    try:
        print("Fetching all courses")
        courses = await get_all_courses()
        return courses
    except Exception as e:
        error(500, f"Failed to retrieve courses: {str(e)}")

@router.get("/all_stages")
async def get_all_stagesAPI(_: dict = Depends(validate_user)):
    """Get all stages available in the system"""
    try:
        print("Fetching all stages")
        stages = await get_all_stages()  # Assuming get_all_courses returns stage data
        return stages
    except Exception as e:
        error(500, f"Failed to retrieve stages: {str(e)}")

@router.get("/courses")
async def get_courses(user_id: UUID = Query(..., description="User ID to get courses for"), _: dict = Depends(validate_user)):
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

@router.get("/companyKPIdashboard")
async def get_company_kpi_stats(company_id: str = Query(..., description="Company ID to get the list of user scores for")):
    """Get Company KPIs stats for dashboard"""
    try:
        company_kpis = await get_company_dashboard_stats(company_id)
        return company_kpis
    except Exception as e:
        error(500, f"Failed to retrieve: {str(e)}")

@router.get("/userJourney")
async def get_journay_by_user(user_id: UUID = Query(..., description="User ID to get Jouney for")):
    """Get User Journey"""
    try:
        get_user_jouney = await get_user_journey(user_id)
        return get_user_jouney
    except Exception as e:
        error(500, f"Failed to retrieve: {str(e)}")


@router.get("/plans")
async def get_billing_plansAPI():
    """Return the billing plans for the selectors in the front"""
    try:
        billing_plans = await get_billing_plans()
        return billing_plans
    except Exception as e:
        error(500, f"Failed to retrieve: {str(e)}")

@router.get("/check-coupon")
async def validate_couponAPI(coupon_code: str):
    """Endpoint to validate the coupon visually in the front"""
    try:
        coupon_details = await validate_coupon(coupon_code)
        return coupon_details
    except Exception as e:
        error(500, f"Failed to retrieve: {str(e)}")

# Asumiendo que has importado la función anterior como `get_dashboard_stats`

@router.get("/myAnalytics")
async def get_my_analytics(user_id: str):
    """Get my analytics"""
    try:
        result = await get_dashboard_stats(user_id)
        return {
            "status": "stats retrieved success",
            "result": result
        }
    
    except Exception as e:
        error(500, f"Failed to retrieve stats: {str(e)}")


@router.get("/companies_news")
async def get_company_news_route(company_id: str):
    """
    Get the latest active announcements (news) for a specific company
    """
    try:
        result = await get_company_announcements(company_id)
        
        if result is None:
            error(500, "Failed to fetch company news")
            
        return {
            "status": "news retrieved success",
            "result": result
        }
    
    except Exception as e:
        error(500, f"Failed to retrieve company news: {str(e)}")