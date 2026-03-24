# ---------------------------------------------------------------------------
# Landing-page chatbot router
# ---------------------------------------------------------------------------

from __future__ import annotations

from fastapi import APIRouter

from app.services.landing_page_assistant import LandingPageAssistant

router = APIRouter(prefix="/landing_page", tags=["Landing Page"])

# Singleton assistant — reuses the underlying OpenAI client across requests.
_assistant = LandingPageAssistant()


@router.get("/landing-assistant")
async def landing_assistant_response(question: str):
    """Answer a visitor's question about Conversa."""
    return _assistant.answer_user_question(question)
