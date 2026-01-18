# Message service for handling conversation messages
# Manages user messages and generates simple assistant responses
# Note: assistant messages have user_id = NULL (system messages)

from .db import execute_query, execute_query_one
from uuid import UUID
from typing import List, Dict, Optional, Tuple


async def get_conversation_messages(conversation_id: UUID) -> List[Dict]:
    """Get all messages for a conversation, ordered by creation time"""
    query = """
    SELECT id, user_id, conversation_id, role, content, created_at, duration
    FROM conversaApp.messages
    WHERE conversation_id = $1
    ORDER BY created_at ASC
    """
    
    results = await execute_query(query, conversation_id)
    return [dict(row) for row in results]

async def send_message(user_id: UUID, conversation_id: UUID, message: str, role: str, duration: float) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Send user message and generate assistant response
    Returns tuple of (user_message, assistant_response)
    """
    # Insert user message
    user_query = """
    INSERT INTO conversaApp.messages (id, user_id, conversation_id, role, content, created_at, duration)
    VALUES (gen_random_uuid(), $1, $2, $4, $3, now(), $5)
    RETURNING id, user_id, conversation_id, role, content, created_at, duration
    """
    
    user_message = await execute_query_one(user_query, user_id, conversation_id, message, role, duration)
    
    if not user_message:
        return None, None
    
    return dict(user_message) if user_message else None

async def get_all_user_scoring_by_company(company_id: str) -> List[Dict]:
    """Get all user scores for a company, ordered by puntuation"""
    try:
        query = """
        SELECT 
            ui.user_id,
            ui.name,
            ui.company_id,
            ui.user_type,
            ui.avatar,
            COALESCE(AVG(sbc.general_score), 0) AS score
        FROM 
            conversaconfig.user_info ui
            LEFT JOIN conversaapp.conversations c
                ON c.user_id = ui.user_id and c.status = 'FINISHED'
            LEFT JOIN conversaapp.scoring_by_conversation sbc 
                ON c.conversation_id = sbc.conversation_id
        WHERE 
            ui.company_id = $1 AND ui.is_active = true AND sbc.general_score > 0
        GROUP BY 
            ui.user_id, ui.name, ui.company_id, ui.user_type, ui.avatar
        ORDER BY 
            score DESC
        LIMIT 5
        """

        results = await execute_query(query, company_id)
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error fetching user scores for company_id {company_id}: {str(e)}")
        return []
    
async def get_all_user_conversation_scoring_by_stage_company(stage_id: str, company_id: str) -> List[Dict]:
    """Get all user conversation scores for a stage and company, ordered by puntuation"""
    try:
        query = """
            SELECT DISTINCT ON (ui.user_id)
                ui.user_id,
                ui.name,
                ui.company_id,
                ui.user_type,
                ui.avatar,
                c.stage_id,
                c.status,
                sbc.general_score,
                sbc.fillerwords_scoring,
                sbc.clarity_scoring,
                sbc.participation_scoring,
                sbc.keythemes_scoring,
                sbc.indexofquestions_scoring,
                sbc.rhythm_scoring,
                sbc.fillerwords_feedback,
                sbc.clarity_feedback,
                sbc.participation_feedback,
                sbc.keythemes_feedback,
                sbc.indexofquestions_feedback,
                sbc.rhythm_feedback
            FROM conversaconfig.user_info ui
            LEFT JOIN conversaapp.conversations c
                ON c.user_id = ui.user_id
            LEFT JOIN conversaapp.scoring_by_conversation sbc 
                ON c.conversation_id = sbc.conversation_id
            AND c.status = 'FINISHED'
            AND c.stage_id = $1
            WHERE ui.company_id = $2
            AND ui.is_active = true
            ORDER BY ui.user_id, sbc.general_score DESC NULLS LAST;
        """

        results = await execute_query(query, stage_id, company_id)
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error fetching user scores for stage_id {stage_id} and company_id {company_id}: {str(e)}")
        return []

async def get_all_user_conversation_average_scoring_by_stage_company(stage_id: str, company_id: str) -> List[Dict]:
    """Get all user conversation average scores for a stage and company, ordered by average score"""
    try:
        query = """
            SELECT DISTINCT ON (ui.user_id)
                ui.user_id,
                ui.name,
                ui.company_id,
                ui.user_type,
                ui.avatar,
                c.stage_id,
                c.status,
                c.general_score,
                c.fillerwords_scoring,
                c.clarity_scoring,
                c.participation_scoring,
                c.keythemes_scoring,
                c.indexofquestions_scoring,
                c.rhythm_scoring
            FROM conversaconfig.user_info ui
            LEFT JOIN conversaapp.conversations c
                ON c.user_id = ui.user_id
            AND c.status = 'FINISHED'
            AND c.stage_id = $1
            WHERE ui.company_id = $2
            AND ui.is_active = true
            AND c.status = 'FINISHED'
            ORDER BY ui.user_id, c.general_score DESC NULLS LAST;
        """

        results = await execute_query(query, stage_id, company_id)
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error fetching user scores for stage_id {stage_id} and company_id {company_id}: {str(e)}")
        return []

async def get_all_user_profiling_by_company(company_id: str) -> List[Dict]:
    """Get all user profiling scores for a company"""
    try:
        query = """
            SELECT
                ui."name",
                ui.user_id,
                ROUND(AVG(pbc.empathy_scoring),2)          AS empathy_scoring,
                ROUND(AVG(pbc.negotiation_scoring),2)      AS negotiation_scoring,
                ROUND(AVG(pbc.prospection_scoring),2)      AS prospection_scoring,
                ROUND(AVG(pbc.resilience_scoring),2)       AS resilience_scoring,
                ROUND(AVG(pbc.technical_domain_scoring),2) AS technical_domain_scoring
            FROM conversaConfig.user_info ui
            LEFT JOIN conversaApp.conversations c
                ON ui.user_id = c.user_id
            LEFT JOIN conversaApp.profiling_by_conversation pbc
                ON c.conversation_id = pbc.conversation_id
            WHERE ui.company_id = $1
                AND c.status = 'FINISHED'
            GROUP BY ui.user_id;
        """

        results = await execute_query(query, company_id)
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error fetching user profiling scores for company_id {company_id}: {str(e)}")
        return []
    
async def get_user_profiling(user_id: str) -> Dict:
    """Get all user profiling scores for a company"""
    try:
        query = """
            SELECT
                ui."name",
                ui.user_id,
                up.general_score,
                up.profile_type,
                ROUND(AVG(pbc.empathy_scoring),2)          AS empathy_scoring,
                ROUND(AVG(pbc.negotiation_scoring),2)      AS negotiation_scoring,
                ROUND(AVG(pbc.prospection_scoring),2)      AS prospection_scoring,
                ROUND(AVG(pbc.resilience_scoring),2)       AS resilience_scoring,
                ROUND(AVG(pbc.technical_domain_scoring),2) AS technical_domain_scoring
            FROM conversaConfig.user_info ui
            left join conversascoring.user_profile up 
                on ui.user_id = up.user_id 
            LEFT JOIN conversaApp.conversations c
                ON ui.user_id = c.user_id
            LEFT JOIN conversaApp.profiling_by_conversation pbc
                ON c.conversation_id = pbc.conversation_id
            WHERE ui.user_id = $1
                AND c.status = 'FINISHED'
            GROUP BY ui.user_id, up.general_score, up.profile_type;
        """

        results = await execute_query(query, user_id)
        return dict(results[0] if len(results) > 0 else {} )
    except Exception as e:
        print(f"Error fetching user profiling scores for user id {user_id}: {str(e)}")
        return []

import json
from typing import List, Dict, Any

async def get_company_dashboard_stats(company_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves consolidated KPIs for the company dashboard.
    Handles JSON parsing for top_performer_data manually in Python.
    """
    try:
        query = """
        WITH company_users AS (
            -- Filter users by company first
            SELECT user_id, name, user_type, avatar
            FROM conversaconfig.user_info
            WHERE company_id = $1
        ),
        user_historical_stats AS (
            -- Calculate average per user (historical)
            SELECT 
                c.user_id,
                AVG(c.general_score) as avg_score
            FROM conversaapp.conversations c
            JOIN company_users u ON c.user_id = u.user_id
            WHERE c.status = 'FINISHED'
            GROUP BY c.user_id
        ),
        current_month_stats AS (
            -- Calculate top performer (current month only)
            SELECT 
                c.user_id,
                AVG(c.general_score) as monthly_avg_score
            FROM conversaapp.conversations c
            JOIN company_users u ON c.user_id = u.user_id
            WHERE c.created_at >= date_trunc('month', CURRENT_DATE)
            GROUP BY c.user_id
        )
        SELECT 
            -- KPI 1: Team Average
            (
                SELECT COALESCE(ROUND(AVG(c.general_score), 1), 0)
                FROM conversaapp.conversations c
                JOIN company_users u ON c.user_id = u.user_id
            ) as team_average,

            -- KPI 2: Attention Required
            (
                SELECT COUNT(*)
                FROM user_historical_stats
                WHERE avg_score < 50
            ) as users_requiring_attention,

            -- KPI 3: Top Performer (Raw JSON from DB)
            (
                SELECT json_build_object(
                    'name', u.name,
                    'role', u.user_type,
                    'photo', u.avatar,
                    'score', ROUND(cms.monthly_avg_score, 1)
                )
                FROM current_month_stats cms
                JOIN company_users u ON cms.user_id = u.user_id
                ORDER BY cms.monthly_avg_score DESC
                LIMIT 1
            ) as top_performer_data;
        """

        results = await execute_query(query, company_id)
        if not results:
            return {
                "team_average": 0.0,
                "users_requiring_attention": 0,
                "top_performer_data": None
            }

        row = dict(results[0])
        raw_top_performer = row.get('top_performer_data')
        clean_top_performer = None

        if raw_top_performer:
            if isinstance(raw_top_performer, str):
                try:
                    clean_top_performer = json.loads(raw_top_performer)
                except json.JSONDecodeError:
                    clean_top_performer = None 
            elif isinstance(raw_top_performer, dict):
                clean_top_performer = raw_top_performer
        
        row['top_performer_data'] = clean_top_performer
        if row.get('team_average') is not None:
            row['team_average'] = float(row['team_average'])
        return row

    except Exception as e:
        print(f"Error fetching KPIs for company_id {company_id}: {str(e)}")
        return []