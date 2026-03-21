# ---------------------------------------------------------------------------
# Read / query response schemas
# ---------------------------------------------------------------------------

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class CourseResponse(BaseModel):
    """Single course item."""
    course_id: UUID
    name: str
    description: Optional[str] = None
    image_src: Optional[str] = None
    created_on: datetime
    is_active: bool
    event_time: Optional[datetime] = None
    metrics: Optional[str] = None


class ConversationResponse(BaseModel):
    """Single conversation item."""
    conversation_id: UUID
    user_id: UUID
    start_timestamp: datetime
    end_timestamp: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Single message item."""
    id: UUID
    user_id: Optional[UUID] = None
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime


class HealthResponse(BaseModel):
    """Liveness / readiness response."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Generic error envelope."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
