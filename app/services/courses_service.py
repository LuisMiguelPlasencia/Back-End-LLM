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
            mc.completion_time_minutes,
            uca.assigned_at,
            uca.estimated_completion_date,
            uca.is_mandatory, 
            cs.stage_id,
            cs.stage_name,
            cs.stage_description,
            cs.stage_order,
            cs.stage_objectives,
            mc.course_steps,
            mc.completion_time_minutes,
            CASE 
                WHEN c.status = 'FINISHED' AND c.is_accomplished = true
                THEN cs.stage_order
                ELSE 0
            END AS stage_progress
        FROM conversaconfig.user_course_assignments uca 
        JOIN conversaconfig.master_courses mc ON uca.course_id = mc.course_id
        LEFT JOIN conversaconfig.course_stages cs ON cs.course_id = mc.course_id
        LEFT JOIN (
            SELECT 
                c.course_id,
                c.stage_id,
                c.status,
                c.conversation_id,
                sbc.is_accomplished,
                ROW_NUMBER() OVER (
                    PARTITION BY c.course_id, c.stage_id
                    ORDER BY 
                        CASE WHEN c.status = 'FINISHED' AND sbc.is_accomplished = true THEN 0 ELSE 1 END,
                        c.created_at DESC
                ) as rn
            FROM conversaapp.conversations c
            LEFT JOIN conversaapp.scoring_by_conversation sbc 
                ON c.conversation_id = sbc.conversation_id
            WHERE c.user_id = $1
        ) c ON c.course_id = mc.course_id 
            AND c.stage_id = cs.stage_id 
            AND c.rn = 1
        WHERE uca.user_id = $1  
        AND mc.is_active 
        ORDER BY uca.estimated_completion_date ASC, cs.stage_order ASC;
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
                "assigned_at": row['assigned_at'],
                "is_mandatory": row['is_mandatory'],
                "estimated_completion_date":row['estimated_completion_date'],
                "completion_time_minutes": row['completion_time_minutes'],
                "course_steps": row['course_steps'],
                "completion_time_minutes": row['completion_time_minutes'],
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
                "stage_order": row['stage_order'],
            })

    return list(courses_map.values())


async def get_all_courses() -> List[Dict]:

    query = """
        SELECT 
            *
        FROM conversaconfig.master_courses
        order by created_on desc;
    """
    
    results = await execute_query(query)

    return [dict(row) for row in results]

async def get_all_stages() -> List[Dict]:

    query = """
        SELECT 
            *
        FROM conversaconfig.course_stages
            INNER JOIN conversaconfig.course_contents 
            ON course_stages.stage_id = course_contents.stage_id
    """
    
    results = await execute_query(query)

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
      cs.stage_description AS cs_stage_description,
      cc.content_id      AS cc_content_id,
      cc.level           AS cc_level,
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
      mc.course_id       AS course_id,
      mc.name            AS name,
      mc.image_src       AS image_src,
      cs.stage_id        AS stage_id,
      cs.stage_name      AS stage_name,
      cs.stage_description AS stage_description,
      cs.stage_objectives AS stage_objectives,
      cs.chatbot_image_src AS chatbot_image_src,
      cc.content_id      AS content_id,
      cc.level           AS level,
      cc.body            AS body,
      cc.bot_prompt      AS bot_prompt,
      cc.user_role       AS user_role,
      cc.bot_role        AS bot_role,
      cc.context_info    AS context_info,
      cs.key_themes,
      cs.stage_objectives
      FROM conversaconfig.master_courses    mc
        LEFT JOIN conversaconfig.course_stages cs ON cs.course_id = mc.course_id
        LEFT JOIN conversaconfig.course_contents cc ON cc.course_id = mc.course_id AND cc.stage_id = cs.stage_id
        WHERE mc.course_id = $1 and mc.is_active and cs.stage_id = $2
        ORDER BY cs.stage_order NULLS LAST, cc.position NULLS LAST;
    """
    
    results = await execute_query(query, course_id, stage_id)
    return [dict(row) for row in results]

async def get_company_courses(company_id: str) -> List[Dict]:
    """
    Get courses by company id
    """
    query = """
    SELECT
      ALL COURSES FOR A COMPANY
    FROM x
    """
    
    results = await execute_query(query, company_id)
    return [dict(row) for row in results]


async def create_new_course(name: str, description: str, image_src: str, is_active: bool, is_mandatory: bool, completion_time_minutes: int, course_steps: int) -> UUID:
    """
    Create a new course in the system.
    """
    query = """
        INSERT INTO conversaconfig.master_courses 
            (name, description, image_src, is_active, is_mandatory, completion_time_minutes, course_steps)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING course_id;
    """
    result = await execute_query(
        query, 
        name, description, image_src, is_active, is_mandatory, completion_time_minutes, course_steps)
    return result[0]['course_id'] if result else None 

async def update_course(course_id: UUID, name: str, description: str, image_src: str, is_active: bool, is_mandatory: bool, completion_time_minutes: int, course_steps: int) -> UUID:
    """
    Update an existing course in the system.
    """
    query = """
        UPDATE conversaconfig.master_courses 
        SET name = $2, description = $3, image_src = $4, is_active = $5, is_mandatory = $6, completion_time_minutes = $7, course_steps = $8
        WHERE course_id = $1
        RETURNING course_id;
    """
    result = await execute_query(
        query, 
        course_id, name, description, image_src, is_active, is_mandatory, completion_time_minutes, course_steps)
    return result[0]['course_id'] if result else None

async def create_new_stage(
    course_id: UUID, stage_order: int, stage_name: str, stage_description: str, 
    key_themes: str, position: int, level: str, body: str, bot_prompt: str, user_role: str, 
    bot_role: str, context_info: str, stage_objectives: str, voice_id: str, agent_id: str, chatbot_image_src: str
) -> UUID:
    """
    Create a new stage in the system.
    """
    query = """
        INSERT INTO conversaconfig.course_stages 
            (course_id, stage_order, stage_name, stage_description, 
            key_themes, stage_objectives, voice_id, agent_id, chatbot_image_src)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING stage_id;
    """
    result = await execute_query(
        query, 
        course_id, stage_order, stage_name, stage_description, key_themes, stage_objectives, voice_id, agent_id, chatbot_image_src
    )
    if result:
        stage_id = result[0]['stage_id']
        # Insert content for the stage
        content_query = """
            INSERT INTO conversaconfig.course_contents 
                (course_id, stage_id, position, level, body, bot_prompt, user_role, bot_role, context_info)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
        """
        await execute_query(
            content_query,
            course_id, stage_id, position, level, body, bot_prompt, user_role, bot_role, context_info
        )

    return result[0]['stage_id'] if result else None

async def update_stage(
    stage_id: UUID, course_id: UUID, stage_order: int, stage_name: str, stage_description: str, 
    key_themes: str, position: int, level: str, body: str, bot_prompt: str, user_role: str, 
    bot_role: str, context_info: str, stage_objectives: str, voice_id: str, agent_id: str, chatbot_image_src: str
) -> UUID:
    """
    Update an existing stage in the system.
    """
    query = """
        UPDATE conversaconfig.course_stages 
        SET stage_order = $3, stage_name = $4, stage_description = $5, 
            key_themes = $6, stage_objectives = $7, voice_id = $8, agent_id = $9, chatbot_image_src = $10
        WHERE stage_id = $1 and course_id = $2
        RETURNING stage_id;
    """
    result = await execute_query(
        query,
        stage_id, course_id, stage_order, stage_name, stage_description, key_themes, stage_objectives, voice_id, agent_id, chatbot_image_src
    )
    if result:
        # Update content for the stage
        content_query = """
            UPDATE conversaconfig.course_contents 
            SET position = $3, level = $4, body = $5, bot_prompt = $6, user_role = $7, bot_role = $8, context_info = $9
            WHERE stage_id = $1 and course_id = $2;
        """
        await execute_query(
            content_query,
            stage_id, course_id, position, level, body, bot_prompt, user_role, bot_role, context_info
        )

    return result[0]['stage_id'] if result else None
