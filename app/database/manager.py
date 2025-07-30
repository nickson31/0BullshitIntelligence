"""
Database Manager for Supabase connections and operations
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from supabase import create_client, Client
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class DatabaseManager:
    """
    Manages Supabase database connections and operations
    """

    def __init__(self):
        self.client: Optional[Client] = None
        self.logger = logger

    async def initialize(self):
        """Initialize Supabase client"""
        try:
            self.client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self.logger.info("Supabase client initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {e}")
            return False

    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            if not self.client:
                await self.initialize()
            
            # Simple health check - try to access a system table
            result = self.client.table('conversations').select('count').limit(1).execute()
            self.logger.info("Database health check passed")
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False

    # ==========================================
    # CONVERSATION OPERATIONS
    # ==========================================

    async def create_conversation(self, session_id: str, initial_data: Optional[Dict[str, Any]] = None) -> str:
        """Create a new conversation"""
        try:
            conversation_data = {
                'session_id': session_id,
                'created_at': datetime.utcnow().isoformat(),
                'project_data': initial_data or {},
                'completeness_score': 0.0
            }
            
            result = self.client.table('conversations').insert(conversation_data).execute()
            conversation_id = result.data[0]['id']
            
            self.logger.info("Conversation created", 
                           session_id=session_id, 
                           conversation_id=conversation_id)
            return conversation_id
            
        except Exception as e:
            self.logger.error(f"Failed to create conversation: {e}")
            raise

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        try:
            result = self.client.table('conversations').select('*').eq('id', conversation_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation: {e}")
            return None

    async def get_session_conversations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a session"""
        try:
            result = self.client.table('conversations').select('*').eq('session_id', session_id).order('created_at', desc=True).execute()
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"Failed to get session conversations: {e}")
            return []

    async def update_conversation_data(self, conversation_id: str, project_data: Dict[str, Any], completeness_score: float) -> bool:
        """Update conversation project data"""
        try:
            update_data = {
                'project_data': project_data,
                'completeness_score': completeness_score,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('conversations').update(update_data).eq('id', conversation_id).execute()
            
            self.logger.info("Conversation data updated", 
                           conversation_id=conversation_id, 
                           completeness_score=completeness_score)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update conversation data: {e}")
            return False

    # ==========================================
    # MESSAGE OPERATIONS
    # ==========================================

    async def save_message(self, conversation_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save a message to the conversation"""
        try:
            message_data = {
                'conversation_id': conversation_id,
                'role': role,  # 'user' or 'assistant'
                'content': content,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('messages').insert(message_data).execute()
            message_id = result.data[0]['id']
            
            self.logger.info("Message saved", 
                           conversation_id=conversation_id, 
                           role=role, 
                           message_id=message_id)
            return message_id
            
        except Exception as e:
            self.logger.error(f"Failed to save message: {e}")
            raise

    async def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages for a conversation"""
        try:
            result = (self.client.table('messages')
                     .select('*')
                     .eq('conversation_id', conversation_id)
                     .order('created_at', desc=False)
                     .limit(limit)
                     .execute())
            
            return result.data or []
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation messages: {e}")
            return []

    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history (alias for get_conversation_messages for backward compatibility)"""
        return await self.get_conversation_messages(conversation_id, limit)

    # ==========================================
    # ANALYTICS OPERATIONS
    # ==========================================

    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a session"""
        try:
            # Get conversation count and data
            conversations = await self.get_session_conversations(session_id)
            
            if not conversations:
                return {
                    'total_conversations': 0,
                    'total_messages': 0,
                    'avg_completeness': 0.0,
                    'categories_mentioned': [],
                    'last_activity': None
                }
            
            # Calculate metrics
            total_conversations = len(conversations)
            avg_completeness = sum(c.get('completeness_score', 0) for c in conversations) / total_conversations
            
            # Extract categories from all conversations
            all_categories = []
            for conv in conversations:
                project_data = conv.get('project_data', {})
                categories = project_data.get('categories', [])
                all_categories.extend(categories)
            
            unique_categories = list(set(all_categories))
            
            # Get total message count
            total_messages = 0
            for conv in conversations:
                messages = await self.get_conversation_messages(conv['id'])
                total_messages += len(messages)
            
            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'avg_completeness': round(avg_completeness, 2),
                'categories_mentioned': unique_categories,
                'last_activity': conversations[0]['updated_at'] if conversations else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get session analytics: {e}")
            return {}

    async def close(self):
        """Close database connections"""
        self.logger.info("Database manager closed")


# Global instance
database_manager = DatabaseManager()