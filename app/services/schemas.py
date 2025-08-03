from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


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