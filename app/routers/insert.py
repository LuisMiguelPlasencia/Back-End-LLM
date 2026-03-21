# ---------------------------------------------------------------------------
# Insert router — mutation endpoints
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.schemas.insert import (
    CloseConversationRequest,
    NewCourseRequest,
    NewStageRequest,
    SendMessageRequest,
    StartConversationRequest,
    UpdateCourseRequest,
    UpdateProgressRequest,
    UpdateStageRequest,
    UpdateUserCourseProgressRequest,
)
from app.services.auth_service import validate_user
from app.services.conversations_service import create_conversation, close_conversation
from app.services.courses_service import create_new_course, create_new_stage, update_course, update_stage
from app.services.messages_service import send_message, update_module_progress, update_user_course_progress
from app.services.payments_service import simulate_investment, InvestmentSimulation
from app.utils.responses import error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insert", tags=["Insert"])


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------

@router.post("/conversation")
async def start_conversation(request: StartConversationRequest):
    """Create a new conversation for a user."""
    try:
        conversation = await create_conversation(request.user_id, request.course_id, request.stage_id)
        if not conversation:
            error(500, "Failed to create conversation")
        return {"status": "conversation created success", "conversation": conversation}
    except Exception as e:
        error(500, f"Failed to create conversation: {e}")


@router.post("/close_conversation")
async def close_conversation_route(request: CloseConversationRequest):
    """Mark a conversation as finished."""
    try:
        result = await close_conversation(
            request.conversation_id, request.user_id, request.course_id
        )
        if not result:
            error(500, "Failed to close conversation")
        return {"status": "conversation closed success", "result": result}
    except Exception as e:
        error(500, f"Failed to close conversation: {e}")


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

@router.post("/message")
async def send_user_message(request: SendMessageRequest):
    """Persist a user or assistant message."""
    try:
        user_message = await send_message(
            request.user_id,
            request.conversation_id,
            request.message.strip(),
            request.role,
            request.duration,
        )
        if not user_message:
            error(500, "Failed to send message")
        return {"status": "message sent", "message": user_message}
    except Exception as e:
        error(500, f"Failed to send message: {e}")


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

@router.post("/update_progress")
async def update_progress_route(request: UpdateProgressRequest):
    """Increment module progress for a user in a journey/course."""
    try:
        result = await update_module_progress(
            user_id=request.user_id,
            journey_id=request.journey_id,
            course_id=request.course_id,
        )
        if not result or not result.get("success"):
            msg = (result or {}).get("error", "Unknown database error")
            error(500, f"Failed to update progress: {msg}")
        return {
            "status": "progress updated success",
            "result": {
                "course_status": result.get("course_status"),
                "journey_status": result.get("journey_status"),
                "completed_modules": result.get("completed_modules"),
            },
        }
    except Exception as e:
        error(500, f"Failed to update progress: {e}")


@router.post("/update_user_course_progress")
async def update_user_course_progress_api(request: UpdateUserCourseProgressRequest):
    """Increment completed_modules by 1 for a course."""
    try:
        await update_user_course_progress(
            user_id=request.user_id,
            course_id=request.course_id,
        )
        return {"status": "progress updated success"}
    except Exception as e:
        error(500, f"Failed to update progress: {e}")


# ---------------------------------------------------------------------------
# Billing simulation
# ---------------------------------------------------------------------------

@router.post("/simulate-investment")
async def simulate_investment_checkout(data: InvestmentSimulation):
    """Simulate pricing for the checkout preview."""
    try:
        return await simulate_investment(data)
    except Exception as e:
        error(500, f"Failed to simulate: {e}")


# ---------------------------------------------------------------------------
# Admin — Course CRUD
# ---------------------------------------------------------------------------

@router.post("/course")
async def create_new_course_api(request: NewCourseRequest, _: dict = Depends(validate_user)):
    """Create a new course (admin)."""
    try:
        course_id = await create_new_course(
            name=request.name,
            description=request.description,
            image_src=request.image_src,
            is_active=request.is_active,
            is_mandatory=request.is_mandatory,
            completion_time_minutes=request.completion_time_minutes,
            course_steps=request.course_steps,
        )
        if not course_id:
            error(500, "Failed to create course")
        return {"status": "course created", "course_id": course_id}
    except Exception as e:
        error(500, f"Failed to create course: {e}")


@router.post("/update_course")
async def update_course_api(request: UpdateCourseRequest, _: dict = Depends(validate_user)):
    """Update an existing course (admin)."""
    try:
        course_id = await update_course(
            course_id=request.course_id,
            name=request.name,
            description=request.description,
            image_src=request.image_src,
            is_active=request.is_active,
            is_mandatory=request.is_mandatory,
            completion_time_minutes=request.completion_time_minutes,
            course_steps=request.course_steps,
        )
        if not course_id:
            error(500, "Failed to update course")
        return {"status": "course updated", "course_id": course_id}
    except Exception as e:
        error(500, f"Failed to update course: {e}")


# ---------------------------------------------------------------------------
# Admin — Stage CRUD
# ---------------------------------------------------------------------------

@router.post("/stage")
async def create_new_stage_api(request: NewStageRequest, _: dict = Depends(validate_user)):
    """Create a new stage within a course (admin)."""
    try:
        stage_id = await create_new_stage(
            course_id=request.course_id, stage_order=request.stage_order,
            stage_name=request.stage_name, stage_description=request.stage_description,
            key_themes=request.key_themes, position=request.position,
            level=request.level, body=request.body, bot_prompt=request.bot_prompt,
            user_role=request.user_role, bot_role=request.bot_role,
            context_info=request.context_info, stage_objectives=request.stage_objectives,
            voice_id=request.voice_id, agent_id=request.agent_id,
            chatbot_image_src=request.chatbot_image_src,
        )
        if not stage_id:
            error(500, "Failed to create stage")
        return {"status": "stage created", "stage_id": stage_id}
    except Exception as e:
        error(500, f"Failed to create stage: {e}")


@router.post("/update_stage")
async def update_stage_api(request: UpdateStageRequest, _: dict = Depends(validate_user)):
    """Update an existing stage (admin)."""
    try:
        stage_id = await update_stage(
            stage_id=request.stage_id, course_id=request.course_id,
            stage_order=request.stage_order, stage_name=request.stage_name,
            stage_description=request.stage_description, key_themes=request.key_themes,
            position=request.position, level=request.level, body=request.body,
            bot_prompt=request.bot_prompt, user_role=request.user_role,
            bot_role=request.bot_role, context_info=request.context_info,
            stage_objectives=request.stage_objectives, voice_id=request.voice_id,
            agent_id=request.agent_id, chatbot_image_src=request.chatbot_image_src,
        )
        if not stage_id:
            error(500, "Failed to update stage")
        return {"status": "stage updated", "stage_id": stage_id}
    except Exception as e:
        error(500, f"Failed to update stage: {e}")
