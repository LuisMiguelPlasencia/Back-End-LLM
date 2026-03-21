# ---------------------------------------------------------------------------
# Read router — data retrieval endpoints
# ---------------------------------------------------------------------------

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.auth_service import validate_user
from app.services.courses_service import (
    get_all_courses,
    get_all_stages,
    get_company_courses,
    get_courses_details,
    get_user_courses,
    get_user_courses_stages,
    user_course_progress,
)
from app.services.conversations_service import (
    get_conversation_details,
    get_user_conversations,
)
from app.services.messages_service import (
    get_all_user_conversation_average_scoring_by_stage_company,
    get_all_user_conversation_scoring_by_company,
    get_all_user_conversation_scoring_by_stage_company,
    get_all_user_profiling_by_company,
    get_all_user_scoring_by_company,
    get_company_announcements,
    get_company_dashboard_stats,
    get_conversation_messages,
    get_dashboard_stats,
    get_user_avg_filler_words,
    get_user_avg_participation,
    get_user_avg_rhythm,
    get_user_avg_technical_level,
    get_user_cumulative_average_score,
    get_user_journey,
    get_user_persona_profile,
    get_user_profiling,
)
from app.services.profiling_service import general_profiling
from app.services.payments_service import get_billing_plans, validate_coupon
from app.utils.responses import error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/read", tags=["Read"])


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------

@router.get("/all_courses")
async def get_all_courses_api(_: dict = Depends(validate_user)):
    """List every course in the system."""
    try:
        return await get_all_courses()
    except Exception as e:
        error(500, f"Failed to retrieve courses: {e}")


@router.get("/all_stages")
async def get_all_stages_api(_: dict = Depends(validate_user)):
    """List all stages with their content."""
    try:
        return await get_all_stages()
    except Exception as e:
        error(500, f"Failed to retrieve stages: {e}")


@router.get("/courses")
async def get_courses(
    user_id: UUID = Query(..., description="User ID"),
    _: dict = Depends(validate_user),
):
    """Courses assigned to a specific user."""
    try:
        return await get_user_courses(user_id)
    except Exception as e:
        error(500, f"Failed to retrieve courses: {e}")


@router.get("/courses_stages")
async def get_courses_stages(
    course_id: UUID = Query(..., description="Course ID"),
):
    """Stages within a given course."""
    try:
        return await get_user_courses_stages(course_id)
    except Exception as e:
        error(500, f"Failed to retrieve stages: {e}")


@router.get("/courses_details")
async def get_user_courses_details(
    course_id: UUID = Query(..., description="Course ID"),
    stage_id: UUID = Query(..., description="Stage ID"),
):
    """Full details for a course + stage combination."""
    try:
        return await get_courses_details(course_id, stage_id)
    except Exception as e:
        error(500, f"Failed to retrieve details: {e}")


@router.get("/company_courses")
async def get_company_courses_api(company_id: str):
    """Courses belonging to a company."""
    try:
        result = await get_company_courses(company_id)
        if result is None:
            error(404, "Company course not found")
        return result
    except Exception as e:
        error(500, f"Failed to retrieve: {e}")


# ---------------------------------------------------------------------------
# Conversations & Messages
# ---------------------------------------------------------------------------

@router.get("/conversation")
async def get_conversation(
    conversation_id: UUID = Query(..., description="Conversation ID"),
):
    """Details (incl. scoring) for a single conversation."""
    try:
        return await get_conversation_details(conversation_id)
    except Exception as e:
        error(500, f"Failed to retrieve conversation: {e}")


@router.get("/conversations")
async def get_conversations(
    user_id: UUID = Query(..., description="User ID"),
):
    """Most recent conversations for a user."""
    try:
        return await get_user_conversations(user_id)
    except Exception as e:
        error(500, f"Failed to retrieve conversations: {e}")


@router.get("/messages")
async def get_messages(
    conversation_id: UUID = Query(..., description="Conversation ID"),
    _: dict = Depends(validate_user),
):
    """All messages within a conversation."""
    try:
        return await get_conversation_messages(conversation_id)
    except Exception as e:
        error(500, f"Failed to retrieve messages: {e}")


# ---------------------------------------------------------------------------
# Profiling
# ---------------------------------------------------------------------------

@router.get("/userProfiling")
async def get_user_profiling_api(
    user_id: UUID = Query(..., description="User ID"),
):
    """User profiling scores and feedback."""
    try:
        profiling = await get_user_profiling(str(user_id))
        if isinstance(profiling, list):
            profiling = {}

        keys = [
            "name", "user_id", "general_score", "profile_type",
            "empathy_scoring", "negotiation_scoring", "prospection_scoring",
            "resilience_scoring", "technical_domain_scoring",
            "empathy_feedback", "negotiation_feedback", "prospection_feedback",
            "resilience_feedback", "technical_domain_feedback", "avatar",
        ]
        result = {k: profiling.get(k) for k in keys}
        result.setdefault("user_id", user_id)
        return result
    except Exception as e:
        logger.exception("Error in userProfiling endpoint")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve profiling: {e}")


@router.get("/userProfilingGeneralFeedback")
async def get_user_profiling_general_feedback(
    user_id: UUID = Query(..., description="User ID"),
):
    """Trigger and return the general profiling feedback for a user."""
    try:
        gf = await general_profiling(user_id)
        return {
            "empathy_feedback": (gf or {}).get("general_feedback_empathy"),
            "negotiation_feedback": (gf or {}).get("general_feedback_negotiation"),
            "prospection_feedback": (gf or {}).get("general_feedback_prospection"),
            "resilience_feedback": (gf or {}).get("general_feedback_resilience"),
            "technical_domain_feedback": (gf or {}).get("general_feedback_technical_domain"),
        }
    except Exception as e:
        logger.exception("Error in userProfilingGeneralFeedback endpoint")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve profiling feedback: {e}")


# ---------------------------------------------------------------------------
# Company-level analytics
# ---------------------------------------------------------------------------

@router.get("/allUserScoreByCompany")
async def get_all_user_score_by_company(
    company_id: str = Query(..., description="Company ID"),
):
    """Top-5 leaderboard for a company."""
    try:
        return await get_all_user_scoring_by_company(company_id)
    except Exception as e:
        error(500, f"Failed to retrieve scores: {e}")


@router.get("/allUserConversationScoresByCompany")
async def get_all_user_conversation_scores_by_company(
    company_id: str = Query(..., description="Company ID"),
):
    """Aggregated per-user scoring for a company."""
    try:
        return await get_all_user_conversation_scoring_by_company(company_id)
    except Exception as e:
        error(500, f"Failed to retrieve scores: {e}")


@router.get("/allUserConversationScoresByStageCompany")
async def get_all_user_conversation_scores_by_stage_company(
    stage_id: str = Query(..., description="Stage ID"),
    company_id: str = Query(..., description="Company ID"),
):
    """Per-user scoring for a specific stage in a company."""
    try:
        return await get_all_user_conversation_scoring_by_stage_company(stage_id, company_id)
    except Exception as e:
        error(500, f"Failed to retrieve scores: {e}")


@router.get("/allUserConversationAverageScoresByStageCompany")
async def get_all_user_conversation_avg_scores_by_stage_company(
    stage_id: str = Query(..., description="Stage ID"),
    company_id: str = Query(..., description="Company ID"),
):
    """Average per-user scoring for a stage in a company."""
    try:
        return await get_all_user_conversation_average_scoring_by_stage_company(stage_id, company_id)
    except Exception as e:
        error(500, f"Failed to retrieve scores: {e}")


@router.get("/userScoringTimeSeries")
async def get_user_scoring_time_series(
    user_id: str = Query(..., description="User ID"),
    n_days: int = Query(7, ge=1, le=365, description="Number of days"),
):
    """Cumulative average score per day."""
    try:
        return await get_user_cumulative_average_score(user_id, n_days)
    except Exception as e:
        error(500, f"Failed to retrieve time series: {e}")


@router.get("/allUserProfilingByCompany")
async def get_all_user_profiling_by_company_api(
    company_id: str = Query(..., description="Company ID"),
):
    """Profiling scores for every user in a company."""
    try:
        return await get_all_user_profiling_by_company(company_id)
    except Exception as e:
        error(500, f"Failed to retrieve profiling: {e}")


@router.get("/companyKPIdashboard")
async def get_company_kpi_stats(
    company_id: str = Query(..., description="Company ID"),
):
    """Consolidated company KPI dashboard."""
    try:
        return await get_company_dashboard_stats(company_id)
    except Exception as e:
        error(500, f"Failed to retrieve KPIs: {e}")


# ---------------------------------------------------------------------------
# User Journey & Progress
# ---------------------------------------------------------------------------

@router.get("/userJourney")
async def get_journey_by_user(
    user_id: UUID = Query(..., description="User ID"),
):
    """User's assigned journeys with course progress."""
    try:
        return await get_user_journey(str(user_id))
    except Exception as e:
        error(500, f"Failed to retrieve journey: {e}")


@router.get("/user_course_progress")
async def user_course_progress_api(user_id: str, course_id: str):
    """Current progress for a user within a course."""
    try:
        result = await user_course_progress(user_id, course_id)
        if result is None:
            error(404, "User course progress not found")
        return {"status": "success", "result": result}
    except Exception as e:
        error(500, f"Error fetching user course progress: {e}")


# ---------------------------------------------------------------------------
# My Analytics
# ---------------------------------------------------------------------------

@router.get("/myAnalytics")
async def get_my_analytics(user_id: str):
    """Individual user dashboard stats."""
    try:
        result = await get_dashboard_stats(user_id)
        return {"status": "stats retrieved success", "result": result}
    except Exception as e:
        error(500, f"Failed to retrieve stats: {e}")


@router.get("/myAnalytics-ScoringTab")
async def get_my_analytics_scoring_tab(user_id: str):
    """Aggregated scoring-tab metrics (4 queries in parallel)."""
    try:
        participation, rhythm, filler_words, technical_level = await asyncio.gather(
            get_user_avg_participation(user_id),
            get_user_avg_rhythm(user_id),
            get_user_avg_filler_words(user_id),
            get_user_avg_technical_level(user_id),
        )
        return {
            "status": "success",
            "result": {
                "participation": participation,
                "rhythm": rhythm,
                "filler_words": filler_words,
                "technical_level": technical_level,
            },
        }
    except Exception as e:
        error(500, f"Failed to retrieve analytics scoring tab: {e}")


@router.get("/myAnalytics-PersonalityTab")
async def get_my_analytics_personality_tab(user_id: str):
    """User's conversational persona card."""
    try:
        result = await get_user_persona_profile(user_id)
        if result is None:
            error(404, "User profile not found")
        return {"status": "success", "result": result}
    except Exception as e:
        error(500, f"Error fetching persona profile: {e}")


# ---------------------------------------------------------------------------
# Billing / Coupons
# ---------------------------------------------------------------------------

@router.get("/plans")
async def get_billing_plans_api():
    """Active billing plans."""
    try:
        return await get_billing_plans()
    except Exception as e:
        error(500, f"Failed to retrieve plans: {e}")


@router.get("/check-coupon")
async def validate_coupon_api(coupon_code: str):
    """Validate a coupon code for the checkout UI."""
    try:
        return await validate_coupon(coupon_code)
    except Exception as e:
        error(500, f"Failed to validate coupon: {e}")


# ---------------------------------------------------------------------------
# Company News
# ---------------------------------------------------------------------------

@router.get("/companies_news")
async def get_company_news_route(company_id: str):
    """Active announcements for a company."""
    try:
        result = await get_company_announcements(company_id)
        return {"status": "news retrieved success", "result": result}
    except Exception as e:
        error(500, f"Failed to retrieve company news: {e}")
