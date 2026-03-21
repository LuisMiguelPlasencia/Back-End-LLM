# ---------------------------------------------------------------------------
# Conversation service
# ---------------------------------------------------------------------------
# CRUD operations for conversations, plus scoring / profiling persistence.
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.services.db import execute_query, execute_query_one, get_transaction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

async def get_conversation_details(conversation_id: UUID) -> List[Dict]:
    """Return conversation + scoring details for a single conversation."""
    query = """
        SELECT
            c.conversation_id, c.start_timestamp, c.end_timestamp, c.status,
            c.created_at, c.updated_at, c.course_id,
            sbc.general_score, sbc.fillerwords_scoring, sbc.clarity_scoring,
            sbc.participation_scoring, sbc.keythemes_scoring, sbc.indexofquestions_scoring,
            sbc.rhythm_scoring, sbc.fillerwords_feedback, sbc.clarity_feedback,
            sbc.participation_feedback, sbc.keythemes_feedback,
            sbc.indexofquestions_feedback, sbc.rhythm_feedback, sbc.is_accomplished
        FROM conversaApp.conversations c
        LEFT JOIN conversaapp.scoring_by_conversation sbc
            ON c.conversation_id = sbc.conversation_id
        WHERE c.conversation_id = $1
        ORDER BY c.start_timestamp DESC
    """
    results = await execute_query(query, conversation_id)
    return [dict(row) for row in results]


async def get_user_conversations(user_id: UUID) -> List[Dict]:
    """Return the 10 most recent conversations for a user, with scoring data."""
    query = """
        SELECT
            c.conversation_id, c.start_timestamp, c.end_timestamp, c.status,
            c.created_at, c.updated_at, c.course_id,
            mc.name, mc.image_src,
            sbc.general_score, sbc.fillerwords_scoring, sbc.clarity_scoring,
            sbc.participation_scoring, sbc.keythemes_scoring, sbc.indexofquestions_scoring,
            sbc.rhythm_scoring, c.fillerwords_feedback, sbc.clarity_feedback,
            sbc.participation_feedback, sbc.keythemes_feedback,
            sbc.indexofquestions_feedback, sbc.rhythm_feedback, sbc.is_accomplished,
            m.message_count
        FROM conversaApp.conversations c
        LEFT JOIN conversaconfig.master_courses mc ON c.course_id = mc.course_id
        LEFT JOIN (
            SELECT conversation_id, COUNT(*) AS message_count
            FROM conversaapp.messages
            GROUP BY conversation_id
        ) m ON c.conversation_id = m.conversation_id
        LEFT JOIN conversaapp.scoring_by_conversation sbc
            ON c.conversation_id = sbc.conversation_id
        WHERE c.user_id = $1
        ORDER BY c.start_timestamp DESC
        LIMIT 10
    """
    results = await execute_query(query, user_id)
    return [dict(row) for row in results]


async def get_user_profiling_by_conversations(user_id: UUID) -> Dict[str, list]:
    """Return profiling scores from the user's last 10 completed conversations.

    Returns a dict mapping column names → lists of values, or empty dict when
    no qualifying rows exist.
    """
    query = """
        SELECT
            pbc.empathy_scoring, pbc.prospection_scoring, pbc.resilience_scoring,
            pbc.technical_domain_scoring, pbc.negotiation_scoring,
            pbc.empathy_feedback, pbc.prospection_feedback, pbc.resilience_feedback,
            pbc.technical_domain_feedback, pbc.negotiation_feedback
        FROM conversaApp.conversations c
        LEFT JOIN conversaapp.profiling_by_conversation pbc
            ON c.conversation_id = pbc.conversation_id
        WHERE c.user_id = $1
          AND pbc.prospection_scoring IS NOT NULL
          AND pbc.empathy_scoring IS NOT NULL
          AND pbc.resilience_scoring IS NOT NULL
          AND pbc.technical_domain_scoring IS NOT NULL
          AND pbc.negotiation_scoring IS NOT NULL
          AND pbc.prospection_feedback IS NOT NULL
          AND pbc.empathy_feedback IS NOT NULL
          AND pbc.resilience_feedback IS NOT NULL
          AND pbc.technical_domain_feedback IS NOT NULL
          AND pbc.negotiation_feedback IS NOT NULL
        ORDER BY c.start_timestamp DESC
        LIMIT 10
    """
    try:
        results = await execute_query(query, user_id)
        if not results:
            return {}

        output: Dict[str, list] = {key: [] for key in results[0].keys()}
        for row in results:
            for key, value in row.items():
                output[key].append(value)
        return output
    except Exception:
        logger.exception("Error fetching profiling for user %s", user_id)
        return {}


async def get_voice_agent(stage_id: UUID) -> Optional[Dict]:
    """Retrieve the voice_id and agent_id configured for a stage."""
    query = "SELECT voice_id, agent_id FROM conversaconfig.course_stages WHERE stage_id = $1"
    result = await execute_query(query, stage_id)
    return dict(result[0]) if result else None


async def get_conversation_status(conversation_id: UUID, user_id: UUID) -> Optional[str]:
    """Return the status string for a conversation, or None if not found."""
    row = await execute_query_one(
        "SELECT status FROM conversaApp.conversations WHERE conversation_id = $1 AND user_id = $2",
        conversation_id,
        user_id,
    )
    return row["status"] if row else None


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

async def create_conversation(user_id: UUID, course_id: UUID, stage_id: UUID) -> Optional[Dict]:
    """Insert a new conversation row and return the created record."""
    query = """
        INSERT INTO conversaApp.conversations
            (user_id, course_id, stage_id, conversation_id, start_timestamp, status, created_at, updated_at)
        VALUES ($1, $2, $3, gen_random_uuid(), now(), 'OPEN', now(), now())
        RETURNING conversation_id, user_id, course_id, stage_id, start_timestamp, status, created_at
    """
    result = await execute_query_one(query, user_id, course_id, stage_id)
    return dict(result) if result else None


async def close_conversation(
    user_id: UUID,
    conversation_id: UUID,
    conversation_id_elevenlabs: str,
    agent_id: str,
) -> bool:
    """Mark a conversation as FINISHED and record ElevenLabs metadata."""
    await execute_query(
        """
        UPDATE conversaApp.conversations
        SET status = 'FINISHED',
            end_timestamp = now(),
            conversation_id_elevenlabs = $3,
            agent_id = $4
        WHERE user_id = $1 AND conversation_id = $2
        """,
        user_id,
        conversation_id,
        conversation_id_elevenlabs,
        agent_id,
    )
    return True


# ---------------------------------------------------------------------------
# Scoring persistence
# ---------------------------------------------------------------------------

async def set_conversation_scoring(
    fillerwords_scoring: float,
    clarity_scoring: float,
    participation_scoring: float,
    keythemes_scoring: float,
    indexofquestions_scoring: float,
    rhythm_scoring: float,
    fillerwords_feedback: str,
    clarity_feedback: str,
    participation_feedback: str,
    keythemes_feedback: str,
    indexofquestions_feedback: str,
    rhythm_feedback: str,
    puntuacion_global: float,
    objetivo: bool,
    conv_id: UUID,
) -> None:
    """Insert a scoring record for a finished conversation."""
    query = """
        INSERT INTO conversaapp.scoring_by_conversation
            (scoring_id, conversation_id,
             fillerwords_scoring, clarity_scoring, participation_scoring,
             keythemes_scoring, indexofquestions_scoring, rhythm_scoring,
             fillerwords_feedback, clarity_feedback, indexofquestions_feedback,
             participation_feedback, keythemes_feedback, rhythm_feedback,
             general_score, is_accomplished)
        VALUES (gen_random_uuid(), $15,
                $1, $2, $3, $4, $5, $6,
                $7, $8, $11, $9, $10, $12,
                $13, $14)
    """
    await execute_query_one(
        query,
        fillerwords_scoring, clarity_scoring, participation_scoring,
        keythemes_scoring, indexofquestions_scoring, rhythm_scoring,
        fillerwords_feedback, clarity_feedback, participation_feedback,
        keythemes_feedback, indexofquestions_feedback, rhythm_feedback,
        puntuacion_global, objetivo, conv_id,
    )


# ---------------------------------------------------------------------------
# Profiling persistence
# ---------------------------------------------------------------------------

async def set_conversation_profiling(
    prospection_scoring: int,
    empathy_scoring: int,
    technical_domain_scoring: int,
    negotiation_scoring: int,
    resilience_scoring: int,
    prospection_feedback: str,
    empathy_feedback: str,
    technical_domain_feedback: str,
    negotiation_feedback: str,
    resilience_feedback: str,
    conv_id: UUID,
) -> None:
    """Insert a profiling record for a finished conversation."""
    query = """
        INSERT INTO conversaapp.profiling_by_conversation
            (profiling_id, conversation_id,
             prospection_scoring, empathy_scoring, technical_domain_scoring,
             negotiation_scoring, resilience_scoring,
             prospection_feedback, empathy_feedback, technical_domain_feedback,
             negotiation_feedback, resilience_feedback)
        VALUES (gen_random_uuid(), $11,
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10)
    """
    await execute_query_one(
        query,
        prospection_scoring, empathy_scoring, technical_domain_scoring,
        negotiation_scoring, resilience_scoring,
        prospection_feedback, empathy_feedback, technical_domain_feedback,
        negotiation_feedback, resilience_feedback,
        conv_id,
    )


async def set_general_profiling(
    prospection_scoring: int,
    empathy_scoring: int,
    technical_domain_scoring: int,
    negotiation_scoring: int,
    resilience_scoring: int,
    prospection_feedback: str,
    empathy_feedback: str,
    technical_domain_feedback: str,
    negotiation_feedback: str,
    resilience_feedback: str,
    user_id: UUID,
) -> None:
    """Upsert the global profiling snapshot for a user."""
    query = """
        INSERT INTO conversascoring.user_profile
            (prospection_score, empathy_score, technical_domain_score,
             negotiation_score, resilience_score,
             prospection_feedback, empathy_feedback, technical_domain_feedback,
             negotiation_feedback, resilience_feedback,
             user_id, event_timestamp)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            event_timestamp           = NOW(),
            prospection_score         = EXCLUDED.prospection_score,
            empathy_score             = EXCLUDED.empathy_score,
            technical_domain_score    = EXCLUDED.technical_domain_score,
            negotiation_score         = EXCLUDED.negotiation_score,
            resilience_score          = EXCLUDED.resilience_score,
            prospection_feedback      = EXCLUDED.prospection_feedback,
            empathy_feedback          = EXCLUDED.empathy_feedback,
            technical_domain_feedback = EXCLUDED.technical_domain_feedback,
            negotiation_feedback      = EXCLUDED.negotiation_feedback,
            resilience_feedback       = EXCLUDED.resilience_feedback
    """
    await execute_query_one(
        query,
        prospection_scoring, empathy_scoring, technical_domain_scoring,
        negotiation_scoring, resilience_scoring,
        prospection_feedback, empathy_feedback, technical_domain_feedback,
        negotiation_feedback, resilience_feedback,
        user_id,
    )
    logger.info("General profiling upserted for user %s", user_id)


async def set_user_profile(
    user_id: UUID,
    general_score: float,
    profile_type: str,
) -> None:
    """Upsert the user's aggregate profile (score + type label)."""
    query = """
        INSERT INTO conversascoring.user_profile
            (user_id, event_timestamp, general_score, profile_type)
        VALUES ($1, NOW(), $2, $3)
        ON CONFLICT (user_id) DO UPDATE SET
            event_timestamp = NOW(),
            general_score   = EXCLUDED.general_score,
            profile_type    = EXCLUDED.profile_type
    """
    await execute_query_one(query, user_id, general_score, profile_type)
