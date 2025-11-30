# Pydantic models for read endpoints (GET requests)
# Handles query parameters and response formatting for data retrieval

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class UserIdQuery(BaseModel):
    """Query parameter for user_id"""
    user_id: UUID

class ConversationIdQuery(BaseModel):
    """Query parameter for conversation_id"""
    conversation_id: UUID

class CourseResponse(BaseModel):
    """Course information response"""
    course_id: UUID
    name: str
    description: Optional[str]
    image_src: Optional[str]
    created_on: datetime
    is_active: bool
    event_time: Optional[datetime]
    metrics: Optional[str]

class ConversationResponse(BaseModel):
    """Conversation information response"""
    conversation_id: UUID
    user_id: UUID
    start_timestamp: datetime
    end_timestamp: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    """Message information response"""
    id: UUID
    user_id: Optional[UUID]
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
