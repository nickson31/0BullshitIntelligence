"""
Judge System for 0BullshitIntelligence
Analyzes user intent and determines appropriate response strategy
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

import google.generativeai as genai
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.ai_systems import JudgeDecision

logger = get_logger(__name__)
settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)


class JudgeSystem:
    """
    Intelligent system for analyzing user intent and determining response strategy
    """
    
    def __init__(self):
        self.conversation_states = {}  # Track conversation context
    
    async def analyze_message(self, user_input: str, conversation_id: str, context: Dict[str, Any]) -> JudgeDecision:
        """
        Analyze user message and determine intent and response strategy
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info("Judge analysis started", 
                       conversation_id=conversation_id,
                       message_length=len(user_input))
            
            # Get conversation state
            conv_state = self.conversation_states.get(conversation_id, {
                'message_count': 0,
                'has_business_context': False,
                'last_intent': None
            })
            
            conv_state['message_count'] += 1
            
            # Build analysis prompt based on conversation state
            prompt = self._build_analysis_prompt(user_input, conv_state)
            
            # Call Gemini for analysis
            response = await self._call_gemini(prompt)
            decision = self._parse_decision(response, user_input, conversation_id)
            
            # Update conversation state
            conv_state['last_intent'] = decision.detected_intent
            if decision.detected_intent in ['business_question', 'search_investors', 'search_companies']:
                conv_state['has_business_context'] = True
            
            self.conversation_states[conversation_id] = conv_state
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info("Judge decision completed",
                       conversation_id=conversation_id,
                       decision=decision.detected_intent,
                       confidence=decision.confidence_score,
                       processing_time_ms=round(processing_time, 2))
            
            return decision
            
        except Exception as e:
            logger.error("Judge analysis failed", 
                        conversation_id=conversation_id,
                        error=str(e))
            
            # Return fallback decision
            return JudgeDecision(
                conversation_id=conversation_id,
                user_input=user_input,
                detected_intent="chat",
                confidence_score=0.5,
                should_search=False,
                should_ask_questions=True,
                should_upsell=False,
                reasoning="Fallback due to analysis error"
            )
    
    def _build_analysis_prompt(self, user_input: str, conv_state: Dict[str, Any]) -> str:
        """Build context-aware analysis prompt"""
        
        message_count = conv_state.get('message_count', 0)
        has_business_context = conv_state.get('has_business_context', False)
        
        return f"""Analyze this user message and determine the most appropriate response strategy.

User message: "{user_input}"

Conversation context:
- Message count: {message_count}
- Has business context: {has_business_context}
- Previous intent: {conv_state.get('last_intent', 'none')}

Intent categories:
1. "simple_greeting" - Basic greetings like "hi", "hello", "hola" without business context
2. "casual_chat" - Casual conversation, small talk, general questions  
3. "business_question" - Specific business/startup questions or problems
4. "search_investors" - Looking for investors, funding, VCs
5. "search_companies" - Looking for service providers, partners, vendors
6. "personal_intro" - User introducing themselves or their business

Guidelines:
- First messages that are just greetings should be "simple_greeting"
- Only classify as "business_question" if there's a clear business problem or startup topic
- Don't assume business intent from simple greetings
- Consider conversation flow and previous context

Respond with:
INTENT: [intent_category]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation]
ASK_QUESTIONS: [true/false] - whether to ask follow-up questions
SHOULD_SEARCH: [true/false] - whether this needs search functionality
SHOULD_UPSELL: [true/false] - whether to mention premium features"""

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API for analysis"""
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error("Gemini analysis failed", error=str(e))
            return "INTENT: chat\nCONFIDENCE: 0.5\nREASONING: Fallback response\nASK_QUESTIONS: true\nSHOULD_SEARCH: false\nSHOULD_UPSELL: false"
    
    def _parse_decision(self, response: str, user_input: str, conversation_id: str) -> JudgeDecision:
        """Parse Gemini response into JudgeDecision"""
        try:
            lines = response.split('\n')
            
            # Default values
            intent = "chat"
            confidence = 0.7
            reasoning = "Default reasoning"
            ask_questions = True
            should_search = False
            should_upsell = False
            
            # Parse each line
            for line in lines:
                line = line.strip()
                if line.startswith('INTENT:'):
                    intent = line.split(':', 1)[1].strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                    except:
                        confidence = 0.7
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
                elif line.startswith('ASK_QUESTIONS:'):
                    ask_questions = line.split(':', 1)[1].strip().lower() == 'true'
                elif line.startswith('SHOULD_SEARCH:'):
                    should_search = line.split(':', 1)[1].strip().lower() == 'true'
                elif line.startswith('SHOULD_UPSELL:'):
                    should_upsell = line.split(':', 1)[1].strip().lower() == 'true'
            
            return JudgeDecision(
                conversation_id=conversation_id,
                user_input=user_input,
                detected_intent=intent,
                confidence_score=confidence,
                should_search=should_search,
                should_ask_questions=ask_questions,
                should_upsell=should_upsell,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error("Failed to parse judge decision", error=str(e))
            return JudgeDecision(
                conversation_id=conversation_id,
                user_input=user_input,
                detected_intent="chat",
                confidence_score=0.5,
                should_search=False,
                should_ask_questions=True,
                should_upsell=False,
                reasoning="Parsing error"
            )


# Global instance
judge_system = JudgeSystem()