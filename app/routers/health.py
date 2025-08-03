from datetime import datetime
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.services.database import get_session, engine
from app.services.schemas import HealthResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/readiness", summary="Check database connection")
def health_check(session: Session = Depends(get_session)):
    """Execute a simple SELECT 1 against the DB to verify connectivity."""
    result = session.exec(select(1)).one()
    return {"database": result}

@router.get("/liveness", response_model=HealthResponse)
async def liveness_check():
    """Liveness check - verifies application is running"""
    return HealthResponse(
        status="alive",
        timestamp=datetime.utcnow()
    ) 