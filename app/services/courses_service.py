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
