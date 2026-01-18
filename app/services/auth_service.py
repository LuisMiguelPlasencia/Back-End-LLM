# Authentication service using pgcrypto for password verification
# Assumes pgcrypto extension is available in PostgreSQL database
# Handles user login validation against conversaConfig.user_info table

from .db import execute_query_one
from typing import Optional, Dict
import bcrypt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from dotenv import load_dotenv
from app.services.db import execute_query
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

load_dotenv()
SECRET_KEY_JWT = os.getenv("SECRET_KEY_JWT")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60

async def authenticate_user(email: str, password_input: str) -> Optional[Dict]:
    """
    Authenticate user with email and password using pgcrypto crypt()
    Returns user data if authentication successful, None otherwise
    """
    query = """
    SELECT user_id, email, password, name, user_type, is_active, avatar, company_id
    FROM conversaConfig.user_info
    WHERE email = $1
    """
    
    results = await execute_query_one(query, email)
    print(results)
    if isinstance(results, list):
        raw_row = results[0]
    else:
        raw_row = results
    user_row = dict(raw_row)
    stored_hash = user_row.get("password")

    if verify_password(password_input, stored_hash):
        user_row.pop("password", None) 
        
        return user_row  
    else:
        return None  
    

async def user_exists(email: str) -> bool:
    """Check if user exists by email"""
    query = "SELECT 1 FROM conversaConfig.user_info WHERE email = $1 AND is_active = TRUE"
    result = await execute_query_one(query, email)
    return result is not None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara clave plana vs hash de la BD"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a standardized JWT token with an expiration time.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Fallback default expiration
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_JWT, algorithm=ALGORITHM)
    return encoded_jwt

def is_token_valid(token: str) -> bool:
    """
    Checks if the provided token is structurally valid and has not expired.
    Returns True if reusable, False if a new one is needed.
    """
    if not token:
        return False
    try:
        # Attempt to decode. The library automatically checks signature and 'exp' claim.
        jwt.decode(token, SECRET_KEY_JWT, algorithms=[ALGORITHM])
        return True
    except JWTError:
        # Token is expired, tampered with, or invalid
        return False

# --- HELPER 3: Database Persistence ---
async def update_user_token_in_db(user_id: str, new_token: str):
    """
    Updates the api_key field in the user_info table.
    """
    query = """
        UPDATE conversaconfig.user_info 
        SET api_key = $1 
        WHERE user_id = $2
    """
    try:
        await execute_query(query, new_token, user_id)
    except Exception as e:
        print(f"Error updating token for user {user_id}: {e}")


header_scheme = APIKeyHeader(name="x-api-key", auto_error=True)

async def validate_user(token: str = Depends(header_scheme)):
    """
    Valida el token recibido en el header 'x-api-key'.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key or Session expired",
    )

    # 1. Decodificar JWT
    try:
        payload = jwt.decode(token, SECRET_KEY_JWT, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 2. Consultar BD
    query = """
        SELECT user_id, api_key, is_active, user_type 
        FROM conversaconfig.user_info 
        WHERE user_id = $1
    """
    results = await execute_query(query, user_id)

    if not results:
        raise credentials_exception

    # Manejo robusto (Lista vs Fila)
    user_row = dict(results[0]) if isinstance(results, list) else dict(results)

    # 3. Validar coincidencia (Single Session)
    db_token = user_row.get("api_key")
    if db_token != token:
        raise credentials_exception

    if not user_row.get("is_active"):
        raise HTTPException(status_code=403, detail="Inactive user")

    return user_row