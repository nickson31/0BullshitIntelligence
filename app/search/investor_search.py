"""
Investor Search Engine - Search for Angels and Investment Funds
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from app.core.config import settings
from app.core.logging import get_logger
from app.database import database_manager
from app.models import UserContext

logger = get_logger(__name__)


class InvestorSearchEngine:
    """
    Search engine for finding relevant investors (Angels + Funds)
    
    Implements hybrid search combining Angels and Investment Funds
    with intelligent scoring and filtering.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.search_count = 0
        self.last_search_time = None
    
    async def initialize(self):
        """Initialize the investor search engine"""
        try:
            # Verify database connection
            if not database_manager.is_initialized:
                raise Exception("Database manager not initialized")
            
            # Test basic search functionality
            await self._test_search_functionality()
            
            self.is_initialized = True
            logger.info("Investor search engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Investor search engine initialization failed: {e}")
            raise
    
    async def _test_search_functionality(self):
        """Test basic search functionality"""
        try:
            # Test angel investor search
            angels = await database_manager.search_angel_investors(
                keywords=["test"],
                limit=1
            )
            
            # Test fund search  
            funds = await database_manager.search_investment_funds(
                keywords=["test"],
                limit=1
            )
            
            logger.debug(f"Search test successful - Angels: {len(angels)}, Funds: {len(funds)}")
            
        except Exception as e:
            logger.error(f"Search functionality test failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check engine health"""
        try:
            if not self.is_initialized:
                return False
            
            # Quick health check
            await self._test_search_functionality()
            return True
            
        except Exception as e:
            logger.error(f"Investor search engine health check failed: {e}")
            return False
    
    async def search_investors(
        self,
        keywords: List[str],
        stage_keywords: List[str] = None,
        categories: List[str] = None,
        project_id: Optional[str] = None,
        user_context: Optional[UserContext] = None,
        limit: int = 15
    ) -> Dict[str, Any]:
        """
        Search for relevant investors using hybrid approach
        
        Returns mixed results of Angels and Investment Funds
        weighted by project stage and context.
        """
        try:
            self.search_count += 1
            self.last_search_time = datetime.utcnow()
            
            logger.info(
                "Starting investor search",
                keywords=keywords,
                stage_keywords=stage_keywords,
                categories=categories,
                limit=limit
            )
            
            # Validate inputs
            if not keywords and not stage_keywords and not categories:
                raise ValueError("At least one search parameter is required")
            
            # Determine search distribution based on stage
            angel_ratio, fund_ratio = self._calculate_search_distribution(
                stage_keywords, user_context
            )
            
            angel_limit = max(1, int(limit * angel_ratio))
            fund_limit = max(1, int(limit * fund_ratio))
            
            logger.debug(f"Search distribution - Angels: {angel_limit}, Funds: {fund_limit}")
            
            # Execute parallel searches
            angel_task = database_manager.search_angel_investors(
                keywords=keywords or [],
                categories=categories or [],
                stages=stage_keywords or [],
                min_score=settings.min_angel_score,
                limit=angel_limit
            )
            
            fund_task = database_manager.search_investment_funds(
                keywords=keywords or [],
                categories=categories or [],
                stages=stage_keywords or [],
                limit=fund_limit
            )
            
            # Wait for both searches to complete
            angels, funds = await asyncio.gather(angel_task, fund_task)
            
            # Combine and process results
            combined_results = self._combine_search_results(
                angels, funds, keywords, stage_keywords, categories
            )
            
            # Limit final results
            final_results = combined_results[:limit]
            
            search_metadata = {
                "search_id": str(uuid.uuid4()),
                "total_results": len(final_results),
                "angels_found": len(angels),
                "funds_found": len(funds),
                "search_distribution": {"angels": angel_ratio, "funds": fund_ratio},
                "search_time": datetime.utcnow().isoformat(),
                "keywords_used": keywords or [],
                "filters_applied": {
                    "stage_keywords": stage_keywords or [],
                    "categories": categories or [],
                    "min_angel_score": settings.min_angel_score
                }
            }
            
            logger.info(
                "Investor search completed",
                total_results=len(final_results),
                angels=len(angels),
                funds=len(funds)
            )
            
            return {
                "results": final_results,
                "metadata": search_metadata,
                "search_type": "investors",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Investor search failed: {e}")
            raise
    
    async def get_fund_employees(
        self,
        fund_id: str,
        min_score: float = None
    ) -> List[Dict[str, Any]]:
        """Get employees for a specific investment fund"""
        try:
            min_score = min_score or settings.min_employee_score
            
            # Extract fund name from fund result (this would need fund lookup)
            # For now, assume fund_id is the fund name
            employees = await database_manager.get_fund_employees(
                fund_name=fund_id,
                min_score=min_score
            )
            
            return employees
            
        except Exception as e:
            logger.error(f"Fund employee search failed: {e}")
            raise
    
    async def test_search(
        self,
        keywords: List[str] = None,
        stage: str = None
    ) -> Dict[str, Any]:
        """Test search with sample data (debug mode only)"""
        test_keywords = keywords or ["fintech", "saas"]
        test_stages = [stage] if stage else ["seed", "series_a"]
        
        return await self.search_investors(
            keywords=test_keywords,
            stage_keywords=test_stages,
            limit=5
        )
    
    def _calculate_search_distribution(
        self,
        stage_keywords: List[str] = None,
        user_context: Optional[UserContext] = None
    ) -> tuple[float, float]:
        """
        Calculate distribution between Angels and Funds based on stage
        
        Early stage: More Angels (70/30)
        Later stage: More Funds (30/70)
        Unknown: Balanced (50/50)
        """
        
        if not stage_keywords:
            return 0.5, 0.5  # Balanced when no stage info
        
        # Define stage mapping
        early_stages = ["idea", "prototype", "mvp", "pre-seed", "seed"]
        later_stages = ["series_a", "series_b", "series_c", "growth", "scale"]
        
        early_count = sum(1 for stage in stage_keywords if any(early in stage.lower() for early in early_stages))
        later_count = sum(1 for stage in stage_keywords if any(later in stage.lower() for later in later_stages))
        
        if early_count > later_count:
            return 0.7, 0.3  # More angels for early stage
        elif later_count > early_count:
            return 0.3, 0.7  # More funds for later stage
        else:
            return 0.5, 0.5  # Balanced when mixed or unclear
    
    def _combine_search_results(
        self,
        angels: List[Dict[str, Any]],
        funds: List[Dict[str, Any]],
        keywords: List[str] = None,
        stage_keywords: List[str] = None,
        categories: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Combine and score results from both searches"""
        
        combined = []
        
        # Process angels
        for angel in angels:
            result = {
                **angel,
                "investor_type": "angel",
                "source": "angel_investors",
                "display_name": angel.get("fullname", "Unknown Angel"),
                "linkedin_url": angel.get("linkedinurl"),
                "contact_email": angel.get("email"),
                "location": angel.get("addresswithcountry"),
                "profile_image": angel.get("profilepic"),
                "score": angel.get("angel_score", 0),
                "relevance_score": angel.get("relevance_score", 0),
                "description": angel.get("validation_reasons_spanish") or angel.get("validation_reasons_english"),
                "categories": self._extract_categories(angel),
                "stages": self._extract_stages(angel)
            }
            combined.append(result)
        
        # Process funds
        for fund in funds:
            result = {
                **fund,
                "investor_type": "fund",
                "source": "investment_funds",
                "display_name": fund.get("name", "Unknown Fund"),
                "linkedin_url": fund.get("linkedin"),
                "contact_email": fund.get("contact_email"),
                "website": fund.get("website"),
                "phone": fund.get("phone_number"),
                "location": self._format_fund_location(fund.get("location_identifiers")),
                "score": fund.get("relevance_score", 0),
                "relevance_score": fund.get("relevance_score", 0),
                "description": fund.get("short_description"),
                "categories": self._extract_fund_categories(fund.get("category_keywords", "")),
                "stages": self._extract_fund_stages(fund.get("stage_keywords", ""))
            }
            combined.append(result)
        
        # Sort by combined score (relevance + type-specific score)
        combined.sort(
            key=lambda x: (x["relevance_score"], x["score"]),
            reverse=True
        )
        
        return combined
    
    def _extract_categories(self, angel: Dict[str, Any]) -> List[str]:
        """Extract categories from angel investor data"""
        categories = []
        
        for field in ["categories_general_es", "categories_general_en", "categories_strong_es", "categories_strong_en"]:
            if angel.get(field):
                categories.extend(angel[field])
        
        return list(set(categories))  # Remove duplicates
    
    def _extract_stages(self, angel: Dict[str, Any]) -> List[str]:
        """Extract stages from angel investor data"""
        stages = []
        
        for field in ["stage_general_es", "stage_general_en", "stage_strong_es", "stage_strong_en"]:
            if angel.get(field):
                stages.extend(angel[field])
        
        return list(set(stages))  # Remove duplicates
    
    def _extract_fund_categories(self, category_keywords: str) -> List[str]:
        """Extract categories from fund category keywords string"""
        if not category_keywords or category_keywords == "[]":
            return []
        
        # Parse the category keywords (they're stored as a string)
        # This is a simplified parser - might need more sophisticated parsing
        import re
        categories = re.findall(r"'([^']+)'", category_keywords)
        return categories[:10]  # Limit to avoid too many categories
    
    def _extract_fund_stages(self, stage_keywords: str) -> List[str]:
        """Extract stages from fund stage keywords string"""
        if not stage_keywords or stage_keywords == "[]":
            return []
        
        import re
        stages = re.findall(r"'([^']+)'", stage_keywords)
        return stages[:10]  # Limit to avoid too many stages
    
    def _format_fund_location(self, location_identifiers: Any) -> str:
        """Format fund location from location identifiers"""
        if not location_identifiers:
            return "Unknown"
        
        # location_identifiers might be a list or dict
        if isinstance(location_identifiers, list) and location_identifiers:
            return ", ".join(str(loc) for loc in location_identifiers[:3])  # Take first 3
        elif isinstance(location_identifiers, dict):
            return str(location_identifiers.get("value", "Unknown"))
        else:
            return str(location_identifiers)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            "initialized": self.is_initialized,
            "search_count": self.search_count,
            "last_search_time": self.last_search_time.isoformat() if self.last_search_time else None
        }


# Create singleton instance for import
investor_search_engine = InvestorSearchEngine()