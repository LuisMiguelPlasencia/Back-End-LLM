# this program will be imported in realtime_bridge and added to the stop() method (????)

import asyncio
import base64
import numpy as np
import json
from app.services.conversations_service import close_conversation, get_conversation_status
from app.services.scoring_service import scoring
from app.services.profiling_service import profiling
from scoring_scripts.get_user_profile import user_clasiffier

async def stop_process(user_id, conversation_id, frontend_ws, course_id, stage_id, conversation_id_elevenlabs, agent_id):

    await close_conversation(user_id, conversation_id, conversation_id_elevenlabs, agent_id) 
    ## scoring conversation if conver finished
    await scoring(conversation_id, course_id, stage_id)
    await profiling(conversation_id, course_id, stage_id)
    await user_clasiffier(user_id)
    # notify frontend that conversation is closed and scored
    await frontend_ws.send_text(json.dumps({"type": "conversation.scoring.completed", "conversation_id": str(conversation_id)}))

async def openai_msg_process(user_id, conversation_id):
    # placeholder for any processing needed when receiving messages from OpenAI
    pass

async def user_msg_processed(user_id, conversation_id):
    # placeholder for any processing needed when user message is sent to OpenAI
    pass

def is_non_silent(audio_b64, threshold=0.01):
    pcm = np.frombuffer(base64.b64decode(audio_b64), dtype=np.int16)
    rms = np.sqrt(np.mean((pcm / 32768.0) ** 2))
    return rms > threshold
