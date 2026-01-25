# Authentication routes
# Handles user login with email/password validation
# Example: curl -X POST "http://localhost:8000/auth/login" -H "Content-Type: application/json" -d '{"email":"user@example.com","password":"password123"}'

from fastapi import APIRouter
from ..schemas.auth import LoginRequest, UserResponse
from ..services.auth_service import authenticate_user, user_exists, is_token_valid, create_access_token, update_user_token_in_db
import os
from datetime import  timedelta
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv(override=True)
SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 Hours

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login")
async def login(request: LoginRequest):
    """
    Authenticate user, manage JWT lifecycle (Reuse vs Renew), and return user profile.
    
    Flow:
    1. Validate credentials.
    2. Check if user is active.
    3. Check if existing DB token is still valid.
    4. Reuse existing token OR generate and save a new one.
    """
    # 1. Check if user exists
    # Note: ensure user_exists returns a boolean
    if not await user_exists(request.email):
        # Using 401 for generic error to prevent user enumeration attacks is safer, 
        # but 404 is acceptable for internal tools.
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. Authenticate user
    # Returns Dict with user data or None
    user_data = await authenticate_user(request.email, request.password)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 3. Check activity status
    if not user_data.get("is_active", False):
        raise HTTPException(status_code=403, detail="Account is inactive")

    # --- JWT LOGIC ---
    
    user_id = str(user_data["user_id"])
    current_stored_token = user_data.get("api_key")
    final_token = None

    # A. Check for reusable valid token
    if current_stored_token and is_token_valid(current_stored_token):
        print(f"🔄 Valid token found for user {user_id}. Reusing.")
        final_token = current_stored_token
    
    # B. Generate new token if missing or expired
    else:
        print(f"🆕 Generating new token for user {user_id}...")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token_payload = {
            "sub": user_id, 
            "email": user_data.get("email"),
            "role": user_data.get("user_type", "user")
        }
        
        final_token = create_access_token(
            data=token_payload, 
            expires_delta=access_token_expires
        )
        
        # Async update to database
        await update_user_token_in_db(user_id, final_token)
        
        # Update local dict to ensure consistency in response
        user_data["api_key"] = final_token


    # Prepare Response
    # Assuming UserResponse matches your Pydantic schema
    user_response = UserResponse(**user_data)
    
    return {
        "status": "success",
        "message": "Login successful",
        "token": final_token,
        "user": user_response.dict()
    }