import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import get_session
from app.models import User, Audio, Transcription
from app.config import settings


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture():
    """Create test database session"""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with dependency override"""
    def get_session_override():
        yield session
    
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    """Create test user"""
    user = User(
        supabase_id="test-user-id",
        email="test@example.com",
        full_name="Test User"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_audio")
def test_audio_fixture(session: Session, test_user: User):
    """Create test audio file"""
    audio = Audio(
        user_id=test_user.id,
        filename="test-audio.wav",
        original_filename="test.wav",
        file_size=1024,
        mime_type="audio/wav",
        storage_path="test/path/audio.wav",
        status="uploaded"
    )
    session.add(audio)
    session.commit()
    session.refresh(audio)
    return audio


@pytest.fixture(name="test_transcription")
def test_transcription_fixture(session: Session, test_audio: Audio):
    """Create test transcription"""
    transcription = Transcription(
        audio_id=test_audio.id,
        status="completed",
        text="Test transcription text",
        confidence=0.95,
        language="en"
    )
    session.add(transcription)
    session.commit()
    session.refresh(transcription)
    return transcription 