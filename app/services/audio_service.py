import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from sqlmodel import Session, select
from app.config import settings
from app.database import get_supabase
from app.models import Audio, AudioStatus, User
import logging

logger = logging.getLogger(__name__)


class AudioService:
    """Service for audio file management"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.max_file_size = settings.max_file_size
        self.allowed_types = settings.allowed_audio_types_list
    
    def validate_audio_file(self, file: UploadFile) -> None:
        """Validate uploaded audio file"""
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file size
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {self.max_file_size} bytes"
            )
        
        # Check MIME type
        if file.content_type not in self.allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_types)}"
            )
    
    async def upload_audio_file(
        self, 
        file: UploadFile, 
        user_id: int, 
        language: Optional[str] = None,
        session: Session = None
    ) -> Audio:
        """Upload audio file to Supabase Storage and create database record"""
        try:
            # Validate file
            self.validate_audio_file(file)
            
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ".wav"
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Create storage path
            storage_path = f"audios/{user_id}/{unique_filename}"
            
            # Upload to Supabase Storage
            file_content = await file.read()
            result = self.supabase.storage.from_("audio-files").upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": file.content_type}
            )
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload file to storage"
                )
            
            # Create database record
            audio = Audio(
                user_id=user_id,
                filename=unique_filename,
                original_filename=file.filename or "unknown",
                file_size=len(file_content),
                mime_type=file.content_type,
                storage_path=storage_path,
                status=AudioStatus.UPLOADED,
                language=language
            )
            
            if session:
                session.add(audio)
                session.commit()
                session.refresh(audio)
            
            logger.info(f"Audio file uploaded successfully: {audio.id}")
            return audio
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading audio file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload audio file"
            )
    
    def get_audio_by_id(self, audio_id: int, user_id: int, session: Session) -> Optional[Audio]:
        """Get audio file by ID for specific user"""
        statement = select(Audio).where(
            Audio.id == audio_id,
            Audio.user_id == user_id
        )
        return session.exec(statement).first()
    
    def get_user_audios(self, user_id: int, session: Session, limit: int = 50, offset: int = 0):
        """Get all audio files for a user"""
        statement = select(Audio).where(
            Audio.user_id == user_id
        ).order_by(Audio.created_at.desc()).offset(offset).limit(limit)
        
        return session.exec(statement).all()
    
    def delete_audio_file(self, audio_id: int, user_id: int, session: Session) -> bool:
        """Delete audio file from storage and database"""
        audio = self.get_audio_by_id(audio_id, user_id, session)
        if not audio:
            return False
        
        try:
            # Delete from Supabase Storage
            self.supabase.storage.from_("audio-files").remove([audio.storage_path])
            
            # Delete from database
            session.delete(audio)
            session.commit()
            
            logger.info(f"Audio file deleted: {audio_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting audio file: {e}")
            return False
    
    def get_audio_download_url(self, audio: Audio) -> str:
        """Get download URL for audio file"""
        try:
            result = self.supabase.storage.from_("audio-files").get_public_url(audio.storage_path)
            return result
        except Exception as e:
            logger.error(f"Error getting download URL: {e}")
            return "" 