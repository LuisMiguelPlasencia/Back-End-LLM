# Authentication routes
# Handles user login with email/password validation
# Example: curl -X POST "http://localhost:8000/auth/login" -H "Content-Type: application/json" -d '{"email":"user@example.com","password":"password123"}'

from fastapi import APIRouter
from ..schemas.auth import LoginRequest, UserResponse
from ..services.auth_service import authenticate_user, user_exists
from ..utils.responses import error

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login")
async def login(request: LoginRequest):
    """
    Authenticate user with email and password
    Returns user info if successful, error if invalid credentials or user not found
    """
    # Check if user exists first
    if not await user_exists(request.email):
        error(404, "user not found")
    
    # Authenticate user
    user_data = await authenticate_user(request.email, request.password)
    
    if not user_data:
        error(401, "invalid credentials")
    
    # Check if user is active
    if not user_data.get("is_active", False):
        error(401, "account is inactive")
    
    # Return successful login response
    user_response = UserResponse(**user_data)
    return {
        "status": "login success",
        "user": user_response.dict()
    }
