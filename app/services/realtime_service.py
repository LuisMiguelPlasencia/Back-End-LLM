# this program will be imported in realtime_bridge and added to the stop() method (????)

import asyncio
import json
from app.services.conversations_service import close_conversation, get_conversation_status
from app.services.scoring_service import scoring


async def stop_process(user_id, conversation_id, frontend_ws):

    await close_conversation(user_id, conversation_id) 
    ## scoring conversation if conver finished
    await scoring(conversation_id)
    # notify frontend that conversation is closed and scored
    await frontend_ws.send_text(json.dumps({"type": "conversation.scoring.completed", "conversation_id": str(conversation_id)}))

async def openai_msg_process(user_id, conversation_id):
    # placeholder for any processing needed when receiving messages from OpenAI
    pass

async def user_msg_processed(user_id, conversation_id):
    # placeholder for any processing needed when user message is sent to OpenAI
    pass


