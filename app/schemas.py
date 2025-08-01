from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models import TranscriptionStatus, AudioStatus


# User schemas
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    supabase_id: str


class UserResponse(UserBase):
    id: int
    supabase_id: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime


# Audio schemas
class AudioUpload(BaseModel):
    user_id: int
    language: Optional[str] = None


class AudioResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    storage_path: str
    status: AudioStatus
    language: Optional[str] = None
    duration: Optional[float] = None
    created_at: datetime
    updated_at: datetime


# Transcription schemas
class TranscriptionResponse(BaseModel):
    id: int
    audio_id: int
    status: TranscriptionStatus
    text: Optional[str] = None
    confidence: Optional[float] = None
    language: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TranscriptionCreate(BaseModel):
    audio_id: int


# Chat schemas
class ChatSessionCreate(BaseModel):
    user_id: int
    title: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    chat_session_id: int
    content: str
    role: str = Field(default="user")


class MessageResponse(BaseModel):
    id: int
    chat_session_id: int
    role: str
    content: str
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime


class ChatCompletionRequest(BaseModel):
    transcription_id: int
    message: str = Field(..., min_length=1, max_length=1000)


class ChatCompletionResponse(BaseModel):
    message: str
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None


# Health check
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"


# Error responses
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 