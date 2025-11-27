# Course service for retrieving user-specific courses
# Joins master_courses with user_type_relations based on user's type
# Returns courses available to the user's type

from .db import execute_query
from uuid import UUID
from typing import List, Dict

async def get_user_courses(user_id: UUID) -> List[Dict]:
    """
    Get courses available to user based on their user_type
    Joins master_courses with user_type_relations via user's type
    """
    query = """
    SELECT mc.course_id, mc.name, mc.description, mc.image_id, mc.created_on, mc.is_active,
           utr.event_time, utr.metrics
    FROM conversaConfig.master_courses mc
    JOIN conversaConfig.user_type_relations utr ON mc.course_id = utr.course_id
    WHERE utr.user_type = (
      SELECT user_type FROM conversaConfig.user_info WHERE user_id = $1
    )
    """
    
    results = await execute_query(query, user_id)
    return [dict(row) for row in results]

async def get_user_courses_stages(course_id: UUID) -> List[Dict]:
    """
    Get stages available for a course
    """
    query = """
    SELECT
      mc.course_id       AS mc_course_id,
      mc.name            AS mc_name,
      cs.stage_id        AS cs_stage_id,
      cs.stage_name      AS cs_stage_name,
      cs.stage_description AS cs_stage_description
      FROM conversaconfig.master_courses    mc
        LEFT JOIN conversaconfig.course_stages cs ON cs.course_id = mc.course_id
        WHERE mc.course_id = $1 and mc.is_active
        ORDER BY cs.stage_order NULLS LAST;
    """
    
    results = await execute_query(query, course_id)
    return [dict(row) for row in results]

async def get_courses_details(course_id: UUID, stage_id: UUID) -> List[Dict]:
    """
    Get courses details based on course_id and stage_id
    """
    query = """
    SELECT
      mc.course_id       AS mc_course_id,
      mc.name            AS mc_name,
      cs.stage_id        AS cs_stage_id,
      cs.stage_name      AS cs_stage_name,
      cs.stage_description AS cs_stage_description,
      cc.content_id      AS cc_content_id,
      cc.title           AS cc_title,
      cc.body            AS cc_body,
      cc.bot_prompt      AS cc_bot_prompt
      FROM conversaconfig.master_courses    mc
        LEFT JOIN conversaconfig.course_stages cs ON cs.course_id = mc.course_id
        LEFT JOIN conversaconfig.course_contents cc ON cc.course_id = mc.course_id AND cc.stage_id = cs.stage_id
        WHERE mc.course_id = $1 and mc.is_active and cs.stage_id = $2
        ORDER BY cs.stage_order NULLS LAST, cc.position NULLS LAST;
    """
    
    results = await execute_query(query, course_id, stage_id)
    return [dict(row) for row in results]