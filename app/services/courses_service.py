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

async def get_courses_details(course_id: UUID) -> List[Dict]:
    """
    Get courses details based on course_id
    """
    query = """
    SELECT
  mc.course_id       AS mc_course_id,
  mc.name            AS mc_name,
  mc.description     AS mc_description,
  mc.image_id        AS mc_image_id,
  mc.created_on      AS mc_created_on,
  mc.updated_at      AS mc_updated_at,
  mc.is_active       AS mc_is_active,
  cs.stage_id        AS cs_stage_id,
  cs.course_id       AS cs_course_id,
  cs.stage_order     AS cs_stage_order,
  cs.stage_name      AS cs_stage_name,
  cs.stage_description AS cs_stage_description,
  cs.created_on      AS cs_created_on,
  cs.updated_at      AS cs_updated_at,
  cc.content_id      AS cc_content_id,
  cc.course_id       AS cc_course_id,
  cc.stage_id        AS cc_stage_id,
  cc.position        AS cc_position,
  cc.title           AS cc_title,
  cc.body            AS cc_body,
  cc.resource_url    AS cc_resource_url,
  cc.created_on      AS cc_created_on,
  cc.updated_at      AS cc_updated_at,
  cc.bot_prompt      AS cc_bot_prompt
FROM conversaconfig.master_courses    mc
LEFT JOIN conversaconfig.course_stages cs ON cs.course_id = mc.course_id
LEFT JOIN conversaconfig.course_contents cc ON cc.course_id = mc.course_id AND cc.stage_id = cs.stage_id
WHERE mc.course_id = $1 and mc.is_active 
ORDER BY cs.stage_order NULLS LAST, cc.position NULLS LAST;
    """
    
    results = await execute_query(query, course_id)
    return [dict(row) for row in results]