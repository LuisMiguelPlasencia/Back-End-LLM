from sqlmodel import SQLModel, create_engine, Session
from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)


def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session


def get_supabase():
    """Get Supabase client"""
    return supabase 