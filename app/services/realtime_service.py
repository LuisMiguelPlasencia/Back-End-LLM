# ---------------------------------------------------------------------------
# Realtime service — post-conversation processing
# ---------------------------------------------------------------------------
# Called when the ElevenLabs bridge closes. Orchestrates:
#   scoring → profiling → general profiling → user classification → progress
# ---------------------------------------------------------------------------

from __future__ import annotations

import base64
import json
import logging

import numpy as np

from app.services.conversations_service import close_conversation, get_conversation_status
from app.services.messages_service import update_user_course_progress
from app.services.scoring_service import scoring
from app.services.profiling_service import profiling, general_profiling
from scoring_scripts.get_user_profile import user_clasiffier

logger = logging.getLogger(__name__)


async def stop_process(
    user_id,
    conversation_id,
    frontend_ws,
    course_id,
    stage_id,
    conversation_id_elevenlabs,
    agent_id,
):
    """End-of-conversation pipeline: close → score → profile → notify."""
    await close_conversation(user_id, conversation_id, conversation_id_elevenlabs, agent_id)

    objetivo = await scoring(conversation_id, course_id, stage_id)
    await profiling(conversation_id, course_id, stage_id)
    await general_profiling(user_id)
    await user_clasiffier(user_id)

    if objetivo:
        await update_user_course_progress(user_id, course_id)

    # Notify frontend that scoring is complete
    await frontend_ws.send_text(
        json.dumps({
            "type": "conversation.scoring.completed",
            "conversation_id": str(conversation_id),
        })
    )


async def user_msg_processed(user_id, conversation_id):
    """Hook for any processing when a user message is received (no-op)."""
    pass


def is_non_silent(audio_b64: str, threshold: float = 0.05) -> bool:
    """Check whether a base64-encoded PCM16 audio chunk exceeds the silence threshold."""
    pcm = np.frombuffer(base64.b64decode(audio_b64), dtype=np.int16)
    rms = np.sqrt(np.mean((pcm / 32768.0) ** 2))
    return rms > threshold
