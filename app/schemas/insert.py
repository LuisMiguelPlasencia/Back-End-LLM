# ---------------------------------------------------------------------------
# Insert / mutation request schemas
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# -- Conversations ----------------------------------------------------------

class StartConversationRequest(BaseModel):
    """POST /insert/conversation"""
    user_id: UUID
    course_id: UUID
    stage_id: UUID


class CloseConversationRequest(BaseModel):
    """POST /insert/close_conversation"""
    conversation_id: UUID
    user_id: UUID
    course_id: UUID


# -- Messages ---------------------------------------------------------------

class SendMessageRequest(BaseModel):
    """POST /insert/message"""
    user_id: UUID
    conversation_id: UUID
    message: str = Field(..., min_length=1)
    role: str = Field(..., pattern="^(user|assistant)$")
    duration: Optional[float] = None


# -- Progress ---------------------------------------------------------------

class UpdateProgressRequest(BaseModel):
    """POST /insert/update_progress"""
    user_id: str
    journey_id: str
    course_id: str


class UpdateUserCourseProgressRequest(BaseModel):
    """POST /insert/update_user_course_progress"""
    user_id: str
    course_id: str


# -- Courses ----------------------------------------------------------------

class NewCourseRequest(BaseModel):
    """POST /insert/course"""
    name: str = Field(..., min_length=1)
    description: str
    image_src: str
    is_active: bool = True
    is_mandatory: bool = False
    completion_time_minutes: int = Field(..., ge=0)
    course_steps: int = Field(..., ge=0)


class UpdateCourseRequest(BaseModel):
    """POST /insert/update_course"""
    course_id: UUID
    name: str = Field(..., min_length=1)
    description: str
    image_src: str
    is_active: bool = True
    is_mandatory: bool = False
    completion_time_minutes: int = Field(..., ge=0)
    course_steps: int = Field(..., ge=0)


# -- Stages -----------------------------------------------------------------

class _StageFields(BaseModel):
    """Shared fields for stage create / update."""
    course_id: UUID
    stage_order: int = Field(..., ge=0)
    stage_name: str = Field(..., min_length=1)
    stage_description: str
    key_themes: str
    position: int = Field(..., ge=0)
    level: str
    body: str
    bot_prompt: str
    user_role: str
    bot_role: str
    context_info: str
    stage_objectives: str
    voice_id: str
    agent_id: str
    chatbot_image_src: str


class NewStageRequest(_StageFields):
    """POST /insert/stage"""
    pass


class UpdateStageRequest(_StageFields):
    """POST /insert/update_stage"""
    stage_id: UUID


# -- Responses (generic envelopes) -----------------------------------------

class ConversationCreatedResponse(BaseModel):
    status: str = "conversation created success"
    conversation: dict


class MessageSentResponse(BaseModel):
    status: str = "message sent"
    message: dict
    assistant_response: dict
