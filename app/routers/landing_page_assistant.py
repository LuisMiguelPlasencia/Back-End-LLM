from app.services.landing_page_assistant import LandingPageAssistant
from fastapi import APIRouter

router = APIRouter()

# Create a single LandingPageAssistant at import time so we reuse the
# underlying OpenAI client across requests.
assistant = LandingPageAssistant()


@router.get("/landing-assistant")
async def landing_assistant_response(question: str):
    return assistant.answer_user_question(question)
