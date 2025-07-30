"""
Database connection and operations for testing interface
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
import google.generativeai as genai
from config import settings

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.gemini_model = None
        
    async def initialize(self):
        """Initialize database and AI connections"""
        try:
            # Initialize Supabase
            self.supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            
            # Initialize Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            print("✅ Database and AI connections initialized")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize connections: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection and return status"""
        try:
            # Test Supabase connection
            response = self.supabase.table("users").select("count", count="exact").execute()
            user_count = response.count if response.count else 0
            
            # Test conversations table
            conv_response = self.supabase.table("conversations").select("count", count="exact").execute()
            conversation_count = conv_response.count if conv_response.count else 0
            
            # Test messages table
            msg_response = self.supabase.table("messages").select("count", count="exact").execute()
            message_count = msg_response.count if msg_response.count else 0
            
            return {
                "status": "connected",
                "supabase_url": settings.SUPABASE_URL,
                "stats": {
                    "users": user_count,
                    "conversations": conversation_count,
                    "messages": message_count
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_recent_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent conversations with user info"""
        try:
            response = self.supabase.table("conversations").select(
                "*, users(name, email, plan)"
            ).order("created_at", desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"Error fetching conversations: {e}")
            return []
    
    async def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages for a specific conversation"""
        try:
            response = self.supabase.table("messages").select("*").eq(
                "conversation_id", conversation_id
            ).order("created_at", asc=True).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []
    
    async def get_search_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent search results"""
        try:
            response = self.supabase.table("search_results").select(
                "*, users(name, email, plan), projects(name, stage, category)"
            ).order("created_at", desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"Error fetching search results: {e}")
            return []
    
    async def get_investor_data(self, search_term: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """Get angel investors data with optional search"""
        try:
            query = self.supabase.table("angel_investors").select("*")
            
            if search_term:
                query = query.or_(
                    f"fullName.ilike.%{search_term}%,"
                    f"headline.ilike.%{search_term}%,"
                    f"addressWithCountry.ilike.%{search_term}%,"
                    f"categories_general_en.ilike.%{search_term}%"
                )
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"Error fetching investors: {e}")
            return []
    
    async def get_fund_data(self, search_term: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """Get investment funds data with optional search"""
        try:
            query = self.supabase.table("investment_funds").select("*")
            
            if search_term:
                query = query.or_(
                    f"name.ilike.%{search_term}%,"
                    f"description.ilike.%{search_term}%,"
                    f"category_keywords.ilike.%{search_term}%"
                )
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"Error fetching funds: {e}")
            return []
    
    async def simulate_chat_message(self, message: str, user_id: str = None) -> Dict[str, Any]:
        """Simulate a chat message through the AI system"""
        try:
            # Create a test conversation if needed
            if not user_id:
                user_id = "test-user-123"
            
            # Generate AI response using Gemini
            prompt = f"""
            You are 0BullshitIntelligence, an AI assistant specialized in connecting startups with investors.
            
            User message: "{message}"
            
            Respond as the AI chat system would, providing helpful advice about investors, fundraising, or startup guidance.
            Keep response concise and actionable, Y-Combinator style.
            """
            
            response = await self.gemini_model.generate_content_async(prompt)
            ai_response = response.text
            
            # Save to database (create conversation and messages)
            conversation_data = {
                "user_id": user_id,
                "title": message[:50] + "..." if len(message) > 50 else message,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            conv_result = self.supabase.table("conversations").insert(conversation_data).execute()
            conversation_id = conv_result.data[0]["id"] if conv_result.data else None
            
            if conversation_id:
                # Save user message
                user_msg = {
                    "conversation_id": conversation_id,
                    "role": "user",
                    "content": message,
                    "created_at": datetime.utcnow().isoformat()
                }
                self.supabase.table("messages").insert(user_msg).execute()
                
                # Save AI response
                ai_msg = {
                    "conversation_id": conversation_id,
                    "role": "assistant",
                    "content": ai_response,
                    "gemini_prompt_used": "test_simulation",
                    "gemini_response_raw": ai_response,
                    "created_at": datetime.utcnow().isoformat()
                }
                self.supabase.table("messages").insert(ai_msg).execute()
            
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "user_message": message,
                "ai_response": ai_response,
                "processing_time_ms": 1500  # Simulated
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        try:
            # Users stats
            users_response = self.supabase.table("users").select("plan", count="exact").execute()
            users_by_plan = {}
            if users_response.data:
                for user in users_response.data:
                    plan = user.get("plan", "free")
                    users_by_plan[plan] = users_by_plan.get(plan, 0) + 1
            
            # Recent activity (last 24 hours)
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
            
            recent_conversations = self.supabase.table("conversations").select(
                "count", count="exact"
            ).gte("created_at", yesterday).execute()
            
            recent_messages = self.supabase.table("messages").select(
                "count", count="exact"
            ).gte("created_at", yesterday).execute()
            
            recent_searches = self.supabase.table("search_results").select(
                "count", count="exact"
            ).gte("created_at", yesterday).execute()
            
            # Total counts
            total_angels = self.supabase.table("angel_investors").select(
                "count", count="exact"
            ).execute()
            
            total_funds = self.supabase.table("investment_funds").select(
                "count", count="exact"
            ).execute()
            
            total_companies = self.supabase.table("companies").select(
                "count", count="exact"
            ).execute()
            
            return {
                "users": {
                    "total": users_response.count or 0,
                    "by_plan": users_by_plan
                },
                "activity_24h": {
                    "conversations": recent_conversations.count or 0,
                    "messages": recent_messages.count or 0,
                    "searches": recent_searches.count or 0
                },
                "database": {
                    "angel_investors": total_angels.count or 0,
                    "investment_funds": total_funds.count or 0,
                    "companies": total_companies.count or 0
                }
            }
            
        except Exception as e:
            print(f"Error getting dashboard stats: {e}")
            return {"error": str(e)}

# Global database manager instance
db_manager = DatabaseManager()