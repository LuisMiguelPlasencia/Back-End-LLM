# ---------------------------------------------------------------------------
# Authentication schemas
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# -- Requests ---------------------------------------------------------------

class LoginRequest(BaseModel):
    """POST /auth/login payload."""
    email: EmailStr
    password: str = Field(..., min_length=1)


# -- Responses --------------------------------------------------------------

class UserResponse(BaseModel):
    """Public-facing user profile returned after login."""
    user_id: UUID
    email: str
    name: str
    user_type: str
    is_active: bool
    avatar: Optional[str] = None
    company_id: Optional[str] = None


class LoginResponse(BaseModel):
    """Envelope for a successful login."""
    status: str = "success"
    message: str = "Login successful"
    token: str
    user: UserResponse
