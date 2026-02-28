# Message service for handling conversation messages
# Manages user messages and generates simple assistant responses
# Note: assistant messages have user_id = NULL (system messages)
import asyncio
import pandas as pd
from .db import execute_query, execute_query_one
from uuid import UUID
from typing import List, Dict, Optional, Tuple

async def get_conversation_transcript(conversation_id: UUID) -> List[Dict]:
    query = """
    SELECT 
        role,
        content,
        created_at,
        duration
    FROM conversaapp.messages 
    WHERE conversation_id = $1
    ORDER BY created_at ASC
    """

    results = await execute_query(query, conversation_id)
    
    role_map = {"user": "vendedor", "assistant": "cliente"}
    
    conversation = [
        {
            "speaker": role_map.get(row["role"], row["role"]),
            "text": row["content"],
            "duracion": float(row["duration"]) if row["duration"] is not None else None
        }
        for row in results
    ]

    return conversation

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
    """
    Recupera el Top 5 de usuarios de una empresa ordenados por Puntuación, 
    desempatando por Cursos completados y nombre.
    """
    try:
        # Tu SQL definitiva
        query = """
            WITH UserScores AS (
                SELECT
                    ui.user_id,
                    ui.name,
                    ui.avatar,
                    COALESCE(ROUND(AVG(sbc.general_score))::int, 0) AS puntaje
                FROM conversaconfig.user_info ui
                JOIN conversaapp.conversations c ON ui.user_id = c.user_id
                JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
                WHERE ui.company_id = $1
                GROUP BY ui.user_id, ui.name, ui.avatar
            ),
            UserCompletedCourses AS (
                SELECT 
                    uja.user_id,
                    COUNT(ucp.course_progress_id) AS total_courses
                FROM conversaconfig.user_info ui
                JOIN conversaconfig.user_journeys_assigments uja ON ui.user_id = uja.user_id
                JOIN conversaconfig.user_course_progress ucp ON uja.user_journey_id = ucp.user_journey_id
                JOIN conversaconfig.master_courses mc ON ucp.course_id = mc.course_id
                WHERE ui.company_id = $1
                  AND ucp.completed_modules >= mc.course_steps 
                  AND mc.course_steps > 0
                GROUP BY uja.user_id
            )
            SELECT
                RANK() OVER (ORDER BY us.puntaje desc, ucc.total_courses desc, us."name" asc) as rank,
                us.user_id,
                us.name as Usuario,
                us.avatar,
                us.puntaje as Puntuacion,
                COALESCE(ucc.total_courses, 0) AS Cursos
            FROM UserScores us
            LEFT JOIN UserCompletedCourses ucc ON us.user_id = ucc.user_id
            ORDER BY rank asc
            LIMIT 5;
        """

        results = await execute_query(query, company_id)
        
        if not results:
            return []
            
        leaderboard = []
        for row in results:
            leaderboard.append({
                "rank": int(row['rank']),
                "user_id": str(row['user_id']),
                "Usuario": row['usuario'],        # Alias de tu SQL
                "avatar": row['avatar'],
                "Puntuacion": int(row['puntuacion']), # Alias de tu SQL
                "Cursos": int(row['cursos'])          # Alias de tu SQL
            })

        return leaderboard

    except Exception as e:
        print(f"Error getting leaderboard for company {company_id}: {str(e)}")
        return None
    
async def get_all_user_conversation_scoring_by_company(company_id: str) -> List[Dict]:
    """Get all user conversation scores for a company, ordered by puntuation"""
    try:
        query = """
            SELECT DISTINCT ON (ui.user_id)
                ui.user_id,
                ui.name,
                ui.company_id,
                ui.user_type,
                ui.avatar,
                ROUND(AVG(sbc.general_score),2) AS general_score,
                ROUND(AVG(sbc.fillerwords_scoring),2) AS fillerwords_scoring,
                ROUND(AVG(sbc.clarity_scoring),2)      AS clarity_scoring,
                ROUND(AVG(sbc.participation_scoring),2)      AS participation_scoring,
                ROUND(AVG(sbc.keythemes_scoring),2)      AS keythemes_scoring,
                ROUND(AVG(sbc.indexofquestions_scoring),2)      AS indexofquestions_scoring,
                ROUND(AVG(sbc.rhythm_scoring),2)       AS rhythm_scoring
            FROM conversaconfig.user_info ui
            LEFT JOIN conversaapp.conversations c
                ON c.user_id = ui.user_id
            LEFT JOIN conversaapp.scoring_by_conversation sbc 
                ON c.conversation_id = sbc.conversation_id
                AND c.status = 'FINISHED'
            WHERE ui.company_id = $1
                AND ui.is_active = true
            GROUP BY ui.user_id;
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
    SELECT user_id, name, user_type, avatar
    FROM conversaconfig.user_info
    WHERE company_id = $1
),
team_monthly_comparison AS (
    
    SELECT 
        AVG(CASE 
            WHEN c.created_at >= date_trunc('month', CURRENT_DATE) 
            THEN sbc.general_score END) as current_month_avg,
        AVG(CASE 
            WHEN c.created_at >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month') 
             AND c.created_at < date_trunc('month', CURRENT_DATE)
            THEN sbc.general_score END) as prev_month_avg
    FROM conversaapp.conversations c
    JOIN company_users u ON c.user_id = u.user_id
    JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
    WHERE c.status = 'FINISHED'
    AND c.created_at >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')
),
user_historical_stats AS (
    SELECT 
        c.user_id,
        AVG(sbc.general_score) as avg_score
    FROM conversaapp.conversations c
    JOIN company_users u ON c.user_id = u.user_id
    JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
    WHERE c.status = 'FINISHED'
    GROUP BY c.user_id
),
current_month_stats AS (
    SELECT 
        c.user_id,
        AVG(sbc.general_score) as monthly_avg_score
    FROM conversaapp.conversations c
    JOIN company_users u ON c.user_id = u.user_id
    JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
    WHERE c.created_at >= date_trunc('month', CURRENT_DATE) AND c.status = 'FINISHED'
    GROUP BY c.user_id
)
SELECT 
    COALESCE(ROUND(tmc.current_month_avg, 1), 0) as team_average,
    CASE 
        WHEN tmc.prev_month_avg IS NULL OR tmc.prev_month_avg = 0 THEN 0 
        ELSE ROUND(((tmc.current_month_avg - tmc.prev_month_avg) / tmc.prev_month_avg) * 100, 1)
    END as team_average_growth_pct,
    (
        SELECT COUNT(*)
        FROM user_historical_stats
        WHERE avg_score < 50
    ) as users_requiring_attention,
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
    ) as top_performer_data
FROM team_monthly_comparison tmc;
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


async def get_user_journey(user_id: str) -> List[Dict[str, Any]]:
    """
    Recupera los journeys asignados al usuario y agrupa los cursos con su 
    progreso detallado (módulos completados vs totales).
    """
    try:
        # Tu SQL definitiva
        query = """
            SELECT 
                uaj.journey_id,
                jc.course_id,
                jc.is_mandatory,
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
                ON uaj.user_journey_id = ucp.user_journey_id 
                AND jc.course_id = ucp.course_id
            WHERE uaj.user_id = $1  AND mj.is_active 
            ORDER BY jc.display_order;
        """

        results = await execute_query(query, user_id)
        
        if not results:
            return []

        journeys_map = {}

        for row in results:
            j_id = str(row['journey_id'])
            
            # 1. Inicializamos el journey si es la primera vez que iteramos sobre él
            if j_id not in journeys_map:
                journeys_map[j_id] = {
                    "journey_id": j_id,
                    "journey_status": row['journey_status'],
                    "courses": []
                }
            
            # 2. Añadimos el curso actual a la lista de cursos del journey
            journeys_map[j_id]["courses"].append({
                "course_id": str(row['course_id']),
                "course_name": row['course_name'],
                "is_mandatory": row['is_mandatory'],
                "course_order": row['course_order'],
                "total_modules": row['total_modules'],
                "completed_modules": row['completed_modules'],
                "course_status": row['course_status']
            })

        # 3. Retornamos solo los valores (la lista de journeys ya agrupada)
        return list(journeys_map.values())

    except Exception as e:
        print(f"Error fetching journey assignments for user {user_id}: {str(e)}")
        return []


async def update_module_progress(user_id: str, journey_id: str, course_id: str) -> Dict[str, Any]:
    """
    Registra que un usuario ha completado un módulo de un curso específico.
    Actualiza el progreso del curso y, si es necesario, el estado global del Journey.
    """
    try:
        # 1. Obtener el user_journey_id y el total de módulos del curso
        # Añadimos ::uuid para asegurar la conversión desde el string de Python
        context_query = """
            SELECT uaj.user_journey_id, mc.course_steps
            FROM conversaconfig.user_journeys_assigments uaj
            JOIN conversaconfig.master_courses mc ON mc.course_id = $3::uuid
            WHERE uaj.user_id = $1::uuid AND uaj.journey_id = $2::uuid;
        """
        context = await execute_query(context_query, user_id, journey_id, course_id)
        
        if not context:
            return {"success": False, "error": "Asignación o curso no encontrado"}
            
        user_journey_id = context[0]['user_journey_id']
        total_modules = context[0]['course_steps']

        # 2. UPSERT: Insertar progreso si es el módulo 1, o sumar +1 si ya existe.
        upsert_query = """
            INSERT INTO conversaconfig.user_course_progress 
                (user_journey_id, course_id, completed_modules, status, started_at)
            VALUES 
                ($1::uuid, $2::uuid, 1, 'in_progress', CURRENT_TIMESTAMP)
            ON CONFLICT (user_journey_id, course_id) 
            DO UPDATE SET 
                completed_modules = LEAST(conversaconfig.user_course_progress.completed_modules + 1, $3::int),
                status = CASE 
                    WHEN conversaconfig.user_course_progress.completed_modules + 1 >= $3::int THEN 'completed'::varchar
                    ELSE 'in_progress'::varchar
                END,
                completed_at = CASE 
                    WHEN conversaconfig.user_course_progress.completed_modules + 1 >= $3::int THEN CURRENT_TIMESTAMP
                    ELSE conversaconfig.user_course_progress.completed_at
                END,
                updated_at = CURRENT_TIMESTAMP
            RETURNING completed_modules, status;
        """
        progress_result = await execute_query(upsert_query, user_journey_id, course_id, total_modules)
        current_course_status = progress_result[0]['status']

        # 3. Verificamos si quedan cursos obligatorios sin terminar
        journey_check_query = """
            SELECT count(*) AS pending_courses
            FROM conversaconfig.journey_courses jc
            LEFT JOIN conversaconfig.user_course_progress ucp 
                ON ucp.course_id = jc.course_id AND ucp.user_journey_id = $1::uuid
            WHERE jc.journey_id = $2::uuid 
              AND jc.is_mandatory = true 
              AND (ucp.status IS NULL OR ucp.status != 'completed');
        """
        check_result = await execute_query(journey_check_query, user_journey_id, journey_id)
        pending_courses = check_result[0]['pending_courses']

        # 4. Actualizar el estado del Journey
        # ¡AQUÍ ESTÁ LA SOLUCIÓN AL ERROR! -> $2::varchar
        new_journey_status = 'completed' if pending_courses == 0 else 'in_progress'
        
        update_journey_query = """
            UPDATE conversaconfig.user_journeys_assigments
            SET 
                status = $2::varchar,
                completed_at = CASE WHEN $2::varchar = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_journey_id = $1::uuid
            RETURNING status;
        """
        await execute_query(update_journey_query, user_journey_id, new_journey_status)

        return {
            "success": True,
            "course_status": current_course_status,
            "journey_status": new_journey_status,
            "completed_modules": progress_result[0]['completed_modules']
        }

    except Exception as e:
        print(f"Error updating progress for user {user_id}, course {course_id}: {str(e)}")
        return {"success": False, "error": str(e)}


from typing import Dict, Any

def get_user_level_label(score: int) -> str:
    """Función auxiliar para determinar el nivel basado en la nota."""
    if score >= 80:
        return "Level 5: Avanzado"
    elif score >= 60:
        return "Level 3: Intermedio"
    elif score > 0:
        return "Level 1: Principiante"
    else:
        return "Sin Nivel"

async def get_dashboard_stats(user_id: str) -> Dict[str, Any]:
    """
    Recupera y calcula las estadísticas del usuario desde la base de datos
    (nota general, horas de aprendizaje y cursos completados).
    """
    try:
        query = """
            WITH stats_conversations AS (
                SELECT
                    COALESCE(ROUND(AVG(sbc.general_score)), 0) AS average_score,
                    COALESCE(ROUND(SUM(EXTRACT(EPOCH FROM (c.end_timestamp - c.start_timestamp))) / 3600.0, 1), 0.0) AS total_learning_hours
                FROM conversaapp.conversations c
                JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
                WHERE c.user_id = $1::uuid
            ),
            stats_courses AS (
                SELECT COUNT(ucp.course_progress_id) AS total_completed_courses
                FROM conversaconfig.user_course_progress ucp
                JOIN conversaconfig.user_journeys_assigments uja ON ucp.user_journey_id = uja.user_journey_id
                JOIN conversaconfig.master_courses mc ON ucp.course_id = mc.course_id
                WHERE uja.user_id = $1::uuid
                  AND ucp.completed_modules >= mc.course_steps
                  AND mc.course_steps > 0
            )
            SELECT 
                sc.average_score,
                sc.total_learning_hours,
                stc.total_completed_courses
            FROM stats_conversations sc
            CROSS JOIN stats_courses stc;
        """

        results = await execute_query(query, user_id)
        
        # Si el usuario es nuevo y no tiene historial
        if not results:
            return {
                "user_id": user_id,
                "level": "Sin Nivel",
                "average_score": 0,
                "total_learning_hours": 0.0,
                "total_completed_courses": 0
            }
            
        row = results[0]
        avg_score = int(row['average_score'])
        
        # Devolvemos el diccionario formateado
        return {
            "user_id": user_id,
            "level": get_user_level_label(avg_score),
            "average_score": avg_score,
            "total_learning_hours": float(row['total_learning_hours']),
            "total_completed_courses": int(row['total_completed_courses'])
        }

    except Exception as e:
        print(f"Error getting dashboard stats for {user_id}: {str(e)}")
        # Retornamos None para que el router sepa que hubo un fallo
        return None



async def get_company_announcements(company_id: str) -> List[Dict[str, Any]]:
    """
    Recupera las noticias (announcements) activas y no caducadas para una empresa,
    ordenadas de más recientes a más antiguas.
    """
    try:
        query = """
            SELECT 
                announcement_id,
                type,
                title,
                message,
                badge_text,
                created_at
            FROM conversaconfig.company_announcements
            WHERE company_id = $1
              AND is_active = true
              -- Filtro de caducidad: Si es NULL es permanente, si tiene fecha debe ser futura
              AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY created_at DESC
            LIMIT 5; -- Traemos solo las 5 más recientes para no saturar la UI
        """

        results = await execute_query(query, company_id)
        
        if not results:
            return []

        return results

    except Exception as e:
        print(f"Error getting announcements for company {company_id}: {str(e)}")
        return None


from typing import Dict, Any

async def get_user_avg_participation(user_id: str) -> Dict[str, Any]:
    """
    Calcula el balance de participación real sumando la duración de los 
    mensajes del usuario y restándoselo a la duración total de sus conversaciones.
    """
    try:
        query = """
            WITH valid_conversations AS (
                -- 1. Aislamos las conversaciones completadas y calculamos la duración de cada una en segundos
                SELECT 
                    c.conversation_id,
                    EXTRACT(EPOCH FROM (c.end_timestamp - c.start_timestamp)) AS conv_duration
                FROM conversaapp.conversations c
                JOIN conversaapp.scoring_by_conversation sbc ON c.conversation_id = sbc.conversation_id
                WHERE c.user_id = $1::uuid 
                  --AND sbc.is_accomplished = true
                  AND c.start_timestamp IS NOT NULL
                  AND c.end_timestamp IS NOT NULL
            ),
            total_time AS (
                -- 2. Sumamos todo el tiempo que el usuario ha estado en conversaciones
                SELECT COALESCE(SUM(conv_duration), 0) AS total_duration
                FROM valid_conversations
            ),
            user_time AS (
                -- 3. Sumamos la duración específica de los mensajes donde el rol es 'user'
                SELECT COALESCE(SUM(m.duration), 0) AS user_duration
                FROM conversaapp.messages m
                JOIN valid_conversations vc ON m.conversation_id = vc.conversation_id
                WHERE m.role = 'user'
            )
            -- 4. Juntamos los datos y calculamos por diferencia el tiempo del asistente
            SELECT 
                t.total_duration,
                u.user_duration,
                -- Usamos GREATEST por seguridad, para evitar tiempos negativos si hay algún desfase de milisegundos
                GREATEST(t.total_duration - u.user_duration, 0) AS assistant_duration
            FROM total_time t
            CROSS JOIN user_time u;
        """
        
        results = await execute_query(query, user_id)
        
        # Si no hay resultados o la duración total es 0 (no ha completado nada aún)
        if not results or float(results[0]['total_duration']) == 0:
            return {
                "user_percentage": 50.0,
                "client_percentage": 50.0,
                "balance_status": "Sin datos suficientes"
            }
            
        row = results[0]
        total_duration = float(row['total_duration'])
        user_duration = float(row['user_duration'])
        
        # Calculamos los porcentajes reales
        user_pct = round((user_duration / total_duration) * 100, 1)
        # El cliente es simplemente el resto hasta 100
        client_pct = round(100.0 - user_pct, 1) 
        
        # Lógica de feedback basada en el porcentaje del usuario
        if 40 <= user_pct <= 60:
            balance_status = "Balance Ideal"
        elif user_pct > 60:
            balance_status = "Hablas demasiado"
        else:
            balance_status = "Escuchas demasiado"

        return {
            "user_percentage": user_pct,
            "client_percentage": client_pct,
            "balance_status": balance_status
        }

    except Exception as e:
        print(f"Error fetching participation metrics for user {user_id}: {str(e)}")
        return None



async def get_user_avg_rhythm(user_id: str) -> Dict[str, Any]:
    """
    Calcula las Palabras por Minuto (WPM) agregadas del usuario contando 
    el total de sus palabras y dividiéndolo entre su tiempo de habla real.
    """
    try:
        query = """
            WITH user_messages AS (
                SELECT 
                    m.content,
                    m.duration
                FROM conversaapp.messages m
                JOIN conversaapp.conversations c ON m.conversation_id = c.conversation_id
                WHERE c.user_id = $1::uuid 
                  AND m.role = 'user'
                  -- AND c.status = 'completed' -- Descomenta esto si solo quieres contar las terminadas
            )
            SELECT 
                -- Truco SQL: limpiamos espacios extra, cortamos por espacios y contamos el tamaño del array
                COALESCE(SUM(array_length(string_to_array(trim(content), ' '), 1)), 0) as total_words,
                
                -- Sumamos la duración exacta de sus audios/mensajes
                COALESCE(SUM(duration), 0) as total_seconds
            FROM user_messages;
        """
        
        results = await execute_query(query, user_id)
        
        
        if not results or float(results[0]['total_seconds']) == 0:
            return {"wpm": 0, "status_label": "Sin datos suficientes"}
            
        total_words = int(results[0]['total_words'])
        total_seconds = float(results[0]['total_seconds'])
        
        
        wpm = int((total_words / total_seconds) * 60)
        
        
        if 130 <= wpm <= 150:
            status_label = "Rango Óptimo: 130-150"
        elif wpm > 150:
            status_label = "Ligeramente Rápido"
        else:
            status_label = "Ligeramente Lento"

        return {"wpm": wpm, "status_label": status_label}

    except Exception as e:
        print(f"Error fetching rhythm metrics for user {user_id}: {str(e)}")
        return None