# ---------------------------------------------------------------------------
# Scoring service
# ---------------------------------------------------------------------------
# Computes per-conversation scores (filler words, clarity, participation,
# key themes, questions index, rhythm) and persists them.
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging

from app.services.conversations_service import set_conversation_scoring
from app.services.messages_service import get_conversation_transcript
from scoring_scripts.get_conver_scores import get_conver_scores

logger = logging.getLogger(__name__)


async def scoring(conv_id, course_id, stage_id) -> bool | None:
    """Score a finished conversation and persist results.

    Returns the *objetivo* (goal-accomplished) boolean, or ``None`` when
    no transcript exists.
    """
    transcript = await get_conversation_transcript(conv_id)
    if not transcript:
        logger.warning("No messages found for conversation_id=%s", conv_id)
        return None

    result = await get_conver_scores(transcript, course_id, stage_id)

    scores = result["detalle"]
    feedback = result["feedback"]
    puntuacion_global = result["puntuacion_global"]
    objetivo = result["objetivo"]

    score_fields = {
        "fillerwords": "muletillas_pausas",
        "clarity": "claridad",
        "participation": "participacion",
        "keythemes": "cobertura",
        "indexofquestions": "preguntas",
        "rhythm": "ppm",
    }

    s = {k: scores.get(v) for k, v in score_fields.items()}
    f = {k: feedback.get(v) for k, v in score_fields.items()}

    logger.info(
        "Scores for conv %s: global=%s, objective=%s, detail=%s",
        conv_id, puntuacion_global, objetivo, s,
    )

    await set_conversation_scoring(
        s["fillerwords"], s["clarity"], s["participation"],
        s["keythemes"], s["indexofquestions"], s["rhythm"],
        f["fillerwords"], f["clarity"], f["participation"],
        f["keythemes"], f["indexofquestions"], f["rhythm"],
        puntuacion_global, objetivo, conv_id,
    )

    return objetivo
