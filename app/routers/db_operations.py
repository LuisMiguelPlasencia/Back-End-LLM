from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session,select
from uuid import UUID
from typing import List

from app.services.database import (
    get_session,
    create_profile, get_profile,
    create_recording, list_recordings_for_user, update_transcription,
    add_analysis, get_analyses_for_recording,
    log_webhook_event,
    Profile, Recording, RecordingAnalysis, WebhookLog,
)

router = APIRouter(prefix="/dbops", tags=["db operations"])


@router.post("/profiles/", response_model=Profile)
def post_profile(profile: Profile, session: Session = Depends(get_session)):
    return create_profile(session, profile)

@router.get("/profiles/{profile_id}", response_model=Profile)
def get_profile_endpoint(profile_id: UUID, session: Session = Depends(get_session)):
    profile = get_profile(session, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/recordings/", response_model=Recording)
def post_recording(recording: Recording, session: Session = Depends(get_session)):
    return create_recording(session, recording)

@router.get("/recordings/user/{user_id}", response_model=List[Recording])
def get_recordings(user_id: UUID, session: Session = Depends(get_session)):
    return list_recordings_for_user(session, user_id)

@router.patch("/recordings/{recording_id}/transcription", response_model=Recording)
def patch_transcription(recording_id: UUID, text: str, session: Session = Depends(get_session)):
    return update_transcription(session, recording_id, text)

@router.post("/analyses/", response_model=RecordingAnalysis)
def post_analysis(analysis: RecordingAnalysis, session: Session = Depends(get_session)):
    return add_analysis(session, analysis)

@router.get("/analyses/recording/{recording_id}", response_model=List[RecordingAnalysis])
def get_analyses(recording_id: UUID, session: Session = Depends(get_session)):
    return get_analyses_for_recording(session, recording_id)

@router.post("/webhook-logs/", response_model=WebhookLog)
def post_webhook(log: WebhookLog, session: Session = Depends(get_session)):
    return log_webhook_event(session, log)
