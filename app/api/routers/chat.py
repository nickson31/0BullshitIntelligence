"""
Chat router - Main endpoint for AI chat interactions
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse

from app.core.logging import get_logger
from app.models import (
    ResponseModel, ChatMessage, ChatResponse, ConversationCreate,
    ConversationResponse, Language, UserContext
)
from app.services.chat_service import chat_service
from app.services.conversation_service import conversation_service
from app.api.middleware import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    user_context: UserContext = Depends(get_current_user)
):
    """
    Send a message to the AI chat system
    
    This is the main endpoint for chat interactions. It:
    1. Analyzes user intent with Judge System
    2. Executes appropriate actions (mentor response, searches, etc.)
    3. Returns structured response with any results
    4. Saves conversation in background
    """
    try:
        logger.info(f"Processing chat message", 
                   user_id=user_context.user_id,
                   conversation_id=message.conversation_id,
                   message_length=len(message.content))
        
        # Process the message through the chat service
        response = await chat_service.process_message(
            message=message,
            user_context=user_context
        )
        
        # Save conversation in background
        background_tasks.add_task(
            conversation_service.save_message,
            message,
            response,
            user_context.user_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat message processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    user_context: UserContext = Depends(get_current_user)
):
    """Create a new conversation"""
    try:
        conversation = await conversation_service.create_conversation(
            user_id=user_context.user_id,
            project_id=conversation_data.project_id,
            title=conversation_data.title
        )
        
        return ConversationResponse(
            success=True,
            message="Conversation created successfully",
            data=conversation
        )
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("/conversations", response_model=ResponseModel)
async def get_conversations(
    project_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user_context: UserContext = Depends(get_current_user)
):
    """Get user's conversations"""
    try:
        conversations = await conversation_service.get_user_conversations(
            user_id=user_context.user_id,
            project_id=project_id,
            limit=limit,
            offset=offset
        )
        
        return ResponseModel(
            success=True,
            message="Conversations retrieved successfully",
            data={
                "conversations": conversations,
                "total_count": len(conversations),
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")


@router.get("/conversations/{conversation_id}", response_model=ResponseModel)
async def get_conversation(
    conversation_id: str,
    user_context: UserContext = Depends(get_current_user)
):
    """Get conversation details and message history"""
    try:
        conversation = await conversation_service.get_conversation_with_history(
            conversation_id=conversation_id,
            user_id=user_context.user_id
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ResponseModel(
            success=True,
            message="Conversation retrieved successfully",
            data=conversation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")


@router.post("/conversations/{conversation_id}/title", response_model=ResponseModel)
async def update_conversation_title(
    conversation_id: str,
    title_data: Dict[str, str],
    user_context: UserContext = Depends(get_current_user)
):
    """Update conversation title"""
    try:
        await conversation_service.update_conversation_title(
            conversation_id=conversation_id,
            user_id=user_context.user_id,
            new_title=title_data.get("title", "")
        )
        
        return ResponseModel(
            success=True,
            message="Conversation title updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to update conversation title: {e}")
        raise HTTPException(status_code=500, detail="Failed to update title")


@router.get("/welcome", response_model=ResponseModel)
async def get_welcome_message(
    project_id: Optional[str] = None,
    user_context: UserContext = Depends(get_current_user)
):
    """Get personalized welcome message for new chat"""
    try:
        from app.ai_systems.welcome_system import welcome_system
        
        welcome_message = await welcome_system.generate_welcome_message(
            user_context=user_context,
            project_id=project_id
        )
        
        return ResponseModel(
            success=True,
            message="Welcome message generated",
            data={"welcome_message": welcome_message}
        )
        
    except Exception as e:
        logger.error(f"Failed to generate welcome message: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate welcome message")


@router.post("/regenerate", response_model=ChatResponse)
async def regenerate_response(
    regenerate_data: Dict[str, Any],
    user_context: UserContext = Depends(get_current_user)
):
    """Regenerate the last AI response"""
    try:
        conversation_id = regenerate_data.get("conversation_id")
        message_id = regenerate_data.get("message_id")
        
        if not conversation_id or not message_id:
            raise HTTPException(status_code=400, detail="conversation_id and message_id required")
        
        response = await chat_service.regenerate_response(
            conversation_id=conversation_id,
            message_id=message_id,
            user_context=user_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate response: {e}")
        raise HTTPException(status_code=500, detail="Failed to regenerate response")


@router.get("/stream/{conversation_id}")
async def stream_chat_response(
    conversation_id: str,
    user_context: UserContext = Depends(get_current_user)
):
    """Stream chat response for real-time updates during processing"""
    try:
        async def generate_stream():
            async for chunk in chat_service.stream_response(conversation_id, user_context):
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        logger.error(f"Failed to stream response: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream response")


@router.delete("/conversations/{conversation_id}", response_model=ResponseModel)
async def delete_conversation(
    conversation_id: str,
    user_context: UserContext = Depends(get_current_user)
):
    """Delete a conversation"""
    try:
        await conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_context.user_id
        )
        
        return ResponseModel(
            success=True,
            message="Conversation deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")