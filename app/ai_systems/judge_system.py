"""
Judge System for 0BullshitIntelligence.
Determines what action to take based on user input.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.ai_systems import JudgeDecision
import google.generativeai as genai

logger = get_logger(__name__)
settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)


class JudgeSystem:
    """AI Judge system that decides what action to take based on user input"""
    
    def __init__(self):
        self.logger = logger
        
    async def analyze_message(
        self, 
        message: str, 
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> JudgeDecision:
        """Analyze user message and decide next action"""
        
        start_time = datetime.utcnow()
        
        try:
            self.logger.info("Judge analysis started", 
                           conversation_id=conversation_id,
                           message_length=len(message))
            
            # Build prompt for Gemini
            prompt = self._build_judge_prompt(message, context)
            
            # Get Gemini response
            response = await self._call_gemini(prompt)
            
            # Parse response into structured decision
            decision = self._parse_decision(response, conversation_id, message)
            
            # Log the decision
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.logger.info("Judge decision completed",
                           conversation_id=conversation_id,
                           decision=decision.detected_intent,
                           confidence=decision.confidence_score,
                           processing_time_ms=processing_time)
            
            return decision
            
        except Exception as e:
            self.logger.error("Judge analysis failed",
                            conversation_id=conversation_id,
                            error=str(e))
            
            # Return fallback decision
            return JudgeDecision(
                conversation_id=conversation_id,
                user_input=message,
                detected_intent="chat",
                confidence_score=0.5,
                reasoning="Fallback due to analysis error"
            )
    
    def _build_judge_prompt(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for judge decision"""
        
        context_str = ""
        if context:
            context_str = f"\nContext: {context}"
        
        return f"""
You are an AI assistant judge that analyzes user messages to determine the best action.

User message: "{message}"{context_str}

Analyze this message and determine the user's intent. Choose from:
1. "chat" - General conversation, answer directly
2. "search_investors" - User wants to find investors 
3. "search_companies" - User wants to find companies/competitors
4. "ask_questions" - Need more info about their project
5. "upsell" - Opportunity to suggest premium features

Also determine:
- Confidence score (0.0 to 1.0)
- Language detected (spanish/english) 
- Reasoning for your decision

Respond in this exact format:
INTENT: [intent]
CONFIDENCE: [0.0-1.0]
LANGUAGE: [spanish/english]
SEARCH_TYPE: [investors/companies/none]
SHOULD_SEARCH: [true/false]
SHOULD_ASK_QUESTIONS: [true/false]
SHOULD_UPSELL: [true/false]
REASONING: [your reasoning]
"""
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            self.logger.error("Gemini API call failed", error=str(e))
            raise
    
    def _parse_decision(self, response: str, conversation_id: str, user_input: str) -> JudgeDecision:
        """Parse Gemini response into structured decision"""
        
        try:
            lines = response.strip().split('\n')
            data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip()
            
            return JudgeDecision(
                conversation_id=conversation_id,
                user_input=user_input,
                detected_intent=data.get('INTENT', 'chat'),
                confidence_score=float(data.get('CONFIDENCE', '0.7')),
                should_search=data.get('SHOULD_SEARCH', 'false').lower() == 'true',
                should_ask_questions=data.get('SHOULD_ASK_QUESTIONS', 'false').lower() == 'true',
                should_upsell=data.get('SHOULD_UPSELL', 'false').lower() == 'true',
                search_type=data.get('SEARCH_TYPE', 'none') if data.get('SEARCH_TYPE', 'none') != 'none' else None,
                reasoning=data.get('REASONING', 'Analysis completed'),
                language_detected="spanish"  # Default for now
            )
            
        except Exception as e:
            self.logger.error("Failed to parse judge response", 
                            response=response, error=str(e))
            
            # Return safe fallback
            return JudgeDecision(
                conversation_id=conversation_id,
                user_input=user_input,
                detected_intent="chat",
                confidence_score=0.5,
                reasoning="Failed to parse analysis"
            )


# Global instance
judge_system = JudgeSystem()