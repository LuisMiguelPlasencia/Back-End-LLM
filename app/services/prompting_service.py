


from .db import execute_query
from uuid import UUID
from typing import List, Dict
from .courses_service import get_courses_details
from ..prompting_templates.master_template import master_prompt as master_prompt_template

async def master_prompt_generator(course_id: UUID, stage_id: UUID) -> str:
    course = await get_courses_details(course_id, stage_id)

    if not course:
        raise ValueError("No data found for the course and stage specified.")

    row = course[0] 

    return await master_prompt_template(
        row["mc_name"],                # main_theme
        row["cc_title"],               # level
        row["cs_stage_name"],          # role
        row["cs_stage_description"],   # level_description
        row["cc_bot_prompt"],          # bot_prompt
        row["cc_body"]                 # course_body
    )