from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


class TranscriptionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AudioStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    supabase_id: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    audios: List["Audio"] = Relationship(back_populates="user")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")


class Audio(SQLModel, table=True):
    __tablename__ = "audios"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    filename: str = Field(index=True)
    original_filename: str
    file_size: int
    mime_type: str
    storage_path: str
    status: AudioStatus = Field(default=AudioStatus.UPLOADED)
    language: Optional[str] = None
    duration: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="audios")
    transcription: Optional["Transcription"] = Relationship(back_populates="audio")


class Transcription(SQLModel, table=True):
    __tablename__ = "transcriptions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    audio_id: int = Field(foreign_key="audios.id", unique=True)
    status: TranscriptionStatus = Field(default=TranscriptionStatus.PENDING)
    text: Optional[str] = None
    confidence: Optional[float] = None
    language: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    audio: Audio = Relationship(back_populates="transcription")


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="chat_sessions")
    messages: List["Message"] = Relationship(back_populates="chat_session")


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_session_id: int = Field(foreign_key="chat_sessions.id")
    role: str = Field(index=True)  # "user" or "assistant"
    content: str
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    chat_session: ChatSession = Relationship(back_populates="messages") 