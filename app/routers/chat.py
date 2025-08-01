from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.auth import get_current_active_user
from app.models import User, Transcription, ChatSession, Message
from app.schemas import (
    ChatCompletionRequest, 
    ChatCompletionResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    MessageCreate,
    MessageResponse
)
from app.services.llm_service import LLMService
from app.tasks import generate_llm_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/completion", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Generate LLM response based on transcription and user message"""
    try:
        # Verify transcription exists and belongs to user
        statement = select(Transcription).join(Audio).where(
            Transcription.id == request.transcription_id,
            Audio.user_id == current_user.id
        )
        transcription = session.exec(statement).first()
        
        if not transcription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription not found"
            )
        
        if transcription.status != TranscriptionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcription not completed"
            )
        
        # Generate LLM response
        llm_service = LLMService()
        result = await llm_service.generate_chat_response(
            user_message=request.message,
            transcription_text=transcription.text
        )
        
        return ChatCompletionResponse(
            message=result["text"],
            tokens_used=result["tokens_used"],
            model_used=result["model_used"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response"
        )


@router.post("/completion/async")
async def chat_completion_async(
    request: ChatCompletionRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Generate LLM response asynchronously"""
    # Verify transcription exists and belongs to user
    statement = select(Transcription).join(Audio).where(
        Transcription.id == request.transcription_id,
        Audio.user_id == current_user.id
    )
    transcription = session.exec(statement).first()
    
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    if transcription.status != TranscriptionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcription not completed"
        )
    
    # Start async task
    task = generate_llm_response.delay(
        transcription_id=request.transcription_id,
        user_message=request.message
    )
    
    logger.info(f"Started async LLM response task: {task.id}")
    
    return {
        "message": "LLM response generation started",
        "task_id": task.id,
        "transcription_id": request.transcription_id
    }


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db_session: Session = Depends(get_session)
):
    """Create a new chat session"""
    chat_session = ChatSession(
        user_id=current_user.id,
        title=session_data.title
    )
    
    db_session.add(chat_session)
    db_session.commit()
    db_session.refresh(chat_session)
    
    return ChatSessionResponse.from_orm(chat_session)


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """List all chat sessions for the current user"""
    statement = select(ChatSession).where(
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).order_by(ChatSession.created_at.desc())
    
    chat_sessions = session.exec(statement).all()
    return [ChatSessionResponse.from_orm(cs) for cs in chat_sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Get a specific chat session"""
    statement = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    )
    
    chat_session = session.exec(statement).first()
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return ChatSessionResponse.from_orm(chat_session)


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def add_message(
    session_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Add a message to a chat session"""
    # Verify chat session belongs to user
    statement = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    )
    chat_session = session.exec(statement).first()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    message = Message(
        chat_session_id=session_id,
        content=message_data.content,
        role=message_data.role
    )
    
    session.add(message)
    session.commit()
    session.refresh(message)
    
    return MessageResponse.from_orm(message)


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Get all messages in a chat session"""
    # Verify chat session belongs to user
    statement = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    )
    chat_session = session.exec(statement).first()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Get messages
    statement = select(Message).where(
        Message.chat_session_id == session_id
    ).order_by(Message.created_at)
    
    messages = session.exec(statement).all()
    return [MessageResponse.from_orm(msg) for msg in messages] 