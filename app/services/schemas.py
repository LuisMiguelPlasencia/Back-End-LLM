# ---------------------------------------------------------------------------
# Shared service-layer schemas (used by health/db_operations routers)
# ---------------------------------------------------------------------------
# NOTE: Prefer placing schemas in app/schemas/ for new endpoints.
# This file exists for backward-compatibility with legacy routers.
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
