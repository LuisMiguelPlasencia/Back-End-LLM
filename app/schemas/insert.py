# Pydantic models for insert endpoints (POST requests)
# Handles payload validation for data creation operations

from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class StartConversationRequest(BaseModel):
    """Start conversation request payload"""
    user_id: UUID
    course_id: UUID  # Accepted for compatibility but not stored in DB
    stage_id: UUID

class CloseConversationRequest(BaseModel):
    """Close conversation request payload"""
    conversation_id: UUID
    user_id: UUID
    course_id: UUID
    

class SendMessageRequest(BaseModel):
    """Send message request payload"""
    user_id: UUID
    conversation_id: UUID
    message: str
    role: str

class ConversationCreatedResponse(BaseModel):
    """Response for created conversation"""
    status: str
    conversation: dict

class MessageSentResponse(BaseModel):
    """Response for sent message"""
    status: str
    message: dict
    assistant_response: dict

class UpdateProgressRequest(BaseModel):
    user_id: str
    journey_id: str
    course_id: str

class UpdateUserCourseProgressRequest(BaseModel):
    user_id: str
    course_id: str

class NewCourseRequest(BaseModel):
    """Send message request payload"""
    name: str
    description: str
    image_src: str
    is_active: bool
    is_mandatory: bool
    completion_time_minutes: int
    course_steps: int

class UpdateCourseRequest(BaseModel):
    """Send message request payload"""
    course_id: UUID
    name: str
    description: str
    image_src: str
    is_active: bool
    is_mandatory: bool
    completion_time_minutes: int
    course_steps: int

class NewStageRequest(BaseModel):
    """Send message request payload"""
    course_id: UUID
    stage_order: int
    stage_name: str
    stage_description: str
    key_themes: str
    position: int
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

class UpdateStageRequest(BaseModel):
    """Send message request payload"""
    stage_id: UUID
    course_id: UUID
    stage_order: int
    stage_name: str
    stage_description: str
    key_themes: str
    position: int
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



class CreateUserAssignmentRequest(BaseModel):
    """Create user assignment request payload for N users and M courses"""
    user_ids: List[UUID]
    course_ids: List[UUID]


class CreateJourneyAssignmentRequest(BaseModel):
    """Payload para asignar múltiples usuarios a múltiples journeys"""
    user_ids: List[UUID]
    journey_ids: List[UUID]

class DeleteJourneyAssignmentRequest(BaseModel):
    """Payload para eliminar múltiples asignaciones de journeys"""
    user_ids: List[UUID]
    journey_ids: List[UUID]


class CreateJourneyCourseRequest(BaseModel):
    """Payload para asignar cursos a journeys"""
    journey_ids: List[UUID]
    course_ids: List[UUID]
    is_mandatory: Optional[bool] = True
    milestone_id: Optional[UUID] = None

class DeleteJourneyCourseRequest(BaseModel):
    """Payload para eliminar cursos de journeys"""
    journey_ids: List[UUID]
    course_ids: List[UUID]