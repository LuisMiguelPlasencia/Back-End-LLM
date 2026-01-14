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
            ui.company_id = $1 AND ui.is_active = true
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

