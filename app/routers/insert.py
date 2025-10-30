# Insert routes for data creation
# Handles POST requests for creating conversations and sending messages
# Examples:
# curl -X POST "http://localhost:8000/insert/conversation" -H "Content-Type: application/json" -d '{"user_id":"123e4567-e89b-12d3-a456-426614174000","course_id":"123e4567-e89b-12d3-a456-426614174001"}'
# curl -X POST "http://localhost:8000/insert/message" -H "Content-Type: application/json" -d '{"user_id":"123e4567-e89b-12d3-a456-426614174000","conversation_id":"123e4567-e89b-12d3-a456-426614174002","message":"Hello, how are you?"}'

from fastapi import APIRouter
from ..schemas.insert import StartConversationRequest, SendMessageRequest, CloseConversationRequest
from ..services.conversations_service import create_conversation, close_conversation
from ..services.messages_service import send_message
from ..utils.responses import error

router = APIRouter(prefix="/insert", tags=["insert"])

@router.post("/conversation")
async def start_conversation(request: StartConversationRequest):
    """
    Create a new conversation for user
    Note: course_id is accepted for compatibility but not stored in database
    """
    try:
        conversation = await create_conversation(request.user_id, request.course_id)
        
        if not conversation:
            error(500, "Failed to create conversation")
        
        return {
            "status": "conversation created success",
            "conversation": conversation
        }
    
    except Exception as e:
        error(500, f"Failed to create conversation: {str(e)}")

@router.post("/message")
async def send_user_message(request: SendMessageRequest):
    """
    Send a message in a conversation and get assistant response
    Creates both user message and automatic assistant response
    """
    try:
        # Validate message is not empty
        if not request.message or not request.message.strip():
            error(400, "Message cannot be empty")
        
        user_message, assistant_response = await send_message(
            request.user_id, 
            request.conversation_id, 
            request.message.strip()
        )
        
        if not user_message or not assistant_response:
            error(500, "Failed to send message")
        
        return {
            "status": "message sent",
            "message": user_message,
            "assistant_response": assistant_response
        }
    
    except Exception as e:
        error(500, f"Failed to send message: {str(e)}")

@router.post("/close_conversation")
async def close_conversation_route(request: CloseConversationRequest):
    """
    Close a conversation for user
    """
    try:
        result = await close_conversation(request.conversation_id, request.user_id, request.course_id)
        
        if not result:
            error(500, "Failed to close conversation")
        
        return {
            "status": "conversation closed success",
            "result": result
        }
    
    except Exception as e:
        error(500, f"Failed to create conversation: {str(e)}")