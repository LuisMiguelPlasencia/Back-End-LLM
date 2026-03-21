# ---------------------------------------------------------------------------
# Authentication router
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging
from datetime import timedelta

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    is_token_valid,
    update_user_token_in_db,
    user_exists,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return a JWT.

    Flow:
      1. Verify the email exists and account is active.
      2. Validate credentials.
      3. Reuse an existing valid token or mint a new one.
    """
    # 1. Existence check
    if not await user_exists(request.email):
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Credential validation
    user_data = await authenticate_user(request.email, request.password)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user_data.get("is_active", False):
        raise HTTPException(status_code=403, detail="Account is inactive")

    # 3. Token lifecycle
    user_id = str(user_data["user_id"])
    current_token = user_data.get("api_key")
    final_token: str

    if current_token and is_token_valid(current_token):
        logger.info("Reusing valid token for user %s", user_id)
        final_token = current_token
    else:
        logger.info("Generating new token for user %s", user_id)
        payload = {
            "sub": user_id,
            "email": user_data.get("email"),
            "role": user_data.get("user_type", "user"),
        }
        final_token = create_access_token(
            data=payload,
            expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
        )
        await update_user_token_in_db(user_id, final_token)
        user_data["api_key"] = final_token

    # 4. Response
    user_response = UserResponse(**user_data)
    return LoginResponse(token=final_token, user=user_response)
