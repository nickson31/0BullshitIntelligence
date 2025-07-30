"""
Investor Search System for 0BullshitIntelligence
Searches Angel Investors and Investment Funds based on project data and completeness
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import google.generativeai as genai
from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.manager import database_manager

logger = get_logger(__name__)
settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)


class InvestorSearchSystem:
    """
    Intelligent investor search system that combines Angel Investors and Investment Funds
    """
    
    def __init__(self):
        self.min_completeness_score = 50.0  # Minimum 50% completeness required
        self.min_angel_score = 40.0  # Minimum angel score to show results
        self.min_employee_score = 5.9  # Minimum employee score to show
        
    async def can_search_investors(self, project_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if project has minimum 50% completeness for investor search
        Requires: 25% stage + 25% categories
        """
        try:
            completeness_score = project_data.get('completeness_score', 0.0)
            stage = project_data.get('stage')
            categories = project_data.get('categories', [])
            
            # Check minimum completeness
            if completeness_score < self.min_completeness_score:
                missing_stage = not stage
                missing_categories = not categories or len(categories) == 0
                
                missing_info = []
                if missing_stage:
                    missing_info.append("etapa del proyecto")
                if missing_categories:
                    missing_info.append("categorías del negocio")
                    
                return False, f"Necesitas al menos 50% de completitud. Falta: {', '.join(missing_info)}"
            
            return True, "Proyecto listo para búsqueda de inversores"
            
        except Exception as e:
            logger.error("Error checking investor search eligibility", error=str(e))
            return False, "Error al verificar elegibilidad para búsqueda"
    
    async def search_investors(self, user_message: str, project_data: Dict[str, Any], 
                              conversation_id: str) -> Dict[str, Any]:
        """
        Search for investors (Angels + Funds) based on user message and project data
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info("Starting investor search", 
                       conversation_id=conversation_id,
                       project_categories=project_data.get('categories', []),
                       project_stage=project_data.get('stage'))
            
            # Extract keywords from user message and project data
            keywords = await self._extract_search_keywords(user_message, project_data)
            
            # Determine stage-based search weights
            stage_weights = self._calculate_stage_weights(project_data.get('stage'))
            
            # Search angels and funds in parallel
            angels_task = self._search_angels(keywords, stage_weights['angels'])
            funds_task = self._search_funds(keywords, stage_weights['funds'])
            
            angels_results, funds_results = await asyncio.gather(angels_task, funds_task)
            
            # Get fund employees for the funds we found
            fund_employees = await self._get_fund_employees(funds_results)
            
            # Combine and rank results
            final_results = self._combine_results(angels_results, funds_results, fund_employees, stage_weights)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info("Investor search completed",
                       conversation_id=conversation_id,
                       total_results=len(final_results),
                       angels_found=len(angels_results),
                       funds_found=len(funds_results),
                       processing_time_ms=round(processing_time, 2))
            
            return {
                'results': final_results,
                'total_angels': len(angels_results),
                'total_funds': len(funds_results),
                'keywords_used': keywords,
                'stage_weights': stage_weights,
                'search_metadata': {
                    'processing_time_ms': round(processing_time, 2),
                    'search_timestamp': datetime.utcnow().isoformat(),
                    'conversation_id': conversation_id
                }
            }
            
        except Exception as e:
            logger.error("Investor search failed", 
                        conversation_id=conversation_id,
                        error=str(e))
            raise
    
    async def _extract_search_keywords(self, user_message: str, project_data: Dict[str, Any]) -> List[str]:
        """Extract keywords using Gemini for investor search"""
        try:
            categories = project_data.get('categories', [])
            stage = project_data.get('stage', '')
            problem_solved = project_data.get('problem_solved', '')
            business_model = project_data.get('business_model', '')
            
            prompt = f"""Extract KEYWORDS (not phrases) for investor search from this user message and project data.

User message: "{user_message}"

Project context:
- Categories: {categories}
- Stage: {stage}  
- Problem: {problem_solved}
- Business model: {business_model}

Extract 10-20 relevant KEYWORDS (single words or 2-word phrases max) in both Spanish and English that investors would use to categorize investments.

Focus on:
- Industry/sector keywords
- Technology keywords  
- Business model keywords
- Stage keywords
- Geographic keywords if mentioned

Format: Return only keywords separated by commas, no explanations.
Example: fintech, pagos, payments, SaaS, B2B, startup, early stage, España, tecnología, artificial intelligence"""

            response = await self._call_gemini(prompt)
            
            # Parse keywords from response
            keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
            
            # Add project categories and stage as keywords
            if categories:
                keywords.extend(categories)
            if stage:
                keywords.append(stage)
                
            # Remove duplicates while preserving order
            unique_keywords = []
            seen = set()
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in seen:
                    unique_keywords.append(kw)
                    seen.add(kw_lower)
            
            return unique_keywords[:25]  # Limit to 25 keywords max
            
        except Exception as e:
            logger.error("Keyword extraction failed", error=str(e))
            # Fallback to project data only
            keywords = []
            if project_data.get('categories'):
                keywords.extend(project_data['categories'])
            if project_data.get('stage'):
                keywords.append(project_data['stage'])
            return keywords
    
    def _calculate_stage_weights(self, stage: Optional[str]) -> Dict[str, float]:
        """Calculate search weights based on project stage"""
        if not stage:
            return {'angels': 0.6, 'funds': 0.4}  # Default: more angels
            
        stage_lower = stage.lower()
        
        # Early stage: more angels
        if any(term in stage_lower for term in ['pre-seed', 'preseed', 'idea', 'prototype', 'mvp']):
            return {'angels': 0.8, 'funds': 0.2}
        
        # Seed stage: balanced
        elif any(term in stage_lower for term in ['seed', 'semilla']):
            return {'angels': 0.6, 'funds': 0.4}
        
        # Later stages: more funds
        elif any(term in stage_lower for term in ['series a', 'series b', 'serie a', 'serie b', 'growth', 'expansion']):
            return {'angels': 0.3, 'funds': 0.7}
            
        # Very late stage: mostly funds
        elif any(term in stage_lower for term in ['series c', 'serie c', 'late stage', 'mezzanine', 'ipo']):
            return {'angels': 0.1, 'funds': 0.9}
        
        return {'angels': 0.6, 'funds': 0.4}  # Default
    
    async def _search_angels(self, keywords: List[str], weight: float) -> List[Dict[str, Any]]:
        """Search Angel_Investors table"""
        try:
            # Simplified search - get top angels by score for now
            # TODO: Implement keyword filtering once we have proper search setup
            
            response = database_manager.supabase.table('Angel_Investors').select("""
                linkedinUrl,
                fullName,
                headline,
                email,
                about,
                addressWithCountry,
                profilePic,
                angel_score,
                validation_reasons_spanish,
                validation_reasons_english
            """).gte('angel_score', self.min_angel_score).order('angel_score', desc=True).limit(15).execute()
            
            results = []
            for row in response.data:
                results.append({
                    'type': 'angel',
                    'linkedin_url': row.get('linkedinUrl'),
                    'full_name': row.get('fullName'),
                    'headline': row.get('headline'),
                    'email': row.get('email'),
                    'about': row.get('about'),
                    'location': row.get('addressWithCountry'),
                    'profile_pic': row.get('profilePic'),
                    'score': row.get('angel_score'),
                    'validation_reasons_spanish': row.get('validation_reasons_spanish'),
                    'validation_reasons_english': row.get('validation_reasons_english'),
                    'search_weight': weight
                })
            
            logger.info(f"Found {len(results)} angel investors")
            return results
            
        except Exception as e:
            logger.error("Angel search failed", error=str(e))
            return []
    
    async def _search_funds(self, keywords: List[str], weight: float) -> List[Dict[str, Any]]:
        """Search Investment_Funds table"""
        try:
            # Simplified search - get funds for now
            # TODO: Implement keyword filtering and proper column handling
            
            response = database_manager.supabase.table('Investment_Funds').select("""
                name,
                short_description,
                contact_email,
                phone_number
            """).limit(15).execute()
            
            results = []
            for row in response.data:
                results.append({
                    'type': 'fund',
                    'linkedin_url': '',  # Will be added later
                    'name': row.get('name'),
                    'description': row.get('short_description'),
                    'email': row.get('contact_email'),
                    'phone': row.get('phone_number'),
                    'website': '',  # Will be added later
                    'location': '',  # Will be added later
                    'category_keywords': '',
                    'stage_keywords': '',
                    'search_weight': weight
                })
            
            logger.info(f"Found {len(results)} investment funds")
            return results
            
        except Exception as e:
            logger.error("Fund search failed", error=str(e))
            return []
    
    async def _get_fund_employees(self, funds_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get employees for the found funds"""
        try:
            # Simplified for now - return empty list
            # TODO: Implement employee search once fund names are available
            return []
            
        except Exception as e:
            logger.error("Employee search failed", error=str(e))
            return []
    
    def _combine_results(self, angels: List[Dict], funds: List[Dict], 
                        employees: List[Dict], weights: Dict[str, float]) -> List[Dict[str, Any]]:
        """Combine and rank all investor results"""
        all_results = []
        
        # Add angels with weighted scores
        for angel in angels:
            angel['final_score'] = angel['score'] * weights['angels']
            all_results.append(angel)
        
        # Add funds with employees
        for fund in funds:
            fund_employees = [emp for emp in employees if emp['fund_name'] == fund['name']]
            fund['employees'] = fund_employees[:5]  # Max 5 employees per fund
            
            # Calculate fund score based on number of quality employees
            base_score = 50.0  # Base score for funds
            employee_bonus = len(fund_employees) * 5  # Bonus for having employees
            fund['score'] = min(base_score + employee_bonus, 100.0)
            fund['final_score'] = fund['score'] * weights['funds']
            
            all_results.append(fund)
        
        # Sort by final score
        all_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Return top 15 results
        return all_results[:15]
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error("Gemini call failed", error=str(e))
            return ""


# Global instance
investor_search_system = InvestorSearchSystem()