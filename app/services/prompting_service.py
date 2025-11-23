


from .db import execute_query
from uuid import UUID
from typing import List, Dict
from .courses_service import get_courses_details
from ..prompting_templates.master_template import master_prompt as master_prompt_template

async def master_prompt_generator(course_id: UUID) -> dict:

    courses_details = await get_courses_details(course_id)

    main_theme = courses_details[0]['mc_name']
    level = courses_details[0]['cc_title']
    role = courses_details[0]['cs_stage_name']
    level_description = courses_details[0]['cs_stage_description']
    bot_prompt = courses_details[0]['bot_prompt']
    course_body = courses_details[0]['cc_body']

    return await master_prompt_template(main_theme, level, role, level_description, bot_prompt, course_body)