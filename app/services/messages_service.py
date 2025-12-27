# Message service for handling conversation messages
# Manages user messages and generates simple assistant responses
# Note: assistant messages have user_id = NULL (system messages)

from .db import execute_query, execute_query_one
from uuid import UUID
from typing import List, Dict, Optional, Tuple

async def get_conversation_messages(conversation_id: UUID) -> List[Dict]:
    """Get all messages for a conversation, ordered by creation time"""
    query = """
    SELECT id, user_id, conversation_id, role, content, created_at
    FROM conversaApp.messages
    WHERE conversation_id = $1
    ORDER BY created_at ASC
    """
    
    results = await execute_query(query, conversation_id)
    return [dict(row) for row in results]

async def send_message(user_id: UUID, conversation_id: UUID, message: str, role: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Send user message and generate assistant response
    Returns tuple of (user_message, assistant_response)
    """
    # Insert user message
    user_query = """
    INSERT INTO conversaApp.messages (id, user_id, conversation_id, role, content, created_at)
    VALUES (gen_random_uuid(), $1, $2, $4, $3, now())
    RETURNING id, user_id, conversation_id, role, content, created_at
    """
    
    user_message = await execute_query_one(user_query, user_id, conversation_id, message, role)
    
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
            COALESCE(AVG(c.general_score), 0) AS score
        FROM 
            conversaconfig.user_info ui
            LEFT JOIN conversaapp.conversations c
                ON c.user_id = ui.user_id and c.status = 'FINISHED'
        WHERE 
            ui.company_id = $1 AND ui.is_active = true
        GROUP BY 
            ui.user_id, ui.name, ui.company_id, ui.user_type, ui.avatar
        ORDER BY 
            score DESC
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
                c.general_score,
                c.fillerwords_scoring,
                c.clarity_scoring,
                c.participation_scoring,
                c.keythemes_scoring,
                c.indexofquestions_scoring,
                c.rhythm_scoring,
                c.fillerwords_feedback,
                c.clarity_feedback,
                c.participation_feedback,
                c.keythemes_feedback,
                c.indexofquestions_feedback,
                c.rhythm_feedback
            FROM conversaconfig.user_info ui
            LEFT JOIN conversaapp.conversations c
                ON c.user_id = ui.user_id
            AND c.status = 'FINISHED'
            AND c.stage_id = $1
            WHERE ui.company_id = $2
            AND ui.is_active = true
            ORDER BY ui.user_id, c.general_score DESC NULLS LAST;
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
