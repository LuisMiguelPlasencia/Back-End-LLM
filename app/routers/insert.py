# Insert routes for data creation
# Handles POST requests for creating conversations and sending messages
# Examples:
# curl -X POST "http://localhost:8000/insert/conversation" -H "Content-Type: application/json" -d '{"user_id":"123e4567-e89b-12d3-a456-426614174000","course_id":"123e4567-e89b-12d3-a456-426614174001"}'
# curl -X POST "http://localhost:8000/insert/message" -H "Content-Type: application/json" -d '{"user_id":"123e4567-e89b-12d3-a456-426614174000","conversation_id":"123e4567-e89b-12d3-a456-426614174002","message":"Hello, how are you?"}'

from fastapi import APIRouter, Depends

from app.services.auth_service import validate_user
from app.services.courses_service import create_new_course, create_new_stage, update_course, update_stage, update_stage
from ..schemas.insert import NewCourseRequest, NewStageRequest, StartConversationRequest, SendMessageRequest, CloseConversationRequest, UpdateCourseRequest, UpdateProgressRequest, UpdateStageRequest
from ..services.conversations_service import create_conversation, close_conversation
from ..services.messages_service import send_message, update_module_progress
from ..services.payments_service import simulate_investment, InvestmentSimulation
from ..utils.responses import error

router = APIRouter(prefix="/insert", tags=["insert"])

@router.post("/conversation")
async def start_conversation(request: StartConversationRequest):
    """
    Create a new conversation for user
    Note: course_id is accepted for compatibility but not stored in database
    """
    try:
        conversation = await create_conversation(request.user_id, request.course_id,request.stage_id)
        
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
            request.message.strip(),
            request.role, 
            request.duration
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


@router.post("/simulate-investment")
async def simulate_investment_checkout(data: InvestmentSimulation):
    """Simulate the investment for the checkout"""
    try:
        investment = await simulate_investment(data)
        return investment
    except Exception as e:
        error(500, f"Failed to retrieve: {str(e)}")

@router.post("/update_progress")
async def update_progress_route(request: UpdateProgressRequest):
    """
    Updates the progress for a user when they complete a module.
    Automatically handles course completion and journey completion statuses.
    """
    try:
        # Llamamos a la función que ejecuta el UPSERT en base de datos
        result = await update_module_progress(
            user_id=request.user_id, 
            journey_id=request.journey_id, 
            course_id=request.course_id
        )
        
        # Validamos si la función interna reportó algún error lógico
        if not result or not result.get("success"):
            error_msg = result.get("error", "Unknown database error") if result else "No result returned"
            error(500, f"Failed to update progress: {error_msg}")
        
        # Retornamos el éxito con el formato que ya usas
        return {
            "status": "progress updated success",
            "result": {
                "course_status": result.get("course_status"),
                "journey_status": result.get("journey_status"),
                "completed_modules": result.get("completed_modules")
            }
        }
    
    except Exception as e:
        error(500, f"Failed to update progress: {str(e)}")



@router.post("/course")
async def create_new_courseAPI(request: NewCourseRequest, _: dict = Depends(validate_user)):
    """
    Create a new course in the system. This endpoint is intended for admin use to add courses to the platform.
    """
    try:
        # Validate message is not empty
        if not request.name or not request.name.strip():
            error(400, "Course name cannot be empty")
        
        course_id = await create_new_course(
            name=request.name,
            description=request.description,
            image_src=request.image_src,
            is_active=request.is_active,
            is_mandatory=request.is_mandatory,
            completion_time_minutes=request.completion_time_minutes,
            course_steps=request.course_steps
        )
        
        if not course_id:
            error(500, "Failed to create course")
        
        return {
            "status": "course created",
            "course_id": course_id
        }
    
    except Exception as e:
        error(500, f"Failed to create course: {str(e)}")


@router.post("/update_course")
async def update_courseAPI(request: UpdateCourseRequest, _: dict = Depends(validate_user)):
    """
    Update an existing course in the system. This endpoint is intended for admin use to update courses in the platform.
    """
    try:
        # Validate message is not empty
        if not request.course_id:
            error(400, "Course id cannot be empty")
        if not request.name or not request.name.strip():
            error(400, "Course name cannot be empty")
        
        course_id = await update_course(
            course_id=request.course_id,
            name=request.name,
            description=request.description,
            image_src=request.image_src,
            is_active=request.is_active,
            is_mandatory=request.is_mandatory,
            completion_time_minutes=request.completion_time_minutes,
            course_steps=request.course_steps
        )
        
        if not course_id:
            error(500, "Failed to update course")
        
        return {
            "status": "course updated",
            "course_id": course_id
        }
    
    except Exception as e:
        error(500, f"Failed to update course: {str(e)}")



@router.post("/stage")
async def create_new_stageAPI(request: NewStageRequest, _: dict = Depends(validate_user)):
    """
    Create a new stage in the system. This endpoint is intended for admin use to add stages to existing courses.
    """
    try:
        # Validate message is not empty
        if not request.stage_name or not request.stage_name.strip():
            error(400, "Stage name cannot be empty")
        
        stage_id = await create_new_stage(
            course_id=request.course_id,
            stage_order=request.stage_order,
            stage_name=request.stage_name,
            stage_description=request.stage_description,
            key_themes=request.key_themes,
            position=request.position,
            level=request.level,
            body=request.body,
            bot_prompt=request.bot_prompt,
            user_role=request.user_role,
            bot_role=request.bot_role,
            context_info=request.context_info,
            stage_objectives=request.stage_objectives,
            voice_id=request.voice_id,
            agent_id=request.agent_id,
            chatbot_image_src=request.chatbot_image_src
        )
        
        if not stage_id:
            error(500, "Failed to create stage")
        
        return {
            "status": "stage created",
            "stage_id": stage_id
        }
    
    except Exception as e:
        error(500, f"Failed to create stage: {str(e)}")

@router.post("/update_stage")
async def update_stageAPI(request: UpdateStageRequest, _: dict = Depends(validate_user)):
    """
    Update an existing stage in the system. This endpoint is intended for admin use to update stages in existing courses.
    """
    try:
        # Validate message is not empty
        if not request.stage_id:
            error(400, "Stage id cannot be empty")
        if not request.stage_name or not request.stage_name.strip():
            error(400, "Stage name cannot be empty")

        print(request)
        
        stage_id = await update_stage(
            stage_id=request.stage_id,
            course_id=request.course_id,
            stage_order=request.stage_order,
            stage_name=request.stage_name,
            stage_description=request.stage_description,
            key_themes=request.key_themes,
            position=request.position,
            level=request.level,
            body=request.body,
            bot_prompt=request.bot_prompt,
            user_role=request.user_role,
            bot_role=request.bot_role,
            context_info=request.context_info,
            stage_objectives=request.stage_objectives,
            voice_id=request.voice_id,
            agent_id=request.agent_id,
            chatbot_image_src=request.chatbot_image_src
        )
        
        if not stage_id:
            error(500, "Failed to update stage")
        
        return {
            "status": "stage updated",
            "stage_id": stage_id
        }
    
    except Exception as e:
        error(500, f"Failed to create stage: {str(e)}")
