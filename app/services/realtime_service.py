# this program will be imported in realtime_bridge and added to the stop() method (????)

import asyncio
from app.services.conversations_service import close_conversation, get_conversation_status
from app.services.scoring_service import scoring


async def stop_process(user_id, conversation_id, frontend_ws):

    await close_conversation(user_id, conversation_id) 
        ## scoring conversation if conver finished
    status = await get_conversation_status(conversation_id, user_id)
    print(f'status checked: {status}')
    if status == "FINISHED": 
        print('computing scores')
        await asyncio.to_thread(scoring, conversation_id)
        # notify frontend that conversation is closed and scored
        await frontend_ws.send_text('conversation.scoring.completed')
    else:
        print('conversation not finished, skipping scoring')
        # notify frontend that conversation is closed but not finished
        await frontend_ws.send_text('conversation.scoring.skipped')

async def openai_msg_process(user_id, conversation_id):
    # placeholder for any processing needed when receiving messages from OpenAI
    pass

async def user_msg_processed(user_id, conversation_id):
    # placeholder for any processing needed when user message is sent to OpenAI
    pass


