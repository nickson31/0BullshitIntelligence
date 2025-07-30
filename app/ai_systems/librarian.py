"""
Librarian System for 0BullshitIntelligence.
Uses Gemini to extract and maintain project data from conversations.
Provides memory and context continuity without user registration.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.user import ProjectData, ProjectMetrics, TeamInfo, FundingInfo
from app.models.ai_systems import LibrarianUpdate
import google.generativeai as genai

logger = get_logger(__name__)
settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)


class LibrarianBot:
    """
    Intelligent conversation memory system using Gemini.
    Extracts and maintains project data for session continuity.
    """
    
    def __init__(self):
        self.logger = logger
    
    async def process_conversation_update(
        self,
        session_id: str,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        current_project_data: Optional[ProjectData] = None
    ) -> Dict[str, Any]:
        """
        Process conversation and extract/update project data
        Returns updated project data and completeness score
        """
        
        try:
            self.logger.info("Librarian processing conversation",
                           session_id=session_id,
                           conversation_id=conversation_id,
                           user_message_length=len(user_message))
            
            # Extract new information from conversation
            extracted_data = await self._extract_project_info(
                user_message, assistant_response, current_project_data
            )
            
            # Merge with existing data
            updated_data = self._merge_project_data(
                current_project_data, extracted_data
            )
            
            # Calculate completeness score
            completeness_score = self._calculate_completeness(updated_data)
            
            # Create librarian update record
            librarian_update = LibrarianUpdate(
                conversation_id=conversation_id,
                project_id=uuid4(),  # Session-based project ID
                user_message=user_message[:500],  # Truncated
                assistant_response=assistant_response[:500],  # Truncated
                context_extracted=extracted_data,
                relevance_score=self._calculate_relevance(extracted_data),
                success=True
            )
            
            self.logger.info("Librarian processing completed",
                           session_id=session_id,
                           completeness_score=completeness_score,
                           data_extracted=bool(extracted_data))
            
            return {
                'project_data': updated_data,
                'completeness_score': completeness_score,
                'librarian_update': librarian_update,
                'extracted_fields': list(extracted_data.keys()) if extracted_data else []
            }
            
        except Exception as e:
            self.logger.error("Librarian processing failed",
                            session_id=session_id,
                            error=str(e))
            
            # Return safe fallback
            return {
                'project_data': current_project_data,
                'completeness_score': 0.0,
                'librarian_update': None,
                'extracted_fields': []
            }
    
    async def _extract_project_info(
        self,
        user_message: str,
        assistant_response: str,
        current_data: Optional[ProjectData] = None
    ) -> Dict[str, Any]:
        """Use Gemini to extract structured project information"""
        
        current_info = ""
        if current_data:
            current_info = f"""
Current project info we already have:
- Categories: {current_data.categories}
- Stage: {current_data.stage}
- Problem: {current_data.problem_solved}
- Solution: {current_data.solution}
- Target market: {current_data.target_market}
- Business model: {current_data.business_model}
"""
        
        prompt = f"""
You are an expert data extraction system for a business intelligence platform.

Extract structured business information from this conversation:

USER: "{user_message}"
ASSISTANT: "{assistant_response}"

{current_info}

Extract ONLY NEW information mentioned in this conversation. Don't repeat existing data.

Look for these fields (leave empty if not mentioned):

BASIC INFO:
- categories: [fintech, healthtech, edtech, saas, marketplace, ai, etc.]
- stage: [idea, prototype, mvp, early_revenue, growth, scale]
- problem_solved: What problem does the business solve?
- solution: How do they solve it?
- target_market: Who are their customers?
- business_model: How do they make money?

METRICS (if mentioned):
- revenue: Current revenue/ARR/MRR
- users: Number of users/customers
- growth_rate: Growth metrics
- team_size: Size of team

TEAM INFO (if mentioned):
- founders: Founder names/backgrounds
- experience: Previous experience
- technical_team: Do they have technical capabilities?

FUNDING (if mentioned):
- funding_stage: Current funding stage
- amount_raised: Money raised so far
- target_amount: How much they want to raise
- use_of_funds: What they'll use money for

Respond in this exact JSON format (only include fields with actual values):
{{
  "categories": ["category1", "category2"],
  "stage": "stage_name",
  "problem_solved": "description",
  "solution": "description",
  "target_market": "description",
  "business_model": "description",
  "metrics": {{
    "revenue": "amount",
    "users": "number",
    "growth_rate": "percentage"
  }},
  "team_info": {{
    "size": "number",
    "founders": ["name1", "name2"],
    "experience": "description"
  }},
  "funding_info": {{
    "funding_stage": "stage",
    "amount_raised": "amount",
    "target_amount": "amount"
  }}
}}
"""
        
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response (remove markdown if present)
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "")
            
            # Parse JSON
            extracted = json.loads(response_text)
            
            # Filter out empty values
            cleaned_data = self._clean_extracted_data(extracted)
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error("Failed to extract project info", error=str(e))
            return {}
    
    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate extracted data"""
        
        cleaned = {}
        
        # Handle basic fields
        basic_fields = [
            'categories', 'stage', 'problem_solved', 'solution', 
            'target_market', 'business_model'
        ]
        
        for field in basic_fields:
            if field in data and data[field]:
                if isinstance(data[field], str) and data[field].strip():
                    cleaned[field] = data[field].strip()
                elif isinstance(data[field], list) and data[field]:
                    cleaned[field] = data[field]
        
        # Handle nested objects
        if 'metrics' in data and data['metrics']:
            cleaned['metrics'] = {
                k: v for k, v in data['metrics'].items() 
                if v is not None and v != ""
            }
        
        if 'team_info' in data and data['team_info']:
            cleaned['team_info'] = {
                k: v for k, v in data['team_info'].items() 
                if v is not None and v != ""
            }
        
        if 'funding_info' in data and data['funding_info']:
            cleaned['funding_info'] = {
                k: v for k, v in data['funding_info'].items() 
                if v is not None and v != ""
            }
        
        return cleaned
    
    def _merge_project_data(
        self, 
        current: Optional[ProjectData], 
        extracted: Dict[str, Any]
    ) -> ProjectData:
        """Intelligently merge extracted data with existing project data"""
        
        if not current:
            current = ProjectData()
        
        # Basic fields - update if extracted data is more specific
        for field in ['problem_solved', 'solution', 'target_market', 'business_model']:
            if field in extracted:
                setattr(current, field, extracted[field])
        
        # Categories - merge lists
        if 'categories' in extracted:
            current_cats = current.categories or []
            new_cats = extracted['categories']
            merged_cats = list(set(current_cats + new_cats))
            current.categories = merged_cats
        
        # Stage - update to latest stage
        if 'stage' in extracted:
            current.stage = extracted['stage']
        
        # Metrics - merge objects
        if 'metrics' in extracted:
            if not current.metrics:
                current.metrics = ProjectMetrics()
            
            for key, value in extracted['metrics'].items():
                if hasattr(current.metrics, key):
                    setattr(current.metrics, key, value)
        
        # Team info - merge objects
        if 'team_info' in extracted:
            if not current.team_info:
                current.team_info = TeamInfo()
            
            for key, value in extracted['team_info'].items():
                if hasattr(current.team_info, key):
                    setattr(current.team_info, key, value)
        
        # Funding info - merge objects
        if 'funding_info' in extracted:
            if not current.funding_info:
                current.funding_info = FundingInfo()
            
            for key, value in extracted['funding_info'].items():
                if hasattr(current.funding_info, key):
                    setattr(current.funding_info, key, value)
        
        return current
    
    def _calculate_completeness(self, project_data: ProjectData) -> float:
        """Calculate project completeness score (0-100)"""
        
        total_weight = 0
        completed_weight = 0
        
        # Basic info (40% weight)
        basic_fields = {
            'categories': 10,
            'stage': 10,
            'problem_solved': 10,
            'solution': 10
        }
        
        for field, weight in basic_fields.items():
            total_weight += weight
            value = getattr(project_data, field, None)
            if value:
                completed_weight += weight
        
        # Business model (20% weight)
        business_fields = {
            'target_market': 10,
            'business_model': 10
        }
        
        for field, weight in business_fields.items():
            total_weight += weight
            value = getattr(project_data, field, None)
            if value:
                completed_weight += weight
        
        # Metrics (20% weight)
        if project_data.metrics:
            metrics_fields = ['revenue', 'users', 'growth_rate']
            completed_metrics = sum(
                1 for field in metrics_fields 
                if getattr(project_data.metrics, field, None)
            )
            total_weight += 20
            completed_weight += (completed_metrics / len(metrics_fields)) * 20
        else:
            total_weight += 20
        
        # Team info (10% weight)
        if project_data.team_info:
            team_fields = ['size', 'founders']
            completed_team = sum(
                1 for field in team_fields 
                if getattr(project_data.team_info, field, None)
            )
            total_weight += 10
            completed_weight += (completed_team / len(team_fields)) * 10
        else:
            total_weight += 10
        
        # Funding info (10% weight)
        if project_data.funding_info:
            total_weight += 10
            completed_weight += 10
        else:
            total_weight += 10
        
        return (completed_weight / total_weight) * 100 if total_weight > 0 else 0.0
    
    def _calculate_relevance(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate relevance score of extracted data"""
        
        if not extracted_data:
            return 0.0
        
        # Score based on number and importance of fields
        field_scores = {
            'categories': 0.2,
            'stage': 0.2,
            'problem_solved': 0.15,
            'solution': 0.15,
            'target_market': 0.1,
            'business_model': 0.1,
            'metrics': 0.05,
            'team_info': 0.03,
            'funding_info': 0.02
        }
        
        total_score = 0.0
        for field, score in field_scores.items():
            if field in extracted_data:
                total_score += score
        
        return min(total_score, 1.0)


# Global instance
librarian_bot = LibrarianBot()