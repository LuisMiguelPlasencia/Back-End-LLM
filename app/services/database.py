from sqlmodel import SQLModel, create_engine, Field, Session, select
from app.config import settings
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

logger = logging.getLogger(__name__)

# Database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)

def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session

# --- Models ------------------------------------------------------------------

class Profile(SQLModel, table=True):
    __tablename__ = "profiles"
    id: UUID = Field(primary_key=True)
    email: str
    name: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    company: Optional[str]
    role: Optional[str]

class Recording(SQLModel, table=True):
    __tablename__ = "recordings"
    id: UUID = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="profiles.id")
    upload_url: str
    filename: str
    duration_seconds: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    transcription_status: str = Field(default="pending")
    transcription_text: Optional[str]
    transcription_completed_at: Optional[datetime]

class RecordingAnalysis(SQLModel, table=True):
    __tablename__ = "recording_analyses"
    id: UUID = Field(default=None, primary_key=True)
    recording_id: UUID = Field(foreign_key="recordings.id")
    score: int
    summary: str
    strengths: List[str] = Field(sa_column=Column(ARRAY(String), nullable=False))
    improvements: List[str] = Field(sa_column=Column(ARRAY(String), nullable=False))
    model_used: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

class WebhookLog(SQLModel, table=True):
    __tablename__ = "webhook_logs"
    id: UUID = Field(default=None, primary_key=True)
    recording_id: Optional[UUID] = Field(foreign_key="recordings.id")
    user_id: Optional[UUID] = Field(foreign_key="profiles.id")
    event_type: str
    status: str
    error_message: Optional[str]
    payload: dict = Field(sa_column=Column(JSONB, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- CRUD helpers ------------------------------------------------------------

def create_profile(session: Session, profile: Profile) -> Profile:
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

def get_profile(session: Session, profile_id: UUID) -> Optional[Profile]:
    return session.get(Profile, profile_id)

def create_recording(session: Session, rec: Recording) -> Recording:
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec

def list_recordings_for_user(session: Session, user_id: UUID) -> List[Recording]:
    q = select(Recording).where(Recording.user_id == user_id)
    return session.exec(q).all()

def update_transcription(
    session: Session,
    recording_id: UUID,
    text: str,
    status: str = "completed",
) -> Recording:
    rec = session.get(Recording, recording_id)
    rec.transcription_text = text
    rec.transcription_status = status
    rec.transcription_completed_at = datetime.utcnow()
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec

def add_analysis(session: Session, analysis: RecordingAnalysis) -> RecordingAnalysis:
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis

def get_analyses_for_recording(
    session: Session, recording_id: UUID
) -> List[RecordingAnalysis]:
    q = select(RecordingAnalysis).where(RecordingAnalysis.recording_id == recording_id)
    return session.exec(q).all()

def log_webhook_event(session: Session, log: WebhookLog) -> WebhookLog:
    session.add(log)
    session.commit()
    session.refresh(log)
    return log
