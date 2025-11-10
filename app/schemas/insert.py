# Pydantic models for insert endpoints (POST requests)
# Handles payload validation for data creation operations

from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class StartConversationRequest(BaseModel):
    """Start conversation request payload"""
    user_id: UUID
    course_id: UUID  # Accepted for compatibility but not stored in DB

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
