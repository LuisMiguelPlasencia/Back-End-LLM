# ---------------------------------------------------------------------------
# Profiling service
# ---------------------------------------------------------------------------
# Evaluates per-conversation profiling and computes the general (aggregate)
# profiling snapshot for a user by calling GPT on accumulated feedback.
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging

import numpy as np

from app.services.conversations_service import (
    get_user_profiling_by_conversations,
    set_conversation_profiling,
    set_general_profiling,
)
from app.services.messages_service import get_conversation_transcript
from app.prompting_templates.profiling.general_feedback import (
    general_feedback_empathy,
    general_feedback_negotiation,
    general_feedback_prospection,
    general_feedback_resilience,
    general_feedback_technical_domain,
)
from app.utils.call_gpt import call_gpt
from app.utils.openai_client import get_openai_client
from scoring_scripts.get_conver_skills import get_conver_skills

logger = logging.getLogger(__name__)


async def profiling(conv_id, course_id, stage_id):
    """Evaluate a finished conversation and persist per-conversation profiling."""
    transcript = await get_conversation_transcript(conv_id)
    if not transcript:
        logger.warning("No messages found for conversation_id=%s", conv_id)
        return

    result = await get_conver_skills(transcript)

    # Extract scores and feedback
    dimensions = ("prospection", "empathy", "technical_domain", "negotiation", "resilience")
    scores = {d: result[d]["score"] for d in dimensions}
    feedback = {d: result[d]["justification"] for d in dimensions}

    logger.info(
        "Profiling computed for conv %s: %s",
        conv_id,
        {d: scores[d] for d in dimensions},
    )

    await set_conversation_profiling(
        scores["prospection"], scores["empathy"], scores["technical_domain"],
        scores["negotiation"], scores["resilience"],
        feedback["prospection"], feedback["empathy"], feedback["technical_domain"],
        feedback["negotiation"], feedback["resilience"],
        conv_id,
    )


async def general_profiling(user_id):
    """Compute and persist the aggregate profiling for a user.

    Reads per-conversation feedback from the last 10 conversations, then
    sends each dimension's feedback list to GPT for a consolidated summary.
    """
    client = get_openai_client()

    individual_feedbacks = await get_user_profiling_by_conversations(user_id)

    dimensions = ("prospection", "empathy", "resilience", "negotiation", "technical_domain")

    if individual_feedbacks:
        fb = {d: individual_feedbacks.get(f"{d}_feedback", []) for d in dimensions}
        avgs = {d: float(np.mean(individual_feedbacks.get(f"{d}_scoring", [0]))) for d in dimensions}
    else:
        fb = {d: [] for d in dimensions}
        avgs = {d: 0.0 for d in dimensions}

    min_samples = min(len(fb[d]) for d in dimensions)

    prompt_map = {
        "prospection": general_feedback_prospection,
        "empathy": general_feedback_empathy,
        "negotiation": general_feedback_negotiation,
        "resilience": general_feedback_resilience,
        "technical_domain": general_feedback_technical_domain,
    }

    if min_samples > 0:
        general_fb = {
            d: call_gpt(client, prompt_map[d](fb[d]), ensure_json=False)
            for d in dimensions
        }
    else:
        logger.info("No individual feedbacks for user %s — skipping GPT calls.", user_id)
        general_fb = {d: "" for d in dimensions}

    await set_general_profiling(
        avgs["prospection"], avgs["empathy"], avgs["technical_domain"],
        avgs["negotiation"], avgs["resilience"],
        general_fb["prospection"], general_fb["empathy"], general_fb["technical_domain"],
        general_fb["negotiation"], general_fb["resilience"],
        user_id,
    )
