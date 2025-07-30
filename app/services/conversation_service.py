"""
Conversation Service - Manages chat conversations and message history
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.models import ChatMessage, ChatResponse
from app.database import database_manager

logger = get_logger(__name__)


class ConversationService:
    """
    Service for managing conversations and message history
    """
    
    def __init__(self):
        self.created_conversations = 0
        self.saved_messages = 0
    
    async def create_conversation(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new conversation"""
        
        try:
            conversation_id = str(uuid.uuid4())
            
            # Save to database
            conversation = await database_manager.save_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                project_id=project_id,
                title=title or "Nueva conversación"
            )
            
            self.created_conversations += 1
            
            logger.info(f"Conversation created: {conversation_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def save_message(
        self,
        message: ChatMessage,
        response: ChatResponse,
        user_id: str
    ):
        """Save message and response to database"""
        
        try:
            # Save user message
            await database_manager.save_message(
                message_id=str(message.id),
                conversation_id=str(message.conversation_id),
                role="user",
                content=message.content,
                user_id=user_id
            )
            
            # Save AI response
            if response.ai_response:
                ai_message_id = str(uuid.uuid4())
                await database_manager.save_message(
                    message_id=ai_message_id,
                    conversation_id=str(message.conversation_id),
                    role="assistant",
                    content=response.ai_response,
                    user_id=user_id,
                    ai_response_data=response.data,
                    search_results=response.search_results
                )
            
            self.saved_messages += 2
            
            logger.debug(f"Messages saved for conversation {message.conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to save messages: {e}")
            # Don't raise - this is background task
    
    async def get_user_conversations(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's conversations"""
        
        try:
            # This would need to be implemented in database_manager
            # For now, return empty list
            logger.info(f"Getting conversations for user {user_id}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            raise
    
    async def get_conversation_with_history(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get conversation with message history"""
        
        try:
            # Get message history
            messages = await database_manager.get_conversation_history(
                conversation_id=conversation_id,
                limit=50
            )
            
            if not messages:
                return None
            
            return {
                "conversation_id": conversation_id,
                "messages": messages,
                "message_count": len(messages)
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            raise
    
    async def update_conversation_title(
        self,
        conversation_id: str,
        user_id: str,
        new_title: str
    ):
        """Update conversation title"""
        
        try:
            # This would need to be implemented in database_manager
            logger.info(f"Updating title for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to update conversation title: {e}")
            raise
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ):
        """Delete a conversation"""
        
        try:
            # This would need to be implemented in database_manager
            logger.info(f"Deleting conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "created_conversations": self.created_conversations,
            "saved_messages": self.saved_messages
        }


# Create singleton instance
conversation_service = ConversationService()