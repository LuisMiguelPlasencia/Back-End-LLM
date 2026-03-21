# ---------------------------------------------------------------------------
# Message service
# ---------------------------------------------------------------------------
# Handles message CRUD, scoring queries, analytics, profiling reads,
# company dashboard stats, and user journey / progress management.
# ---------------------------------------------------------------------------

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.services.db import execute_query, execute_query_one

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transcript / Messages
# ---------------------------------------------------------------------------

async def get_conversation_transcript(conversation_id: UUID) -> List[Dict]:
    """Return a chronological transcript mapped to Spanish speaker labels."""
    query = """
        SELECT role, content, created_at, duration
        FROM conversaapp.messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
    """
    results = await execute_query(query, conversation_id)

    role_map = {"user": "vendedor", "assistant": "cliente"}
    return [
        {
            "speaker": role_map.get(row["role"], row["role"]),
            "text": row["content"],
            "duracion": float(row["duration"]) if row["duration"] is not None else None,
        }
        for row in results
    ]


async def get_conversation_messages(conversation_id: UUID) -> List[Dict]:
    """Return all messages for a conversation, chronologically."""
    query = """
        SELECT id, user_id, conversation_id, role, content, created_at, duration
        FROM conversaApp.messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
    """
    results = await execute_query(query, conversation_id)
    return [dict(row) for row in results]


async def send_message(
    user_id: UUID,
    conversation_id: UUID,
    message: str,
    role: str,
    duration: float | None,
) -> Optional[Dict]:
    """Persist a message and return the created row."""
    query = """
        INSERT INTO conversaApp.messages
            (id, user_id, conversation_id, role, content, created_at, duration)
        VALUES (gen_random_uuid(), $1, $2, $4, $3, now(), $5)
        RETURNING id, user_id, conversation_id, role, content, created_at, duration
    """
    row = await execute_query_one(query, user_id, conversation_id, message, role, duration)
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Company-level scoring analytics
# ---------------------------------------------------------------------------

async def get_all_user_scoring_by_company(company_id: str) -> List[Dict]:
    """Top-5 leaderboard by average score for a company."""
    try:
        query = """
            WITH user_scores AS (
                SELECT
                    ui.user_id, ui.name, ui.avatar,
                    COALESCE(ROUND(AVG(sbc.general_score))::int, 0) AS puntaje
                FROM conversaconfig.user_info ui
                JOIN conversaapp.conversations c ON ui.user_id = c.user_id
                JOIN conversaapp.scoring_by_conversation sbc
                    ON c.conversation_id = sbc.conversation_id
                WHERE ui.company_id = $1
                  AND sbc.general_score > 0
                  AND c.status = 'FINISHED'
                GROUP BY ui.user_id, ui.name, ui.avatar
            ),
            user_completed_courses AS (
                SELECT uja.user_id,
                       COUNT(ucp.course_progress_id) AS total_courses
                FROM conversaconfig.user_info ui
                JOIN conversaconfig.user_journeys_assigments uja ON ui.user_id = uja.user_id
                JOIN conversaconfig.user_course_progress ucp
                    ON uja.user_journey_id = ucp.user_journey_id
                JOIN conversaconfig.master_courses mc ON ucp.course_id = mc.course_id
                WHERE ui.company_id = $1
                  AND ucp.completed_modules >= mc.course_steps
                  AND mc.course_steps > 0
                GROUP BY uja.user_id
            )
            SELECT
                RANK() OVER (ORDER BY us.puntaje DESC, ucc.total_courses DESC, us.name ASC) AS rank,
                us.user_id, us.name AS "Usuario", us.avatar,
                us.puntaje AS "Puntuacion",
                COALESCE(ucc.total_courses, 0) AS "Cursos"
            FROM user_scores us
            LEFT JOIN user_completed_courses ucc ON us.user_id = ucc.user_id
            ORDER BY rank ASC
            LIMIT 5
        """
        results = await execute_query(query, company_id)
        return [
            {
                "rank": int(row["rank"]),
                "user_id": str(row["user_id"]),
                "Usuario": row["usuario"],
                "avatar": row["avatar"],
                "Puntuacion": int(row["puntuacion"]),
                "Cursos": int(row["cursos"]),
            }
            for row in (results or [])
        ]
    except Exception:
        logger.exception("Error getting leaderboard for company %s", company_id)
        return []


async def get_all_user_conversation_scoring_by_company(company_id: str) -> List[Dict]:
    """Aggregated scoring averages per user in a company."""
    try:
        query = """
            SELECT DISTINCT ON (ui.user_id)
                ui.user_id, ui.name, ui.company_id, ui.user_type, ui.avatar,
                ROUND(AVG(sbc.general_score), 2) AS general_score,
                ROUND(AVG(sbc.fillerwords_scoring), 2)      AS fillerwords_scoring,
                ROUND(AVG(sbc.clarity_scoring), 2)           AS clarity_scoring,
                ROUND(AVG(sbc.participation_scoring), 2)     AS participation_scoring,
                ROUND(AVG(sbc.keythemes_scoring), 2)         AS keythemes_scoring,
                ROUND(AVG(sbc.indexofquestions_scoring), 2)   AS indexofquestions_scoring,
                ROUND(AVG(sbc.rhythm_scoring), 2)            AS rhythm_scoring
            FROM conversaconfig.user_info ui
            LEFT JOIN conversaapp.conversations c
                ON c.user_id = ui.user_id
            LEFT JOIN conversaapp.scoring_by_conversation sbc
                ON c.conversation_id = sbc.conversation_id
                AND c.status = 'FINISHED'
                AND sbc.general_score > 0
            WHERE ui.company_id = $1 AND ui.is_active = true
            GROUP BY ui.user_id
        """
        results = await execute_query(query, company_id)
        return [dict(row) for row in results]
    except Exception:
        logger.exception("Error fetching user scores for company %s", company_id)
        return []


async def get_all_user_conversation_scoring_by_stage_company(
    stage_id: str, company_id: str
) -> List[Dict]:
    """Per-user best scoring for a specific stage within a company."""
    try:
        query = """
            SELECT DISTINCT ON (ui.user_id)
                ui.user_id, ui.name, ui.company_id, ui.user_type, ui.avatar,
                c.stage_id, c.status,
                sbc.general_score, sbc.fillerwords_scoring, sbc.clarity_scoring,
                sbc.participation_scoring, sbc.keythemes_scoring,
                sbc.indexofquestions_scoring, sbc.rhythm_scoring,
                sbc.fillerwords_feedback, sbc.clarity_feedback,
                sbc.participation_feedback, sbc.keythemes_feedback,
                sbc.indexofquestions_feedback, sbc.rhythm_feedback
            FROM conversaconfig.user_info ui
            LEFT JOIN conversaapp.conversations c
                ON c.user_id = ui.user_id
            LEFT JOIN conversaapp.scoring_by_conversation sbc
                ON c.conversation_id = sbc.conversation_id
                AND c.status = 'FINISHED'
                AND c.stage_id = $1
            WHERE ui.company_id = $2 AND ui.is_active = true
            ORDER BY ui.user_id, sbc.general_score DESC NULLS LAST
        """
        results = await execute_query(query, stage_id, company_id)
        return [dict(row) for row in results]
    except Exception:
        logger.exception("Error fetching stage scores for stage=%s company=%s", stage_id, company_id)
        return []


async def get_all_user_conversation_average_scoring_by_stage_company(
    stage_id: str, company_id: str
) -> List[Dict]:
    """Average scoring per user for a stage within a company."""
    try:
        query = """
            SELECT DISTINCT ON (ui.user_id)
                ui.user_id, ui.name, ui.company_id, ui.user_type, ui.avatar,
                c.stage_id, c.status,
                c.general_score, c.fillerwords_scoring, c.clarity_scoring,
                c.participation_scoring, c.keythemes_scoring,
                c.indexofquestions_scoring, c.rhythm_scoring
            FROM conversaconfig.user_info ui
            LEFT JOIN conversaapp.conversations c
                ON c.user_id = ui.user_id
                AND c.status = 'FINISHED'
                AND c.stage_id = $1
            WHERE ui.company_id = $2 AND ui.is_active = true
              AND c.status = 'FINISHED'
            ORDER BY ui.user_id, c.general_score DESC NULLS LAST
        """
        results = await execute_query(query, stage_id, company_id)
        return [dict(row) for row in results]
    except Exception:
        logger.exception("Error fetching avg stage scores for stage=%s company=%s", stage_id, company_id)
        return []


async def get_user_cumulative_average_score(user_id: str, days_back: int = 7) -> List[Dict]:
    """Cumulative daily average score for a user (most recent N days)."""
    try:
        query = """
            WITH all_scores AS (
                SELECT c.end_timestamp::date AS day, sbc.general_score
                FROM conversaapp.conversations c
                JOIN conversaapp.scoring_by_conversation sbc
                    ON c.conversation_id = sbc.conversation_id
                WHERE c.user_id = $1::uuid
                  AND c.status = 'FINISHED'
                  AND c.end_timestamp IS NOT NULL
            ),
            daily AS (
                SELECT day, SUM(general_score) AS sum_score, COUNT(*) AS cnt
                FROM all_scores GROUP BY day
            ),
            cumulative AS (
                SELECT day,
                       SUM(sum_score) OVER (ORDER BY day)
                           / NULLIF(SUM(cnt) OVER (ORDER BY day), 0) AS avg_score
                FROM daily
            )
            SELECT day, COALESCE(ROUND(avg_score, 2), 0) AS average_score
            FROM cumulative
            ORDER BY day DESC
            LIMIT $2
        """
        results = await execute_query(query, user_id, days_back)
        return [dict(row) for row in results]
    except Exception:
        logger.exception("Error fetching cumulative score for user %s", user_id)
        return []


# ---------------------------------------------------------------------------
# Profiling reads
# ---------------------------------------------------------------------------

async def get_all_user_profiling_by_company(company_id: str) -> List[Dict]:
    """Profiling scores for every user in a company."""
    try:
        query = """
            SELECT
                ui.name, ui.user_id, ui.avatar,
                up.empathy_score          AS empathy_scoring,
                up.negotiation_score      AS negotiation_scoring,
                up.prospection_score      AS prospection_scoring,
                up.resilience_score       AS resilience_scoring,
                up.technical_domain_score AS technical_domain_scoring
            FROM conversaConfig.user_info ui
            LEFT JOIN conversascoring.user_profile up ON ui.user_id = up.user_id
            WHERE ui.company_id = $1
        """
        results = await execute_query(query, company_id)
        return [dict(row) for row in results]
    except Exception:
        logger.exception("Error fetching profiling for company %s", company_id)
        return []


async def get_user_profiling(user_id: str) -> Dict:
    """Full profiling snapshot for a single user."""
    try:
        query = """
            SELECT
                ui.name, ui.user_id, ui.avatar,
                up.general_score, up.profile_type,
                up.empathy_score          AS empathy_scoring,
                up.negotiation_score      AS negotiation_scoring,
                up.prospection_score      AS prospection_scoring,
                up.resilience_score       AS resilience_scoring,
                up.technical_domain_score AS technical_domain_scoring,
                up.empathy_feedback, up.negotiation_feedback,
                up.prospection_feedback, up.resilience_feedback,
                up.technical_domain_feedback
            FROM conversaconfig.user_info ui
            LEFT JOIN conversascoring.user_profile up ON ui.user_id = up.user_id
            WHERE ui.user_id = $1
        """
        results = await execute_query(query, user_id)
        return dict(results[0]) if results else {}
    except Exception:
        logger.exception("Error fetching profiling for user %s", user_id)
        return {}


async def get_user_profiling_feedbacks(user_id: str) -> Optional[Dict]:
    """Profiling feedback texts for a user."""
    try:
        query = """
            SELECT
                up.empathy_feedback, up.negotiation_feedback,
                up.prospection_feedback, up.resilience_feedback,
                up.technical_domain_feedback
            FROM conversaconfig.user_info ui
            LEFT JOIN conversascoring.user_profile up ON ui.user_id = up.user_id
            WHERE ui.user_id = $1
        """
        results = await execute_query(query, user_id)
        return dict(results[0]) if results else None
    except Exception:
        logger.exception("Error fetching profiling feedbacks for user %s", user_id)
        return None


# ---------------------------------------------------------------------------
# Company dashboard KPIs
# ---------------------------------------------------------------------------

async def get_company_dashboard_stats(company_id: str) -> Dict[str, Any]:
    """Consolidated KPI row for the company admin dashboard."""
    try:
        query = """
            WITH company_users AS (
                SELECT user_id, name, user_type, avatar
                FROM conversaconfig.user_info
                WHERE company_id = $1
            ),
            company_stats AS (
                SELECT
                    AVG(CASE WHEN c.created_at >= date_trunc('month', CURRENT_DATE)
                             THEN sbc.general_score END) AS current_month_avg,
                    AVG(CASE WHEN c.created_at >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')
                              AND c.created_at < date_trunc('month', CURRENT_DATE)
                             THEN sbc.general_score END) AS prev_month_avg
                FROM conversaapp.conversations c
                JOIN company_users u ON c.user_id = u.user_id
                JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
                WHERE c.status = 'FINISHED'
            ),
            user_historical_stats AS (
                SELECT c.user_id, AVG(sbc.general_score) AS avg_score
                FROM conversaapp.conversations c
                JOIN company_users u ON c.user_id = u.user_id
                JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
                WHERE c.status = 'FINISHED' AND sbc.general_score > 0
                GROUP BY c.user_id
            ),
            current_month_stats AS (
                SELECT c.user_id, AVG(sbc.general_score) AS monthly_avg_score
                FROM conversaapp.conversations c
                JOIN company_users u ON c.user_id = u.user_id
                JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
                WHERE c.created_at >= date_trunc('month', CURRENT_DATE)
                  AND c.status = 'FINISHED' AND sbc.general_score > 0
                GROUP BY c.user_id
            )
            SELECT
                COALESCE(ROUND((SELECT AVG(avg_score) FROM user_historical_stats), 1), 0) AS team_average,
                CASE
                    WHEN cs.prev_month_avg IS NULL OR cs.prev_month_avg = 0 THEN 0
                    ELSE ROUND(((cs.current_month_avg - cs.prev_month_avg) / cs.prev_month_avg) * 100, 1)
                END AS team_average_growth_pct,
                (SELECT COUNT(*) FROM user_historical_stats WHERE avg_score < 50 AND avg_score > 0)
                    AS users_requiring_attention,
                (SELECT json_build_object(
                    'name', u.name, 'role', u.user_type, 'photo', u.avatar,
                    'score', ROUND(cms.monthly_avg_score, 1))
                 FROM current_month_stats cms
                 JOIN company_users u ON cms.user_id = u.user_id
                 ORDER BY cms.monthly_avg_score DESC LIMIT 1
                ) AS top_performer_data
            FROM company_stats cs
        """
        results = await execute_query(query, company_id)
        if not results:
            return {"team_average": 0.0, "users_requiring_attention": 0, "top_performer_data": {}}

        row = dict(results[0])

        # Normalise top_performer_data (may be JSON string or dict)
        raw_tp = row.get("top_performer_data")
        if isinstance(raw_tp, str):
            try:
                row["top_performer_data"] = json.loads(raw_tp)
            except (json.JSONDecodeError, TypeError):
                row["top_performer_data"] = None
        elif not isinstance(raw_tp, dict):
            row["top_performer_data"] = None

        if row.get("team_average") is not None:
            row["team_average"] = float(row["team_average"])
        return row

    except Exception:
        logger.exception("Error fetching KPIs for company %s", company_id)
        return {}


# ---------------------------------------------------------------------------
# User journey / progress
# ---------------------------------------------------------------------------

async def get_user_journey(user_id: str) -> List[Dict]:
    """Grouped journey → courses with per-course progress for a user."""
    try:
        query = """
            SELECT
                uaj.journey_id, jc.course_id, jc.is_mandatory,
                jc.display_order AS course_order,
                mc.name AS course_name,
                mc.course_steps AS total_modules,
                COALESCE(ucp.completed_modules, 0) AS completed_modules,
                COALESCE(ucp.status, 'locked') AS course_status,
                uaj.status AS journey_status
            FROM conversaconfig.user_journeys_assigments uaj
            JOIN conversaconfig.journey_courses jc ON uaj.journey_id = jc.journey_id
            JOIN conversaconfig.master_journeys mj ON uaj.journey_id = mj.journey_id
            JOIN conversaconfig.master_courses mc ON jc.course_id = mc.course_id
            LEFT JOIN conversaconfig.user_course_progress ucp
                ON uaj.user_id = ucp.user_id AND jc.course_id = ucp.course_id
            WHERE uaj.user_id = $1 AND mj.is_active
            ORDER BY jc.display_order
        """
        results = await execute_query(query, user_id)
        if not results:
            return []

        journeys_map: Dict[str, Dict] = {}
        for row in results:
            j_id = str(row["journey_id"])
            if j_id not in journeys_map:
                journeys_map[j_id] = {
                    "journey_id": j_id,
                    "journey_status": row["journey_status"],
                    "courses": [],
                }
            journeys_map[j_id]["courses"].append({
                "course_id": str(row["course_id"]),
                "course_name": row["course_name"],
                "is_mandatory": row["is_mandatory"],
                "course_order": row["course_order"],
                "total_modules": row["total_modules"],
                "completed_modules": row["completed_modules"],
                "course_status": row["course_status"],
            })
        return list(journeys_map.values())

    except Exception:
        logger.exception("Error fetching journey for user %s", user_id)
        return []


async def get_dashboard_stats(user_id: str) -> Optional[Dict[str, Any]]:
    """Individual user dashboard: score, hours, courses completed."""
    try:
        query = """
            WITH stats_conversations AS (
                SELECT
                    COALESCE(ROUND(AVG(sbc.general_score))::int, 0) AS average_score,
                    COALESCE(ROUND(SUM(EXTRACT(EPOCH FROM (c.end_timestamp - c.start_timestamp))) / 3600.0, 1), 0.0)
                        AS total_learning_hours
                FROM conversaapp.conversations c
                JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
                WHERE c.user_id = $1::uuid AND sbc.general_score > 0 AND c.status = 'FINISHED'
            ),
            stats_courses AS (
                SELECT COUNT(ucp.course_progress_id) AS total_completed_courses
                FROM conversaconfig.user_journeys_assigments uja
                JOIN conversaconfig.user_course_progress ucp ON uja.user_journey_id = ucp.user_journey_id
                JOIN conversaconfig.master_courses mc ON ucp.course_id = mc.course_id
                WHERE uja.user_id = $1::uuid
                  AND ucp.completed_modules >= mc.course_steps
                  AND mc.course_steps > 0
            )
            SELECT
                sc.average_score, sc.total_learning_hours,
                stc.total_completed_courses,
                (SELECT profile_type FROM conversascoring.user_profile WHERE user_id = $1::uuid) AS profile_type
            FROM stats_conversations sc
            CROSS JOIN stats_courses stc
        """
        results = await execute_query(query, user_id)
        if not results:
            return {
                "user_id": user_id, "level": "Sin Nivel",
                "average_score": 0, "total_learning_hours": 0.0,
                "total_completed_courses": 0, "profile_type": None,
            }

        row = results[0]
        avg_score = int(row["average_score"])
        return {
            "user_id": user_id,
            "level": _user_level_label(avg_score),
            "average_score": avg_score,
            "total_learning_hours": float(row["total_learning_hours"]),
            "total_completed_courses": int(row["total_completed_courses"]),
            "profile_type": row["profile_type"],
        }
    except Exception:
        logger.exception("Error getting dashboard stats for %s", user_id)
        return None


# ---------------------------------------------------------------------------
# Company announcements
# ---------------------------------------------------------------------------

async def get_company_announcements(company_id: str) -> List[Dict]:
    """Active, non-expired announcements for a company (max 5)."""
    try:
        query = """
            SELECT announcement_id, type, title, message, badge_text, created_at
            FROM conversaconfig.company_announcements
            WHERE company_id = $1
              AND is_active = true
              AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY created_at DESC
            LIMIT 5
        """
        results = await execute_query(query, company_id)
        return [dict(row) for row in results] if results else []
    except Exception:
        logger.exception("Error getting announcements for company %s", company_id)
        return []


# ---------------------------------------------------------------------------
# Analytics – Scoring Tab
# ---------------------------------------------------------------------------

async def get_user_avg_participation(user_id: str) -> Dict[str, Any]:
    """User vs assistant participation balance (by speaking duration)."""
    try:
        query = """
            WITH valid_conversations AS (
                SELECT c.conversation_id,
                       EXTRACT(EPOCH FROM (c.end_timestamp - c.start_timestamp)) AS conv_duration
                FROM conversaapp.conversations c
                JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
                WHERE c.user_id = $1::uuid
                  AND c.start_timestamp IS NOT NULL
                  AND c.end_timestamp IS NOT NULL
            ),
            total_time AS (
                SELECT COALESCE(SUM(conv_duration), 0) AS total_duration FROM valid_conversations
            ),
            user_time AS (
                SELECT COALESCE(SUM(m.duration), 0) AS user_duration
                FROM conversaapp.messages m
                JOIN valid_conversations vc ON m.conversation_id = vc.conversation_id
                WHERE m.role = 'user'
            )
            SELECT t.total_duration, u.user_duration,
                   GREATEST(t.total_duration - u.user_duration, 0) AS assistant_duration
            FROM total_time t CROSS JOIN user_time u
        """
        results = await execute_query(query, user_id)
        if not results or float(results[0]["total_duration"]) == 0:
            return {"user_percentage": 50.0, "client_percentage": 50.0, "balance_status": "Sin datos suficientes"}

        total = float(results[0]["total_duration"])
        user_dur = float(results[0]["user_duration"])
        user_pct = round((user_dur / total) * 100, 1)
        client_pct = round(100.0 - user_pct, 1)

        if 40 <= user_pct <= 60:
            label = "Balance Ideal"
        elif user_pct > 60:
            label = "Hablas demasiado"
        else:
            label = "Escuchas demasiado"

        return {"user_percentage": user_pct, "client_percentage": client_pct, "balance_status": label}
    except Exception:
        logger.exception("Error fetching participation for user %s", user_id)
        return {"user_percentage": 50.0, "client_percentage": 50.0, "balance_status": "Error"}


async def get_user_avg_rhythm(user_id: str) -> Dict[str, Any]:
    """Aggregate words-per-minute for the user's messages."""
    try:
        query = """
            WITH user_messages AS (
                SELECT m.content, m.duration
                FROM conversaapp.messages m
                JOIN conversaapp.conversations c ON m.conversation_id = c.conversation_id
                WHERE c.user_id = $1::uuid AND m.role = 'user'
            )
            SELECT
                COALESCE(SUM(array_length(string_to_array(trim(content), ' '), 1)), 0) AS total_words,
                COALESCE(SUM(duration), 0) AS total_seconds
            FROM user_messages
        """
        results = await execute_query(query, user_id)
        if not results or float(results[0]["total_seconds"]) == 0:
            return {"wpm": 0, "status_label": "Sin datos suficientes"}

        total_words = int(results[0]["total_words"])
        total_seconds = float(results[0]["total_seconds"])
        wpm = int((total_words / total_seconds) * 60)

        if 130 <= wpm <= 150:
            label = "Rango Optimo: 130-150"
        elif wpm > 150:
            label = "Ligeramente Rapido"
        else:
            label = "Ligeramente Lento"

        return {"wpm": wpm, "status_label": label}
    except Exception:
        logger.exception("Error fetching rhythm for user %s", user_id)
        return {"wpm": 0, "status_label": "Error"}


async def get_user_avg_filler_words(user_id: str) -> Dict[str, Any]:
    """Average filler-word score across all conversations."""
    try:
        query = """
            SELECT COALESCE(ROUND(AVG(sbc.fillerwords_scoring)::numeric, 1), 0.0) AS frequency_percentage
            FROM conversaapp.conversations c
            JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
            WHERE c.user_id = $1::uuid
        """
        results = await execute_query(query, user_id)
        if not results or results[0]["frequency_percentage"] is None:
            return {"frequency_percentage": 0.0, "feedback_text": "Sin datos suficientes."}
        return {"frequency_percentage": float(results[0]["frequency_percentage"])}
    except Exception:
        logger.exception("Error fetching filler words for user %s", user_id)
        return {"frequency_percentage": 0.0, "feedback_text": "Error"}


async def get_user_avg_technical_level(user_id: str) -> Dict[str, Any]:
    """Average key-themes score and descriptive label."""
    try:
        query = """
            SELECT COALESCE(ROUND(AVG(sbc.keythemes_scoring)), 0) AS technical_level
            FROM conversaapp.conversations c
            JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
            WHERE c.user_id = $1::uuid
        """
        results = await execute_query(query, user_id)
        if not results:
            return {"score": 0, "level_label": "Basico", "feedback_text": "Sin datos suficientes."}

        score = float(results[0]["technical_level"])
        if score >= 80:
            label, feedback = "Alta", "Dominio preciso de terminologia."
        elif score >= 50:
            label, feedback = "Medio", "Conocimiento adecuado, puedes mejorar detalles."
        else:
            label, feedback = "Basico", "Necesitas repasar los conceptos clave."

        return {"score": score, "level_label": label, "feedback_text": feedback}
    except Exception:
        logger.exception("Error fetching technical level for user %s", user_id)
        return {"score": 0, "level_label": "Basico", "feedback_text": "Error"}


async def get_user_persona_profile(user_id: str) -> Optional[Dict]:
    """The user's sales-persona card (profile type + description)."""
    try:
        query = """
            SELECT pd.*
            FROM conversascoring.user_profile up
            JOIN conversascoring.profile_description pd ON up.profile_type = pd.profile
            WHERE up.user_id = $1::uuid
        """
        results = await execute_query(query, user_id)
        return dict(results[0]) if results else None
    except Exception:
        logger.exception("Error fetching persona profile for user %s", user_id)
        return None


# ---------------------------------------------------------------------------
# Progress mutations
# ---------------------------------------------------------------------------

async def update_module_progress(user_id: str, journey_id: str, course_id: str) -> Dict[str, Any]:
    """Record a module completion and cascade to course / journey status."""
    try:
        context_query = """
            SELECT uaj.user_journey_id, mc.course_steps
            FROM conversaconfig.user_journeys_assigments uaj
            JOIN conversaconfig.master_courses mc ON mc.course_id = $3::uuid
            WHERE uaj.user_id = $1::uuid AND uaj.journey_id = $2::uuid
        """
        context = await execute_query(context_query, user_id, journey_id, course_id)
        if not context:
            return {"success": False, "error": "Assignment or course not found"}

        user_journey_id = context[0]["user_journey_id"]
        total_modules = context[0]["course_steps"]

        upsert = """
            INSERT INTO conversaconfig.user_course_progress
                (user_journey_id, course_id, completed_modules, status, started_at, user_id)
            VALUES ($1::uuid, $2::uuid, 1, 'in_progress', CURRENT_TIMESTAMP, $4::uuid)
            ON CONFLICT (user_journey_id, course_id) DO UPDATE SET
                completed_modules = LEAST(
                    conversaconfig.user_course_progress.completed_modules + 1, $3::int),
                status = CASE
                    WHEN conversaconfig.user_course_progress.completed_modules + 1 >= $3::int
                        THEN 'completed'::varchar ELSE 'in_progress'::varchar END,
                completed_at = CASE
                    WHEN conversaconfig.user_course_progress.completed_modules + 1 >= $3::int
                        THEN CURRENT_TIMESTAMP
                    ELSE conversaconfig.user_course_progress.completed_at END,
                updated_at = CURRENT_TIMESTAMP
            RETURNING completed_modules, status
        """
        progress = await execute_query(upsert, user_journey_id, course_id, total_modules, user_id)
        course_status = progress[0]["status"]

        pending_query = """
            SELECT count(*) AS pending_courses
            FROM conversaconfig.journey_courses jc
            LEFT JOIN conversaconfig.user_course_progress ucp
                ON ucp.course_id = jc.course_id AND ucp.user_journey_id = $1::uuid
            WHERE jc.journey_id = $2::uuid AND jc.is_mandatory = true
              AND (ucp.status IS NULL OR ucp.status != 'completed')
        """
        pending = await execute_query(pending_query, user_journey_id, journey_id)
        new_journey_status = "completed" if pending[0]["pending_courses"] == 0 else "in_progress"

        await execute_query(
            """
            UPDATE conversaconfig.user_journeys_assigments SET
                status = $2::varchar,
                completed_at = CASE WHEN $2::varchar = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_journey_id = $1::uuid RETURNING status
            """,
            user_journey_id,
            new_journey_status,
        )
        return {
            "success": True,
            "course_status": course_status,
            "journey_status": new_journey_status,
            "completed_modules": progress[0]["completed_modules"],
        }
    except Exception:
        logger.exception("Error updating progress for user=%s course=%s", user_id, course_id)
        return {"success": False, "error": "Internal error"}


async def update_user_course_progress(user_id: str, course_id: str) -> Dict[str, Any]:
    """Increment completed_modules by 1 and auto-set status."""
    try:
        query = """
            UPDATE conversaconfig.user_course_progress SET
                completed_modules = completed_modules + 1,
                status = CASE
                    WHEN (completed_modules + 1) >= (
                        SELECT course_steps FROM conversaconfig.master_courses WHERE course_id = $2::uuid
                    ) THEN 'completed'::varchar ELSE 'in_progress'::varchar END,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1::uuid AND course_id = $2::uuid
            RETURNING completed_modules, status
        """
        result = await execute_query(query, user_id, course_id)
        if result:
            return {"success": True, "data": dict(result[0])}
        return {"success": False, "error": "Progress record not found."}
    except Exception:
        logger.exception("Error updating course progress user=%s course=%s", user_id, course_id)
        return {"success": False, "error": "Internal error"}


async def update_user_course_status(user_id: str, course_id: str) -> Dict[str, Any]:
    """Re-evaluate course status based on current completed_modules."""
    try:
        query = """
            UPDATE conversaconfig.user_course_progress p SET
                status = CASE WHEN p.completed_modules >= c.course_steps THEN 'completed' ELSE 'in_progress' END,
                updated_at = CURRENT_TIMESTAMP
            FROM conversaconfig.master_courses c
            WHERE p.user_id = $1::uuid AND p.course_id = $2::uuid AND c.course_id = p.course_id
            RETURNING p.completed_modules, p.status
        """
        result = await execute_query(query, user_id, course_id)
        if result:
            return {"success": True, "data": dict(result[0])}
        return {"success": False, "error": "Progress record not found."}
    except Exception:
        return {"success": False, "error": "Internal error"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_level_label(score: int) -> str:
    if score >= 80:
        return "Level 5: Avanzado"
    elif score >= 60:
        return "Level 3: Intermedio"
    elif score > 0:
        return "Level 1: Principiante"
    return "Sin Nivel"
