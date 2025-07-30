"""
Database Manager for Supabase connections and operations
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from supabase import create_client, Client
import asyncpg
from app.core.config import settings, features
from app.core.logging import get_logger, log_database_performance

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages Supabase database connections and operations
    """
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.sync_supabase: Optional[Client] = None
        self.is_initialized = False
        
        # Table names (all lowercase as per Supabase convention)
        self.tables = {
            "angel_investors": "angel_investors",
            "investment_funds": "investment_funds", 
            "fund_employees": "fund_employees",
            "companies": "companies",
            "conversations": "conversations",
            "messages": "messages",
            "search_results": "search_results",
            "projects": "projects",
            "users": "users"
        }
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Initialize primary Supabase connection
            self.supabase = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            
            logger.info("Primary Supabase connection initialized")
            
            # Initialize sync connection if enabled
            if features.is_sync_enabled() and settings.sync_supabase_url:
                self.sync_supabase = create_client(
                    settings.sync_supabase_url,
                    settings.sync_supabase_key
                )
                logger.info("Sync Supabase connection initialized")
            
            # Test connections
            await self._test_connections()
            
            self.is_initialized = True
            logger.info("✅ Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _test_connections(self):
        """Test database connections"""
        try:
            # Test primary connection
            result = self.supabase.table(self.tables["angel_investors"]).select("count", count="exact").limit(1).execute()
            logger.info(f"Primary database test successful. Angel investors count: {result.count}")
            
            # Test sync connection if available
            if self.sync_supabase:
                # Try to access a common table like users
                try:
                    result = self.sync_supabase.table("users").select("count", count="exact").limit(1).execute()
                    logger.info(f"Sync database test successful. Users count: {result.count}")
                except Exception as e:
                    logger.warning(f"Sync database test failed (may not have users table): {e}")
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            if not self.is_initialized:
                return False
            
            # Quick health check on primary database
            result = self.supabase.table(self.tables["angel_investors"]).select("linkedinurl").limit(1).execute()
            return len(result.data) >= 0  # Even 0 results means connection is working
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    # ==========================================
    # INVESTOR SEARCH OPERATIONS
    # ==========================================
    
    @log_database_performance("search_angel_investors", "angel_investors")
    async def search_angel_investors(
        self,
        keywords: List[str],
        categories: List[str] = None,
        stages: List[str] = None,
        min_score: float = 40.0,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """Search angel investors with keyword matching"""
        try:
            query = self.supabase.table(self.tables["angel_investors"]).select(
                "linkedinurl, fullname, headline, email, addresswithcountry, "
                "profilepic, angel_score, validation_reasons_spanish, validation_reasons_english, "
                "categories_general_es, categories_general_en, categories_strong_es, categories_strong_en, "
                "stage_general_es, stage_general_en, stage_strong_es, stage_strong_en"
            ).gte("angel_score", min_score)
            
            # Add text search for keywords if provided
            if keywords:
                # Create search pattern for multiple keywords
                search_text = " | ".join(keywords)  # OR search
                query = query.text_search("fts", search_text)
            
            result = query.limit(limit).execute()
            
            # Post-process results for relevance scoring
            processed_results = []
            for investor in result.data:
                relevance_score = self._calculate_angel_relevance(
                    investor, keywords, categories, stages
                )
                investor["relevance_score"] = relevance_score
                processed_results.append(investor)
            
            # Sort by relevance and angel score
            processed_results.sort(
                key=lambda x: (x["relevance_score"], x["angel_score"]), 
                reverse=True
            )
            
            logger.info(f"Found {len(processed_results)} angel investors")
            return processed_results
            
        except Exception as e:
            logger.error(f"Angel investor search failed: {e}")
            raise
    
    @log_database_performance("search_investment_funds", "investment_funds")
    async def search_investment_funds(
        self,
        keywords: List[str],
        categories: List[str] = None,
        stages: List[str] = None,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """Search investment funds with keyword matching"""
        try:
            query = self.supabase.table(self.tables["investment_funds"]).select(
                "linkedin, name, contact_email, phone_number, website, short_description, "
                "location_identifiers, category_keywords, stage_keywords"
            ).not_.eq("category_keywords", "[]")  # Exclude empty keywords
            
            result = query.limit(limit * 2).execute()  # Get more to filter better
            
            # Post-process results for relevance scoring
            processed_results = []
            for fund in result.data:
                relevance_score = self._calculate_fund_relevance(
                    fund, keywords, categories, stages
                )
                if relevance_score > 0:  # Only include relevant funds
                    fund["relevance_score"] = relevance_score
                    processed_results.append(fund)
            
            # Sort by relevance
            processed_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Limit results
            processed_results = processed_results[:limit]
            
            logger.info(f"Found {len(processed_results)} investment funds")
            return processed_results
            
        except Exception as e:
            logger.error(f"Investment fund search failed: {e}")
            raise
    
    @log_database_performance("get_fund_employees", "employee_funds") 
    async def get_fund_employees(
        self,
        fund_name: str,
        min_score: float = 5.9,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get employees for a specific fund"""
        try:
            result = self.supabase.table(self.tables["employee_funds"]).select(
                "linkedinurl, fullname, headline, email, addresswithcountry, "
                "profilepic, fund_name, jobtitle, score_combinado, about"
            ).eq("fund_name", fund_name).gte("score_combinado", min_score).limit(limit).execute()
            
            logger.info(f"Found {len(result.data)} employees for fund {fund_name}")
            return result.data
            
        except Exception as e:
            logger.error(f"Fund employee search failed: {e}")
            raise
    
    # ==========================================
    # COMPANY SEARCH OPERATIONS  
    # ==========================================
    
    @log_database_performance("search_companies", "companies")
    async def search_companies(
        self,
        service_keywords: List[str],
        location: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search companies with service keyword matching"""
        try:
            query = self.supabase.table(self.tables["companies"]).select(
                "linkedin, nombre, descripcion_corta, web_empresa, correo, telefono, "
                "sector_categorias, ubicacion_general, keywords_generales, keywords_especificas"
            )
            
            # Add location filter if provided
            if location:
                query = query.ilike("ubicacion_general", f"%{location}%")
            
            result = query.limit(limit * 3).execute()  # Get more to filter better
            
            # Post-process results for relevance scoring
            processed_results = []
            for company in result.data:
                relevance_score = self._calculate_company_relevance(
                    company, service_keywords
                )
                if relevance_score > 0:  # Only include relevant companies
                    company["relevance_score"] = relevance_score
                    processed_results.append(company)
            
            # Sort by relevance
            processed_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Limit results
            processed_results = processed_results[:limit]
            
            logger.info(f"Found {len(processed_results)} companies")
            return processed_results
            
        except Exception as e:
            logger.error(f"Company search failed: {e}")
            raise
    
    # ==========================================
    # CONVERSATION AND MESSAGE OPERATIONS
    # ==========================================
    
    @log_database_performance("save_conversation", "conversations")
    async def save_conversation(
        self,
        conversation_id: str,
        user_id: str,
        project_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save a new conversation"""
        try:
            conversation_data = {
                "id": conversation_id,
                "user_id": user_id,
                "project_id": project_id,
                "title": title,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "active": True
            }
            
            result = self.supabase.table(self.tables["conversations"]).insert(conversation_data).execute()
            
            logger.info(f"Conversation saved: {conversation_id}")
            return result.data[0] if result.data else conversation_data
            
        except Exception as e:
            logger.error(f"Save conversation failed: {e}")
            raise
    
    @log_database_performance("save_message", "messages")
    async def save_message(
        self,
        message_id: str,
        conversation_id: str,
        role: str,
        content: str,
        user_id: str,
        ai_response_data: Optional[Dict[str, Any]] = None,
        search_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save a chat message"""
        try:
            message_data = {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "user_id": user_id,
                "ai_response_data": ai_response_data,
                "search_results": search_results,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table(self.tables["messages"]).insert(message_data).execute()
            
            logger.debug(f"Message saved: {message_id}")
            return result.data[0] if result.data else message_data
            
        except Exception as e:
            logger.error(f"Save message failed: {e}")
            raise
    
    @log_database_performance("get_conversation_history", "messages")
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation message history"""
        try:
            result = self.supabase.table(self.tables["messages"]).select(
                "*"
            ).eq("conversation_id", conversation_id).order("created_at").limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Get conversation history failed: {e}")
            raise
    
    # ==========================================
    # SEARCH RESULTS STORAGE (for CTO outreach)
    # ==========================================
    
    @log_database_performance("save_search_results", "search_results")
    async def save_search_results(
        self,
        search_id: str,
        user_id: str,
        project_id: str,
        search_type: str,
        query_data: Dict[str, Any],
        results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save search results for CTO outreach campaigns"""
        try:
            search_data = {
                "id": search_id,
                "user_id": user_id,
                "project_id": project_id,
                "search_type": search_type,
                "query_data": query_data,
                "results": results,
                "results_count": len(results),
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "used_in_campaigns": False
            }
            
            result = self.supabase.table(self.tables["search_results"]).insert(search_data).execute()
            
            logger.info(f"Search results saved: {search_id} ({len(results)} results)")
            return result.data[0] if result.data else search_data
            
        except Exception as e:
            logger.error(f"Save search results failed: {e}")
            raise
    
    # ==========================================
    # RELEVANCE CALCULATION HELPERS
    # ==========================================
    
    def _calculate_angel_relevance(
        self,
        investor: Dict[str, Any],
        keywords: List[str],
        categories: List[str] = None,
        stages: List[str] = None
    ) -> float:
        """Calculate relevance score for angel investor"""
        score = 0.0
        
        # Base score from angel_score
        score += min(investor.get("angel_score", 0) / 10, 10)  # Max 10 points
        
        # Keyword matching in categories
        all_categories = []
        for field in ["categories_general_es", "categories_general_en", "categories_strong_es", "categories_strong_en"]:
            if investor.get(field):
                all_categories.extend(investor[field])
        
        if keywords:
            keyword_matches = sum(
                1 for keyword in keywords 
                if any(keyword.lower() in cat.lower() for cat in all_categories)
            )
            score += keyword_matches * 5  # 5 points per keyword match
        
        # Stage matching
        all_stages = []
        for field in ["stage_general_es", "stage_general_en", "stage_strong_es", "stage_strong_en"]:
            if investor.get(field):
                all_stages.extend(investor[field])
        
        if stages:
            stage_matches = sum(
                1 for stage in stages
                if any(stage.lower() in st.lower() for st in all_stages)
            )
            score += stage_matches * 3  # 3 points per stage match
        
        return min(score, 100)  # Cap at 100
    
    def _calculate_fund_relevance(
        self,
        fund: Dict[str, Any],
        keywords: List[str],
        categories: List[str] = None,
        stages: List[str] = None
    ) -> float:
        """Calculate relevance score for investment fund"""
        score = 0.0
        
        # Parse category keywords (they're stored as string)
        category_keywords = fund.get("category_keywords", "")
        stage_keywords = fund.get("stage_keywords", "")
        
        if keywords:
            keyword_matches = sum(
                1 for keyword in keywords
                if keyword.lower() in category_keywords.lower()
            )
            score += keyword_matches * 5
        
        if stages:
            stage_matches = sum(
                1 for stage in stages
                if stage.lower() in stage_keywords.lower()
            )
            score += stage_matches * 3
        
        return min(score, 100)
    
    def _calculate_company_relevance(
        self,
        company: Dict[str, Any],
        service_keywords: List[str]
    ) -> float:
        """Calculate relevance score for company"""
        score = 0.0
        
        # Check in general and specific keywords
        general_keywords = company.get("keywords_generales", "")
        specific_keywords = company.get("keywords_especificas", "")
        
        if service_keywords:
            for keyword in service_keywords:
                if keyword.lower() in general_keywords.lower():
                    score += 3
                if keyword.lower() in specific_keywords.lower():
                    score += 5  # Higher weight for specific keywords
        
        return min(score, 100)