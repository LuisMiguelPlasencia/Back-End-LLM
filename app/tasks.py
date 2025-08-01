import time
from typing import Optional
from celery import Celery
from sqlmodel import Session, select
from app.config import settings
from app.database import engine
from app.models import Audio, Transcription, TranscriptionStatus, AudioStatus
from app.services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "speech_to_text",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True)
def transcribe_audio(self, audio_id: int) -> dict:
    """Transcribe audio file using speech recognition"""
    start_time = time.time()
    
    try:
        # Get audio file from database
        with Session(engine) as session:
            statement = select(Audio).where(Audio.id == audio_id)
            audio = session.exec(statement).first()
            
            if not audio:
                raise Exception(f"Audio file not found: {audio_id}")
            
            # Update status to processing
            audio.status = AudioStatus.PROCESSING
            session.commit()
            
            # Create or update transcription record
            statement = select(Transcription).where(Transcription.audio_id == audio_id)
            transcription = session.exec(statement).first()
            
            if not transcription:
                transcription = Transcription(
                    audio_id=audio_id,
                    status=TranscriptionStatus.PROCESSING
                )
                session.add(transcription)
            else:
                transcription.status = TranscriptionStatus.PROCESSING
            
            session.commit()
            
            # TODO: Implement actual speech recognition here
            # For now, we'll simulate transcription
            # In production, you would use:
            # - OpenAI Whisper API
            # - Google Speech-to-Text
            # - Azure Speech Services
            # - AWS Transcribe
            
            # Simulate processing time
            time.sleep(2)
            
            # Simulate transcription result
            transcribed_text = f"Simulated transcription for audio {audio_id}. This is a placeholder for actual speech recognition."
            confidence = 0.95
            detected_language = audio.language or "en"
            
            # Update transcription with results
            transcription.text = transcribed_text
            transcription.confidence = confidence
            transcription.language = detected_language
            transcription.status = TranscriptionStatus.COMPLETED
            transcription.processing_time = time.time() - start_time
            
            # Update audio status
            audio.status = AudioStatus.COMPLETED
            
            session.commit()
            
            logger.info(f"Transcription completed for audio {audio_id}")
            
            return {
                "success": True,
                "audio_id": audio_id,
                "transcription_id": transcription.id,
                "text": transcribed_text,
                "confidence": confidence,
                "language": detected_language,
                "processing_time": transcription.processing_time
            }
            
    except Exception as e:
        logger.error(f"Transcription failed for audio {audio_id}: {e}")
        
        # Update status to failed
        with Session(engine) as session:
            statement = select(Audio).where(Audio.id == audio_id)
            audio = session.exec(statement).first()
            if audio:
                audio.status = AudioStatus.FAILED
                session.commit()
            
            statement = select(Transcription).where(Transcription.audio_id == audio_id)
            transcription = session.exec(statement).first()
            if transcription:
                transcription.status = TranscriptionStatus.FAILED
                transcription.error_message = str(e)
                session.commit()
        
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True)
def generate_llm_response(self, transcription_id: int, user_message: str, provider: str = "openai") -> dict:
    """Generate LLM response based on transcription and user message"""
    try:
        # Get transcription from database
        with Session(engine) as session:
            statement = select(Transcription).where(Transcription.id == transcription_id)
            transcription = session.exec(statement).first()
            
            if not transcription:
                raise Exception(f"Transcription not found: {transcription_id}")
            
            if transcription.status != TranscriptionStatus.COMPLETED:
                raise Exception(f"Transcription not completed: {transcription_id}")
        
        # Generate LLM response
        llm_service = LLMService(provider=provider)
        result = llm_service.generate_chat_response(
            user_message=user_message,
            transcription_text=transcription.text
        )
        
        logger.info(f"LLM response generated for transcription {transcription_id}")
        
        return {
            "success": True,
            "transcription_id": transcription_id,
            "response": result["text"],
            "tokens_used": result["tokens_used"],
            "model_used": result["model_used"]
        }
        
    except Exception as e:
        logger.error(f"LLM response generation failed for transcription {transcription_id}: {e}")
        raise self.retry(countdown=30, max_retries=2)


@celery_app.task
def cleanup_failed_transcriptions():
    """Clean up failed transcriptions older than 24 hours"""
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    with Session(engine) as session:
        # Find failed transcriptions older than 24 hours
        statement = select(Transcription).where(
            Transcription.status == TranscriptionStatus.FAILED,
            Transcription.created_at < cutoff_time
        )
        failed_transcriptions = session.exec(statement).all()
        
        for transcription in failed_transcriptions:
            session.delete(transcription)
        
        session.commit()
        
        logger.info(f"Cleaned up {len(failed_transcriptions)} failed transcriptions")
    
    return {"cleaned_count": len(failed_transcriptions)} 