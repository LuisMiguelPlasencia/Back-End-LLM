# Course service for retrieving user-specific courses
# Joins master_courses with user_type_relations based on user's type
# Returns courses available to the user's type

from .db import execute_query
from uuid import UUID
from typing import List, Dict

async def get_user_courses(user_id: UUID) -> List[Dict]:
    """
    Retrieves a list of courses for a specific user, nested with their respective stages.
    
    Structure: [  
        {
            "courseid": UUID,
            "Coursename": str,
            "Coursedetails": str,
            "Progress": int,
            "Stages": [ { "stageid": int, "stage_name": str, ... }, ... ]
        }, 
        ...
    ]
    """
    
    # Optimization: Removed JOIN on 'course_contents' to prevent Cartesian product (row duplication).
    # Ordering by course_id first is crucial for efficient grouping.
    query = """
        SELECT 
    mc.course_id,
    mc.name,
    mc.description,
    mc.image_src,
    mc.created_on,
    cs.stage_id,
    cs.stage_name,
    cs.stage_description,
    cs.stage_order,
    CASE 
        WHEN (c.conversation_id IS NOT NULL AND c.status = 'FINISHED') 
        THEN cs.stage_order 
        ELSE 0 
    END AS stage_progress
FROM conversaconfig.master_courses mc
JOIN conversaConfig.user_type_relations utr ON mc.course_id = utr.course_id
LEFT JOIN conversaconfig.course_stages cs ON cs.course_id = mc.course_id
LEFT JOIN (
    SELECT 
        couser_id,
        stage_id,
        status,
        conversation_id,
        ROW_NUMBER() OVER (
            PARTITION BY couser_id, stage_id 
            ORDER BY 
                -- 1. Prioridad: Estado FINISHED primero
                CASE WHEN status = 'FINISHED' THEN 0 ELSE 1 END ASC, 
                -- 2. Prioridad: Fecha más reciente 
                created_at DESC
        ) as rn
    FROM conversaapp.conversations
    WHERE user_id = $1
) c ON c.couser_id = mc.course_id 
   AND c.stage_id = cs.stage_id 
   AND c.rn = 1 
WHERE mc.is_active 
  AND utr.user_type = (SELECT user_type FROM conversaConfig.user_info WHERE user_id = $1)
ORDER BY mc.created_on ASC, cs.stage_order ASC;
    """
    
    results = await execute_query(query, user_id)
    
    courses_map: Dict[str, Dict] = {}

    for row in results:
        c_id = str(row['course_id'])

        # Initialize course in map if not present
        if c_id not in courses_map:
            courses_map[c_id] = {
                "course_id": row['course_id'],
                "name": row['name'],
                "description": row['description'],
                "image_src": row['image_src'],
                "created_on":row['created_on'],
                "progress": 0, # Default value, updated below
                "stages": []
            }

        # Update Course Progress: Keep the highest stage_order completed
        if row['stage_progress'] > courses_map[c_id]["progress"]:
            courses_map[c_id]["progress"] = row['stage_progress']

        # Append Stage if it exists (handling LEFT JOIN nulls)
        if row['stage_id']:
            courses_map[c_id]["stages"].append({
                "stage_id": row['stage_id'],
                "stage_name": row['stage_name'],
                "stage_description": row['stage_description'],
                "stage_order": row['stage_order']
            })

    return list(courses_map.values())



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
      cs.stage_description AS cs_stage_description,
      cc.content_id      AS cc_content_id,
      cc.title           AS cc_title,
      cc.body            AS cc_body,
      cc.bot_prompt      AS cc_bot_prompt
      FROM conversaconfig.master_courses    mc
        LEFT JOIN conversaconfig.course_stages cs ON cs.course_id = mc.course_id
        LEFT JOIN conversaconfig.course_contents cc ON cc.course_id = mc.course_id AND cc.stage_id = cs.stage_id
        WHERE mc.course_id = $1 and mc.is_active
        ORDER BY cs.stage_order NULLS LAST, cc.position NULLS LAST;
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