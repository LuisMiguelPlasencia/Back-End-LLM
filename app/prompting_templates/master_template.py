import os

async def master_prompt(level: str,  bot_prompt: str):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if level == "BÁSICO": 
        level_txt = os.path.join(script_dir, "basic.txt")
        with open(level_txt, "r") as f:
            level_prompt = f.read()

    elif level == "INTERMEDIO": 
        level_txt = os.path.join(script_dir, "intermedio.txt")
        with open(level_txt, "r") as f:
            level_prompt = f.read()

    elif level == "AVANZADO": 
        level_txt = os.path.join(script_dir, "avanzado.txt")
        with open(level_txt, "r") as f:
            level_prompt = f.read()
    else: 
        level_prompt = ""

    master_prompt = f"""# CONTEXTO, ROL Y OBJETIVO {bot_prompt}
    {level_prompt}"""

    return master_prompt

