# Conversation service for managing user conversations
# Handles conversation creation and retrieval from conversaApp.conversations
# Note: course_id is accepted in payload but not stored (no field in table)

from tokenize import String
from .db import execute_query, execute_query_one
from uuid import UUID
from typing import List, Dict, Optional

async def get_conversation_details(conversation_id: UUID) -> Optional[Dict]:
    """Get conversation details for a conversation ID"""
    query = """
    SELECT c.conversation_id, c.start_timestamp, c.end_timestamp, c.status, c.created_at
    , c.updated_at, c.course_id, sbc.general_score, sbc.fillerwords_scoring, sbc.clarity_scoring
    , sbc.participation_scoring, sbc.keythemes_scoring, sbc.indexofquestions_scoring
    , sbc.rhythm_scoring, sbc.fillerwords_feedback, sbc.clarity_feedback, sbc.participation_feedback
    , sbc.keythemes_feedback, sbc.indexofquestions_feedback, sbc.rhythm_feedback, sbc.is_accomplished
    FROM conversaApp.conversations c
    LEFT JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
    WHERE c.conversation_id = $1
    ORDER BY start_timestamp DESC
    """
    
    results = await execute_query(query, conversation_id)
    return [dict(row) for row in results]


async def get_user_conversations(user_id: UUID) -> List[Dict]:
    """Get all conversations for a user, ordered by start time (newest first)"""
    query = """
    SELECT 
        c.conversation_id, c.start_timestamp, c.end_timestamp, c.status, c.created_at, 
        c.updated_at, c.course_id, 
        mc.name,
        mc.image_src,
        sbc.general_score,
        sbc.fillerwords_scoring, 
        sbc.clarity_scoring, 
        sbc.participation_scoring, 
        sbc.keythemes_scoring, 
        sbc.indexofquestions_scoring, 
        sbc.rhythm_scoring, 
        c.fillerwords_feedback, 
        sbc.clarity_feedback, 
        sbc.participation_feedback, 
        sbc.keythemes_feedback, 
        sbc.indexofquestions_feedback, 
        sbc.rhythm_feedback,
        sbc.is_accomplished,
        m.message_count
    FROM conversaApp.conversations c
    left join conversaconfig.master_courses mc 
    on c.course_id = mc.course_id 
    LEFT JOIN (
        SELECT conversation_id, COUNT(*) AS message_count
        FROM conversaapp.messages
        GROUP BY conversation_id
    ) m ON c.conversation_id = m.conversation_id
    LEFT JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
    WHERE user_id = $1
    ORDER BY start_timestamp DESC
    LIMIT 10
    """
    
    results = await execute_query(query, user_id)
    return [dict(row) for row in results]



async def get_user_profiling_by_conversations(user_id: UUID) -> List[Dict]:
    """Get last 10 conversations for a user, ordered by start time (newest first)"""
    query = """
    SELECT 
        pbc.empathy_scoring, 
        pbc.prospection_scoring, 
        pbc.resilience_scoring, 
        pbc.technical_domain_scoring,
        pbc.negotiation_scoring, 
        pbc.empathy_feedback, 
        pbc.prospection_feedback, 
        pbc.resilience_feedback, 
        pbc.technical_domain_feedback, 
        pbc.negotiation_feedback
    FROM conversaApp.conversations c
    left join conversaconfig.master_courses mc 
    on c.course_id = mc.course_id 
    LEFT JOIN (
        SELECT conversation_id, COUNT(*) AS message_count
        FROM conversaapp.messages
        GROUP BY conversation_id
    ) m ON c.conversation_id = m.conversation_id
    LEFT JOIN conversaapp.profiling_by_conversation pbc ON c.conversation_id = pbc.conversation_id
    WHERE user_id = $1
    and pbc.prospection_scoring IS NOT NULL
    and pbc.empathy_scoring IS NOT NULL
    and pbc.resilience_scoring IS NOT NULL
    and pbc.technical_domain_scoring IS NOT NULL
    and pbc.negotiation_scoring IS NOT NULL
    and pbc.prospection_feedback IS NOT NULL
    and pbc.empathy_feedback IS NOT NULL
    and pbc.resilience_feedback IS NOT NULL
    and pbc.technical_domain_feedback IS NOT NULL
    and pbc.negotiation_feedback IS NOT NULL
    ORDER BY start_timestamp DESC
    LIMIT 10
    """
    try:
        results = await execute_query(query, user_id)

        if not results:
            return {}

        # initialize dictionary with empty lists
        output = {key: [] for key in results[0].keys()}

        # fill lists
        for row in results:
            for key, value in row.items():
                output[key].append(value)

        return output

    except Exception as e:
        print(f"Error fetching user profiling scores for user id {user_id}: {str(e)}")
        return {}
    # try:
    #     results = await execute_query(query, user_id)
    #     return dict(results) if len(results) > 0 else None
    # except Exception as e:
    #     print(f"Error fetching user profiling scores for user id {user_id}: {str(e)}")
    #     return None


async def get_voice_agent(stage_id: UUID) -> Optional[Dict]:
    """Get voice and agent from the stage of the course"""
    query = """
    SELECT voice_id, agent_id
    FROM conversaconfig.course_stages WHERE stage_id = $1
    """
    result = await execute_query(query, stage_id)
    
    return result[0] if result else None

async def create_conversation(user_id: UUID, course_id: UUID, stage_id: UUID) -> Optional[Dict]:
    """
    Create new conversation for user
    Note: course_id accepted for compatibility but not stored in DB
    """
    query = """
    INSERT INTO conversaApp.conversations (user_id, course_id, stage_id, conversation_id, start_timestamp, status, created_at, updated_at)
    VALUES ($1,$2,$3, gen_random_uuid(), now(), 'OPEN', now(), now())
    RETURNING conversation_id, user_id, course_id, stage_id, start_timestamp, status, created_at
    """
    
    result = await execute_query_one(query, user_id, course_id, stage_id)
    
    if result:
        return dict(result)
    return None

async def close_conversation(user_id: UUID, conversation_id: UUID, conversation_id_elevenlabs: str, agent_id: str) -> Optional[Dict]:
    """
    Close conversation
    """
    query = """
    UPDATE conversaApp.conversations SET status = 'FINISHED', end_timestamp = now(), conversation_id_elevenlabs = $3, agent_id = $4
    WHERE user_id = $1 AND conversation_id = $2
    """
    await execute_query(query, user_id, conversation_id, conversation_id_elevenlabs, agent_id)
    return True

async def get_conversation_status(conversation_id: UUID, user_id: UUID) -> Optional[str]:
    print('Gettin conver status')
    query = """
    SELECT status FROM conversaApp.conversations WHERE conversation_id = $1 AND user_id = $2
    """
    row = await execute_query_one(query, conversation_id, user_id)
    if not row:
        return None
    return row["status"]

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
    conv_id: UUID) -> Optional[str]:
    print('Setting conversation scoring')
    query = """
    INSERT INTO conversaapp.scoring_by_conversation
    (scoring_id, conversation_id, fillerwords_scoring, clarity_scoring, participation_scoring
    , keythemes_scoring, indexofquestions_scoring, rhythm_scoring, fillerwords_feedback
    , clarity_feedback, indexofquestions_feedback, participation_feedback, keythemes_feedback,
     rhythm_feedback, general_score, is_accomplished)
    VALUES (gen_random_uuid(), $15,$1, $2, $3, $4, $5, $6, $7, $8, $11, $9, $10,  $12, $13, $14)
    """
    row = await execute_query_one(
        query,
        fillerwords_scoring,
        clarity_scoring,
        participation_scoring,
        keythemes_scoring,
        indexofquestions_scoring,
        rhythm_scoring,
        fillerwords_feedback,
        clarity_feedback,
        participation_feedback,
        keythemes_feedback,
        indexofquestions_feedback,
        rhythm_feedback,
        puntuacion_global,
        objetivo,
        conv_id,  # UUID ok
    )

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
    conv_id: UUID) -> Optional[str]:
    print('Setting conversation profiling')
    query = """
    INSERT INTO conversaapp.profiling_by_conversation
    (profiling_id, conversation_id, prospection_scoring, empathy_scoring, technical_domain_scoring
    , negotiation_scoring, resilience_scoring, prospection_feedback, empathy_feedback, technical_domain_feedback
    , negotiation_feedback, resilience_feedback)
    VALUES (gen_random_uuid(), $11,$1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """
    row = await execute_query_one(
        query,
        prospection_scoring,
        empathy_scoring,
        technical_domain_scoring,
        negotiation_scoring,
        resilience_scoring,
        prospection_feedback,
        empathy_feedback,
        technical_domain_feedback,
        negotiation_feedback,
        resilience_feedback,
        conv_id,  # UUID ok
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
    user_id: UUID) -> Optional[str]:
    print('Setting general profiling')
    query = """
    INSERT INTO conversascoring.user_profile
    (prospection_score, empathy_score, technical_domain_score, negotiation_score, resilience_score, prospection_feedback, empathy_feedback, technical_domain_feedback, negotiation_feedback, resilience_feedback, user_id, event_timestamp)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
    ON CONFLICT (user_id) 
    DO UPDATE SET
        event_timestamp = NOW(),
        prospection_score = EXCLUDED.prospection_score,
        empathy_score = EXCLUDED.empathy_score,
        technical_domain_score = EXCLUDED.technical_domain_score,
        negotiation_score = EXCLUDED.negotiation_score,
        resilience_score = EXCLUDED.resilience_score,
        prospection_feedback = EXCLUDED.prospection_feedback,
        empathy_feedback = EXCLUDED.empathy_feedback,
        technical_domain_feedback = EXCLUDED.technical_domain_feedback,
        negotiation_feedback = EXCLUDED.negotiation_feedback,
        resilience_feedback = EXCLUDED.resilience_feedback;
    """
    print("setting general profiling for user_id:", user_id)
    row = await execute_query_one(
        query,
        prospection_scoring,
        empathy_scoring,
        technical_domain_scoring,
        negotiation_scoring,
        resilience_scoring,
        prospection_feedback,
        empathy_feedback,
        technical_domain_feedback,
        negotiation_feedback,
        resilience_feedback,
        user_id,  # UUID ok
    )
    print("general profiling was set successfully for user_id:", user_id)

async def set_user_profile(
    user_id: UUID, 
    general_score: float,  
    profile_type: str
) -> Optional[str]:
    print(f'Setting user profile for user {user_id}')
    
    query = """
    INSERT INTO conversascoring.user_profile
    (user_id, event_timestamp, general_score, profile_type)
    VALUES ($1, NOW(), $2, $3)
    ON CONFLICT (user_id) 
    DO UPDATE SET
        event_timestamp = NOW(),
        general_score = EXCLUDED.general_score,
        profile_type = EXCLUDED.profile_type;
    """

    row = await execute_query_one(
        query,
        user_id,
        general_score,
        profile_type
    )
