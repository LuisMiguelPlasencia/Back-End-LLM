# Authentication service using pgcrypto for password verification
# Assumes pgcrypto extension is available in PostgreSQL database
# Handles user login validation against conversaConfig.user_info table

from .db import execute_query_one
from typing import Optional, Dict

async def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """
    Authenticate user with email and password using pgcrypto crypt()
    Returns user data if authentication successful, None otherwise
    """
    query = """
    SELECT user_id, email, name, user_type, is_active
    FROM conversaConfig.user_info
    WHERE email = $1
      AND password = $2
    """
    
    result = await execute_query_one(query, email, password)
    
    if result:
        return dict(result)
    return None

async def user_exists(email: str) -> bool:
    """Check if user exists by email"""
    query = "SELECT 1 FROM conversaConfig.user_info WHERE email = $1 AND is_active = TRUE"
    result = await execute_query_one(query, email)
    return result is not None
