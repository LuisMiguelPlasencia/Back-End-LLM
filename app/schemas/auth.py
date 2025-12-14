# Pydantic models for authentication endpoints
# Handles login request validation and user response formatting

from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional

class LoginRequest(BaseModel):
    """Login request payload"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """User information response"""
    user_id: UUID
    email: str
    name: str
    user_type: str
    is_active: bool
    avatar: str | None
    company_id: str | None

class LoginResponse(BaseModel):
    """Login success response"""
    status: str
    user: UserResponse
