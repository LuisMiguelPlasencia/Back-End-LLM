# ---------------------------------------------------------------------------
# Authentication service
# ---------------------------------------------------------------------------
# Handles credential verification, JWT lifecycle, and request-level auth.
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt

from app.config import settings
from app.services.db import execute_query, execute_query_one

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants (pulled from centralised settings)
# ---------------------------------------------------------------------------
_SECRET = settings.secret_key_jwt
_ALGORITHM = settings.jwt_algorithm
_EXPIRE_MINUTES = settings.jwt_expire_minutes

# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def _verify_password(plain: str, hashed: str) -> bool:
    """Compare a plain-text password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT utilities
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT with an expiration claim."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, _SECRET, algorithm=_ALGORITHM)


def is_token_valid(token: str) -> bool:
    """Return ``True`` if *token* is structurally valid and not expired."""
    if not token:
        return False
    try:
        jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        return True
    except JWTError:
        return False


# ---------------------------------------------------------------------------
# Core authentication
# ---------------------------------------------------------------------------

async def user_exists(email: str) -> bool:
    """Check whether an active user with *email* exists."""
    row = await execute_query_one(
        "SELECT 1 FROM conversaConfig.user_info WHERE email = $1 AND is_active = TRUE",
        email,
    )
    return row is not None


async def authenticate_user(email: str, password_input: str) -> Optional[Dict]:
    """Validate credentials and return user data (without the password hash).

    Returns ``None`` when credentials are invalid.
    """
    query = """
        SELECT user_id, email, password, name, user_type, is_active, avatar, company_id, api_key
        FROM conversaConfig.user_info
        WHERE email = $1
    """
    row = await execute_query_one(query, email)
    if row is None:
        return None

    user = dict(row)
    stored_hash = user.pop("password", None)

    if not _verify_password(password_input, stored_hash or ""):
        return None

    return user


# ---------------------------------------------------------------------------
# Token persistence
# ---------------------------------------------------------------------------

async def update_user_token_in_db(user_id: str, new_token: str) -> None:
    """Persist the latest JWT in the user row for single-session enforcement."""
    try:
        await execute_query(
            "UPDATE conversaconfig.user_info SET api_key = $1 WHERE user_id = $2",
            new_token,
            user_id,
        )
    except Exception:
        logger.exception("Failed to persist token for user %s", user_id)


# ---------------------------------------------------------------------------
# Request-level dependency
# ---------------------------------------------------------------------------

_header_scheme = APIKeyHeader(name="x-api-key", auto_error=True)


async def validate_user(token: str = Depends(_header_scheme)) -> Dict:
    """FastAPI dependency: decode the JWT, verify it against the DB, and return user data."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key or session expired",
    )

    # 1. Decode JWT
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    # 2. Look up user in DB
    rows = await execute_query(
        "SELECT user_id, api_key, is_active, user_type FROM conversaconfig.user_info WHERE user_id = $1",
        user_id,
    )
    if not rows:
        raise credentials_exc

    user_row = dict(rows[0])

    # 3. Single-session check
    if user_row.get("api_key") != token:
        raise credentials_exc

    if not user_row.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user_row
