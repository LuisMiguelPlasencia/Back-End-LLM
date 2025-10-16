# Response helpers for consistent JSON formatting
# Provides standardized success and error response functions

from fastapi import HTTPException
from fastapi.responses import JSONResponse

def ok(data=None, status_code: int = 200):
    """Return successful response with optional data"""
    if data is None:
        return JSONResponse(content={"status": "success"}, status_code=status_code)
    return JSONResponse(content=data, status_code=status_code)

def error(status_code: int, message: str):
    """Return error response with status code and message"""
    raise HTTPException(status_code=status_code, detail={"error": message})
