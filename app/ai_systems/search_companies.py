"""
Company Search System for 0BullshitIntelligence
Searches Companies table based on user needs and extracted keywords
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.manager import database_manager

logger = get_logger(__name__)
settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)


class CompanySearchSystem:
    """
    Intelligent company search system for finding service providers and partners
    """
    
    def __init__(self):
        pass
        
    async def search_companies(self, user_message: str, project_data: Dict[str, Any], 
                              conversation_id: str) -> Dict[str, Any]:
        """
        Search for companies based on user message and project context
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info("Starting company search", 
                       conversation_id=conversation_id,
                       user_message_length=len(user_message))
            
            # Extract keywords from user message
            keywords = await self._extract_search_keywords(user_message, project_data)
            
            # Search companies in database
            results = await self._search_companies_db(keywords)
            
            # Rank and filter results
            final_results = self._rank_results(results, keywords)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info("Company search completed",
                       conversation_id=conversation_id,
                       total_results=len(final_results),
                       keywords_used=keywords,
                       processing_time_ms=round(processing_time, 2))
            
            return {
                'results': final_results,
                'total_found': len(results),
                'keywords_used': keywords,
                'search_metadata': {
                    'processing_time_ms': round(processing_time, 2),
                    'search_timestamp': datetime.utcnow().isoformat(),
                    'conversation_id': conversation_id
                }
            }
            
        except Exception as e:
            logger.error("Company search failed", 
                        conversation_id=conversation_id,
                        error=str(e))
            raise
    
    async def _extract_search_keywords(self, user_message: str, project_data: Dict[str, Any]) -> List[str]:
        """Extract keywords using Gemini for company search"""
        try:
            categories = project_data.get('categories', [])
            stage = project_data.get('stage', '')
            problem_solved = project_data.get('problem_solved', '')
            business_model = project_data.get('business_model', '')
            
            prompt = f"""Extract 10-30 KEYWORDS for finding companies/services based on this user request and project context.

User message: "{user_message}"

Project context:
- Categories: {categories}
- Stage: {stage}  
- Problem: {problem_solved}
- Business model: {business_model}

Extract keywords that describe:
1. Type of service needed (marketing, development, legal, accounting, etc.)
2. Industry/sector keywords
3. Technology keywords (if relevant)
4. Business model related services
5. Stage-specific services (MVP development, scaling, legal setup, etc.)
6. Geographic preferences (if mentioned)

Include both Spanish and English keywords. Use both general terms and specific terms.

Examples:
- User needs marketing help → marketing, marketing digital, digital marketing, publicidad, advertising, SEO, SEM, social media, growth marketing
- User needs development → desarrollo, development, software, programación, programming, web development, mobile app, aplicaciones móviles

Format: Return only keywords separated by commas, no explanations.
Focus on longer, more specific keyword phrases that companies would use in their descriptions."""

            response = await self._call_gemini(prompt)
            
            # Parse keywords from response
            keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
            
            # Remove duplicates while preserving order
            unique_keywords = []
            seen = set()
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in seen and len(kw.strip()) > 2:  # Minimum 3 characters
                    unique_keywords.append(kw.strip())
                    seen.add(kw_lower)
            
            return unique_keywords[:30]  # Limit to 30 keywords max
            
        except Exception as e:
            logger.error("Company keyword extraction failed", error=str(e))
            # Fallback keywords
            return ["servicios", "services", "consultoría", "consulting", "desarrollo", "development"]
    
    async def _search_companies_db(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search Companies table using keywords"""
        try:
            # Simplified search - get sample companies for now
            # TODO: Implement proper keyword filtering
            
            response = database_manager.supabase.table('Companies').select("""
                linkedin,
                nombre,
                descripcion_corta,
                web_empresa,
                correo,
                telefono,
                sector_categorias,
                ubicacion_general
            """).limit(20).execute()
            
            results = []
            for row in response.data:
                results.append({
                    'type': 'company',
                    'linkedin': row.get('linkedin'),
                    'name': row.get('nombre'),
                    'description': row.get('descripcion_corta'),
                    'website': row.get('web_empresa'),
                    'email': row.get('correo'),
                    'phone': row.get('telefono'),
                    'categories': row.get('sector_categorias'),
                    'location': row.get('ubicacion_general'),
                    'keywords_general': '',  # Will be added later
                    'keywords_specific': '',  # Will be added later
                    'relevance_score': 0.0  # Will be calculated in ranking
                })
            
            logger.info(f"Found {len(results)} companies")
            return results
            
        except Exception as e:
            logger.error("Company database search failed", error=str(e))
            return []
    
    def _rank_results(self, results: List[Dict[str, Any]], search_keywords: List[str]) -> List[Dict[str, Any]]:
        """Rank company results by relevance to search keywords"""
        try:
            for company in results:
                score = 0.0
                
                # Get company text fields for matching
                company_text = []
                if company.get('keywords_general'):
                    company_text.append(company['keywords_general'].lower())
                if company.get('keywords_specific'):
                    company_text.append(company['keywords_specific'].lower())
                if company.get('categories'):
                    company_text.append(company['categories'].lower())
                if company.get('description'):
                    company_text.append(company['description'].lower())
                if company.get('name'):
                    company_text.append(company['name'].lower())
                
                company_content = ' '.join(company_text)
                
                # Score based on keyword matches
                for keyword in search_keywords:
                    keyword_lower = keyword.lower()
                    
                    # Different weights for different types of matches
                    if keyword_lower in company.get('keywords_specific', '').lower():
                        score += 3.0  # High weight for specific keywords
                    elif keyword_lower in company.get('keywords_general', '').lower():
                        score += 2.0  # Medium weight for general keywords
                    elif keyword_lower in company.get('categories', '').lower():
                        score += 1.5  # Medium weight for categories
                    elif keyword_lower in company.get('name', '').lower():
                        score += 1.0  # Lower weight for name matches
                    elif keyword_lower in company.get('description', '').lower():
                        score += 0.5  # Lower weight for description matches
                
                company['relevance_score'] = score
            
            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Return top 20 results with minimum score
            filtered_results = [r for r in results if r['relevance_score'] > 0]
            return filtered_results[:20]
            
        except Exception as e:
            logger.error("Company ranking failed", error=str(e))
            return results[:20]  # Return first 20 without ranking
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error("Gemini call failed", error=str(e))
            return ""


# Global instance
company_search_system = CompanySearchSystem()