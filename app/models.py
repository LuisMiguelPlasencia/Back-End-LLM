from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship





class TextEntry(SQLModel, table=True):
    __tablename__ = "text_entries"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    content: str
    language: Optional[str] = None
    source: Optional[str] = None  # "upload", "recording", "file"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


 