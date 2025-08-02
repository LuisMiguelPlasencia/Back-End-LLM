from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Text schemas
class TextUpload(BaseModel):
    title: str
    content: str
    language: Optional[str] = None
    source: Optional[str] = None


class TextResponse(BaseModel):
    id: int
    title: str
    content: str
    language: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime


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