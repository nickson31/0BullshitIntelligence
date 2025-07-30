"""
Company Search Engine - Search for B2B Service Companies
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.database import database_manager
from app.models import UserContext

logger = get_logger(__name__)


class CompanySearchEngine:
    """
    Search engine for finding relevant B2B service companies
    
    Helps users find companies that can provide specific services
    based on their business needs.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.search_count = 0
        self.last_search_time = None
    
    async def initialize(self):
        """Initialize the company search engine"""
        try:
            # Verify database connection
            if not database_manager.is_initialized:
                raise Exception("Database manager not initialized")
            
            # Test basic search functionality
            await self._test_search_functionality()
            
            self.is_initialized = True
            logger.info("Company search engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Company search engine initialization failed: {e}")
            raise
    
    async def _test_search_functionality(self):
        """Test basic search functionality"""
        try:
            # Test company search
            companies = await database_manager.search_companies(
                service_keywords=["test"],
                limit=1
            )
            
            logger.debug(f"Company search test successful - Found: {len(companies)} companies")
            
        except Exception as e:
            logger.error(f"Company search functionality test failed: {e}")
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
            logger.error(f"Company search engine health check failed: {e}")
            return False
    
    async def search_companies(
        self,
        service_keywords: List[str],
        service_type: Optional[str] = None,
        location_preference: Optional[str] = None,
        project_id: Optional[str] = None,
        user_context: Optional[UserContext] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search for relevant B2B service companies
        
        Args:
            service_keywords: Keywords describing the service needed
            service_type: Type of service (marketing, legal, tech, etc.)
            location_preference: Preferred location for the company
            project_id: Associated project ID
            user_context: User context for personalization
            limit: Maximum number of results
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            self.search_count += 1
            self.last_search_time = datetime.utcnow()
            
            logger.info(
                "Starting company search",
                service_keywords=service_keywords,
                service_type=service_type,
                location_preference=location_preference,
                limit=limit
            )
            
            # Validate inputs
            if not service_keywords:
                raise ValueError("Service keywords are required for company search")
            
            # Enhance keywords based on service type
            enhanced_keywords = self._enhance_keywords(service_keywords, service_type)
            
            # Execute search
            companies = await database_manager.search_companies(
                service_keywords=enhanced_keywords,
                location=location_preference,
                limit=limit
            )
            
            # Process and enhance results
            processed_results = self._process_search_results(
                companies, service_keywords, service_type
            )
            
            # Limit final results
            final_results = processed_results[:limit]
            
            search_metadata = {
                "search_id": str(uuid.uuid4()),
                "total_results": len(final_results),
                "companies_found": len(companies),
                "search_time": datetime.utcnow().isoformat(),
                "keywords_used": enhanced_keywords,
                "service_type": service_type,
                "location_preference": location_preference,
                "filters_applied": {
                    "service_keywords": service_keywords,
                    "enhanced_keywords": enhanced_keywords
                }
            }
            
            logger.info(
                "Company search completed",
                total_results=len(final_results),
                companies_found=len(companies)
            )
            
            return {
                "results": final_results,
                "metadata": search_metadata,
                "search_type": "companies",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Company search failed: {e}")
            raise
    
    async def test_search(
        self,
        service_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Test search with sample data (debug mode only)"""
        test_keywords = service_keywords or ["marketing", "digital"]
        
        return await self.search_companies(
            service_keywords=test_keywords,
            service_type="marketing",
            limit=3
        )
    
    def _enhance_keywords(
        self,
        service_keywords: List[str],
        service_type: Optional[str] = None
    ) -> List[str]:
        """Enhance keywords based on service type and domain knowledge"""
        
        enhanced = service_keywords.copy()
        
        # Add related keywords based on service type
        service_expansions = {
            "marketing": ["digital marketing", "seo", "sem", "social media", "content marketing"],
            "legal": ["legal services", "abogados", "asesoría legal", "compliance"],
            "technology": ["desarrollo", "software", "app development", "tech"],
            "design": ["diseño", "ui/ux", "branding", "graphic design"],
            "consulting": ["consultoría", "strategy", "business consulting"],
            "finance": ["contabilidad", "accounting", "financial services"],
            "hr": ["recursos humanos", "human resources", "recruitment"]
        }
        
        if service_type and service_type.lower() in service_expansions:
            enhanced.extend(service_expansions[service_type.lower()])
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for keyword in enhanced:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                result.append(keyword)
        
        return result
    
    def _process_search_results(
        self,
        companies: List[Dict[str, Any]],
        service_keywords: List[str],
        service_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Process and enhance search results"""
        
        processed_results = []
        
        for company in companies:
            # Create standardized result format
            result = {
                **company,
                "company_type": "service_provider",
                "source": "companies",
                "display_name": company.get("nombre", "Unknown Company"),
                "linkedin_url": company.get("linkedin"),
                "website": company.get("web_empresa"),
                "contact_email": company.get("correo"),
                "phone": company.get("telefono"),
                "location": company.get("ubicacion_general", "Unknown"),
                "description": company.get("descripcion_corta", ""),
                "sector": company.get("sector_categorias", ""),
                "relevance_score": company.get("relevance_score", 0),
                "service_match": self._calculate_service_match(company, service_keywords),
                "keywords": self._extract_company_keywords(company),
                "services": self._extract_services(company)
            }
            
            processed_results.append(result)
        
        # Sort by relevance and service match
        processed_results.sort(
            key=lambda x: (x["relevance_score"], x["service_match"]),
            reverse=True
        )
        
        return processed_results
    
    def _calculate_service_match(
        self,
        company: Dict[str, Any],
        service_keywords: List[str]
    ) -> float:
        """Calculate how well company services match the requested keywords"""
        
        # Get company keywords
        general_keywords = company.get("keywords_generales", "").lower()
        specific_keywords = company.get("keywords_especificas", "").lower()
        sector = company.get("sector_categorias", "").lower()
        
        match_score = 0.0
        total_keywords = len(service_keywords)
        
        if total_keywords == 0:
            return 0.0
        
        for keyword in service_keywords:
            keyword_lower = keyword.lower()
            
            # Check in different fields with different weights
            if keyword_lower in specific_keywords:
                match_score += 3.0  # High weight for specific keywords
            elif keyword_lower in general_keywords:
                match_score += 2.0  # Medium weight for general keywords
            elif keyword_lower in sector:
                match_score += 1.0  # Low weight for sector match
        
        # Normalize score
        max_possible_score = total_keywords * 3.0
        normalized_score = (match_score / max_possible_score) * 100
        
        return min(normalized_score, 100)
    
    def _extract_company_keywords(self, company: Dict[str, Any]) -> List[str]:
        """Extract all keywords from company data"""
        
        keywords = []
        
        # Extract from general keywords
        general = company.get("keywords_generales", "")
        if general:
            # Simple extraction - split by comma
            keywords.extend([k.strip() for k in general.split(",") if k.strip()])
        
        # Extract from specific keywords
        specific = company.get("keywords_especificas", "")
        if specific:
            keywords.extend([k.strip() for k in specific.split(",") if k.strip()])
        
        # Limit and clean
        unique_keywords = list(set(keywords))[:20]  # Limit to 20 unique keywords
        
        return unique_keywords
    
    def _extract_services(self, company: Dict[str, Any]) -> List[str]:
        """Extract services offered by the company"""
        
        services = []
        
        # Extract from sector categories
        sector = company.get("sector_categorias", "")
        if sector:
            services.extend([s.strip() for s in sector.split(",") if s.strip()])
        
        # Extract key services from keywords
        specific_keywords = company.get("keywords_especificas", "")
        if specific_keywords:
            # Look for service patterns in specific keywords
            service_patterns = [
                "marketing", "desarrollo", "diseño", "consulting", "legal",
                "contabilidad", "seo", "sem", "social media", "branding"
            ]
            
            for pattern in service_patterns:
                if pattern in specific_keywords.lower():
                    services.append(pattern.title())
        
        # Remove duplicates and limit
        unique_services = list(set(services))[:10]
        
        return unique_services
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            "initialized": self.is_initialized,
            "search_count": self.search_count,
            "last_search_time": self.last_search_time.isoformat() if self.last_search_time else None
        }


# Create singleton instance for import
company_search_engine = CompanySearchEngine()