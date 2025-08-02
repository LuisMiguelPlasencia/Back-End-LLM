from typing import List
from fastapi import APIRouter, HTTPException, status, Form, Depends
from sqlmodel import Session, select
from app.database import get_session
from app.models import TextEntry
from app.schemas import TextUpload, TextResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/text", tags=["text"])


@router.post("/upload", response_model=TextResponse)
async def upload_text(
    title: str = Form(...),
    content: str = Form(...),
    language: str = Form(None),
    source: str = Form(None),
    session: Session = Depends(get_session)
):
    """Upload text content to database"""
    try:
        # Create text entry
        text_entry = TextEntry(
            title=title,
            content=content,
            language=language,
            source=source
        )
        
        session.add(text_entry)
        session.commit()
        session.refresh(text_entry)
        
        logger.info(f"Text entry created successfully: {text_entry.id}")
        return TextResponse.from_orm(text_entry)
        
    except Exception as e:
        logger.error(f"Error creating text entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create text entry"
        )


@router.get("/", response_model=List[TextResponse])
async def list_text_entries(
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session)
):
    """List all text entries"""
    statement = select(TextEntry).order_by(TextEntry.created_at.desc()).offset(offset).limit(limit)
    text_entries = session.exec(statement).all()
    
    return [TextResponse.from_orm(entry) for entry in text_entries]


@router.get("/{text_id}", response_model=TextResponse)
async def get_text_entry(
    text_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific text entry"""
    statement = select(TextEntry).where(TextEntry.id == text_id)
    text_entry = session.exec(statement).first()
    
    if not text_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Text entry not found"
        )
    
    return TextResponse.from_orm(text_entry)


@router.delete("/{text_id}")
async def delete_text_entry(
    text_id: int,
    session: Session = Depends(get_session)
):
    """Delete a text entry"""
    statement = select(TextEntry).where(TextEntry.id == text_id)
    text_entry = session.exec(statement).first()
    
    if not text_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Text entry not found"
        )
    
    session.delete(text_entry)
    session.commit()
    
    return {"message": "Text entry deleted successfully"} 