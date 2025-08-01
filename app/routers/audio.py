from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select
from app.database import get_session
from app.auth import get_current_active_user
from app.models import User, Audio, Transcription, TranscriptionStatus
from app.schemas import AudioResponse, TranscriptionResponse
from app.services.audio_service import AudioService
from app.tasks import transcribe_audio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/upload", response_model=AudioResponse)
async def upload_audio(
    file: UploadFile = File(...),
    language: str = Form(None),
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Upload audio file for transcription"""
    try:
        audio_service = AudioService()
        audio = await audio_service.upload_audio_file(
            file=file,
            user_id=current_user.id,
            language=language,
            session=session
        )
        
        return AudioResponse.from_orm(audio)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload audio file"
        )


@router.get("/{audio_id}/transcription", response_model=TranscriptionResponse)
async def get_transcription(
    audio_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Get transcription status and result for an audio file"""
    # Verify audio belongs to user
    audio_service = AudioService()
    audio = audio_service.get_audio_by_id(audio_id, current_user.id, session)
    
    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    # Get transcription
    statement = select(Transcription).where(Transcription.audio_id == audio_id)
    transcription = session.exec(statement).first()
    
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    return TranscriptionResponse.from_orm(transcription)


@router.post("/{audio_id}/transcribe")
async def start_transcription(
    audio_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Start transcription process for an audio file"""
    # Verify audio belongs to user
    audio_service = AudioService()
    audio = audio_service.get_audio_by_id(audio_id, current_user.id, session)
    
    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    # Check if transcription already exists
    statement = select(Transcription).where(Transcription.audio_id == audio_id)
    existing_transcription = session.exec(statement).first()
    
    if existing_transcription and existing_transcription.status in [
        TranscriptionStatus.PENDING, 
        TranscriptionStatus.PROCESSING
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcription already in progress"
        )
    
    # Create transcription record if it doesn't exist
    if not existing_transcription:
        transcription = Transcription(
            audio_id=audio_id,
            status=TranscriptionStatus.PENDING
        )
        session.add(transcription)
        session.commit()
        session.refresh(transcription)
    else:
        transcription = existing_transcription
        transcription.status = TranscriptionStatus.PENDING
        session.commit()
    
    # Start async transcription task
    task = transcribe_audio.delay(audio_id)
    
    logger.info(f"Started transcription task for audio {audio_id}: {task.id}")
    
    return {
        "message": "Transcription started",
        "task_id": task.id,
        "transcription_id": transcription.id
    }


@router.get("/transcription/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription_by_id(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Get transcription by ID (if user has access)"""
    # Get transcription with audio info
    statement = select(Transcription).join(Audio).where(
        Transcription.id == transcription_id,
        Audio.user_id == current_user.id
    )
    transcription = session.exec(statement).first()
    
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    return TranscriptionResponse.from_orm(transcription)


@router.get("/", response_model=List[AudioResponse])
async def list_user_audios(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """List all audio files for the current user"""
    audio_service = AudioService()
    audios = audio_service.get_user_audios(
        user_id=current_user.id,
        session=session,
        limit=limit,
        offset=offset
    )
    
    return [AudioResponse.from_orm(audio) for audio in audios]


@router.delete("/{audio_id}")
async def delete_audio(
    audio_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    """Delete audio file and its transcription"""
    audio_service = AudioService()
    success = audio_service.delete_audio_file(audio_id, current_user.id, session)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return {"message": "Audio file deleted successfully"} 