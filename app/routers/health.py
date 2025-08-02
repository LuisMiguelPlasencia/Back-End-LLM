from datetime import datetime
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database import get_session, engine
from app.schemas import HealthResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

'''

@router.get("/readiness", response_model=HealthResponse)
async def readiness_check(session: Session = Depends(get_session)):
    """Readiness check - verifies database connectivity"""
    try:
        # Test database connection
        session.exec("SELECT 1").first()
        
        return HealthResponse(
            status="ready",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return HealthResponse(
            status="not_ready",
            timestamp=datetime.utcnow()
        )
'''

@router.get("/liveness", response_model=HealthResponse)
async def liveness_check():
    """Liveness check - verifies application is running"""
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow()
    ) 