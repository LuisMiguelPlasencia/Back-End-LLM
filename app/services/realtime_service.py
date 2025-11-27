# this program will be imported in realtime_bridge and added to the stop() method (????)

from app.services.conversations_service import close_conversation


async def stop_process(user_id, conversation_id):

    await close_conversation(user_id, conversation_id) 
    pass

async def openai_msg_process(user_id, conversation_id):
    # placeholder for any processing needed when receiving messages from OpenAI
    pass

async def user_msg_processed(user_id, conversation_id):
    # placeholder for any processing needed when user message is sent to OpenAI
    pass


