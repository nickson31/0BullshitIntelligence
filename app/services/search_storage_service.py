"""
Search Storage Service - Stores search results for CTO outreach campaigns
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.database import database_manager

logger = get_logger(__name__)


class SearchStorageService:
    """
    Service for storing and retrieving search results for outreach campaigns
    """
    
    def __init__(self):
        self.stored_searches = 0
        self.last_storage_time = None
    
    async def save_investor_search_results(
        self,
        search_results: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Save investor search results for CTO outreach campaigns"""
        
        try:
            search_id = str(uuid.uuid4())
            
            # Extract relevant data for storage
            results = search_results.get("results", [])
            metadata = search_results.get("metadata", {})
            
            # Prepare query data
            query_data = {
                "keywords": metadata.get("keywords_used", []),
                "filters": metadata.get("filters_applied", {}),
                "search_distribution": metadata.get("search_distribution", {}),
                "search_type": "investors"
            }
            
            # Store in database
            stored_result = await database_manager.save_search_results(
                search_id=search_id,
                user_id=user_id,
                project_id=project_id,
                search_type="investors",
                query_data=query_data,
                results=results,
                metadata=metadata
            )
            
            self.stored_searches += 1
            self.last_storage_time = datetime.utcnow()
            
            logger.info(
                "Investor search results saved",
                search_id=search_id,
                results_count=len(results),
                user_id=user_id
            )
            
            return stored_result
            
        except Exception as e:
            logger.error(f"Failed to save investor search results: {e}")
            raise
    
    async def save_company_search_results(
        self,
        search_results: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Save company search results for future reference"""
        
        try:
            search_id = str(uuid.uuid4())
            
            # Extract relevant data for storage
            results = search_results.get("results", [])
            metadata = search_results.get("metadata", {})
            
            # Prepare query data
            query_data = {
                "service_keywords": metadata.get("keywords_used", []),
                "service_type": metadata.get("service_type"),
                "location_preference": metadata.get("location_preference"),
                "search_type": "companies"
            }
            
            # Store in database
            stored_result = await database_manager.save_search_results(
                search_id=search_id,
                user_id=user_id,
                project_id=project_id,
                search_type="companies",
                query_data=query_data,
                results=results,
                metadata=metadata
            )
            
            self.stored_searches += 1
            self.last_storage_time = datetime.utcnow()
            
            logger.info(
                "Company search results saved",
                search_id=search_id,
                results_count=len(results),
                user_id=user_id
            )
            
            return stored_result
            
        except Exception as e:
            logger.error(f"Failed to save company search results: {e}")
            raise
    
    async def get_saved_investor_searches(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's saved investor search results"""
        
        try:
            # This would need to be implemented in database_manager
            # For now, return empty list
            logger.info(f"Getting saved investor searches for user {user_id}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to retrieve saved investor searches: {e}")
            raise
    
    async def get_saved_company_searches(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's saved company search results"""
        
        try:
            # This would need to be implemented in database_manager
            # For now, return empty list
            logger.info(f"Getting saved company searches for user {user_id}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to retrieve saved company searches: {e}")
            raise
    
    async def mark_search_used_in_campaign(
        self,
        search_id: str,
        campaign_id: str
    ):
        """Mark search results as used in outreach campaign"""
        
        try:
            # This would update the search record to indicate it was used
            logger.info(f"Marking search {search_id} as used in campaign {campaign_id}")
            
        except Exception as e:
            logger.error(f"Failed to mark search as used: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "stored_searches": self.stored_searches,
            "last_storage_time": self.last_storage_time.isoformat() if self.last_storage_time else None
        }


# Create singleton instance
search_storage_service = SearchStorageService()