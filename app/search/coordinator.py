"""
Search Coordinator - Manages all search engines
"""

import asyncio
from typing import Dict, Any, List, Optional

from app.core.logging import get_logger
from .investor_search import InvestorSearchEngine
from .company_search import CompanySearchEngine

logger = get_logger(__name__)


class SearchCoordinator:
    """
    Coordinates all search engines for 0BullshitIntelligence
    """
    
    def __init__(self):
        self.investor_engine = InvestorSearchEngine()
        self.company_engine = CompanySearchEngine()
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize all search engines"""
        try:
            logger.info("Initializing search engines...")
            
            # Initialize investor search engine
            await self.investor_engine.initialize()
            logger.info("✅ Investor search engine initialized")
            
            # Initialize company search engine
            await self.company_engine.initialize()
            logger.info("✅ Company search engine initialized")
            
            self.is_initialized = True
            logger.info("✅ All search engines initialized successfully")
            
        except Exception as e:
            logger.error(f"Search engine initialization failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check health of all search engines"""
        try:
            if not self.is_initialized:
                return False
            
            investor_health = await self.investor_engine.health_check()
            company_health = await self.company_engine.health_check()
            
            overall_health = investor_health and company_health
            
            if not overall_health:
                logger.warning("Some search engines are unhealthy")
            
            return overall_health
            
        except Exception as e:
            logger.error(f"Search engine health check failed: {e}")
            return False
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics from all search engines"""
        return {
            "investor_engine": self.investor_engine.get_stats(),
            "company_engine": self.company_engine.get_stats(),
            "initialized": self.is_initialized
        }