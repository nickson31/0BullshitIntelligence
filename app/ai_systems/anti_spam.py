"""
Anti-Spam System for 0BullshitIntelligence.
Uses Gemini to detect spam and generate clever, unique responses.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.ai_systems import AntiSpamResult
import google.generativeai as genai

logger = get_logger(__name__)
settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)


class AntiSpamSystem:
    """AI-powered anti-spam system with clever responses using Gemini"""
    
    def __init__(self):
        self.logger = logger
        self.spam_patterns = [
            "spam", "promoción", "oferta especial", "gratis",
            "click aquí", "ganar dinero", "oportunidad única"
        ]
    
    async def analyze_message(
        self,
        message: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AntiSpamResult:
        """Analyze message for spam content and generate appropriate response"""
        
        try:
            self.logger.info("Anti-spam analysis started",
                           conversation_id=conversation_id,
                           message_length=len(message))
            
            # Get comprehensive analysis from Gemini
            analysis = await self._gemini_comprehensive_analysis(message, context)
            
            # Create result with clever response if spam detected
            result = AntiSpamResult(
                conversation_id=conversation_id,
                user_input=message,
                spam_score=int(analysis['spam_score']),
                is_spam=analysis['is_spam'],
                detected_patterns=analysis['patterns'],
                reasoning=analysis['reasoning'],
                action_taken=analysis['action']
            )
            
            self.logger.info("Anti-spam analysis completed",
                           conversation_id=conversation_id,
                           spam_score=analysis['spam_score'],
                           is_spam=analysis['is_spam'])
            
            return result
            
        except Exception as e:
            self.logger.error("Anti-spam analysis failed",
                            conversation_id=conversation_id,
                            error=str(e))
            
            # Return safe fallback
            return AntiSpamResult(
                conversation_id=conversation_id,
                user_input=message,
                spam_score=0,
                is_spam=False,
                reasoning="Analysis failed, allowing message"
            )
    
    async def generate_clever_response(
        self,
        spam_result: AntiSpamResult,
        detected_language: str = "spanish",
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a clever, unique anti-spam response using Gemini"""
        
        if not spam_result.is_spam:
            return ""  # No response needed for clean messages
        
        try:
            prompt = self._build_response_prompt(
                spam_result, detected_language, user_context
            )
            
            response = await self._call_gemini(prompt)
            
            # Extract the response text (remove any formatting)
            clever_response = response.strip()
            if clever_response.startswith('"') and clever_response.endswith('"'):
                clever_response = clever_response[1:-1]
            
            self.logger.info("Clever anti-spam response generated",
                           conversation_id=spam_result.conversation_id,
                           spam_score=spam_result.spam_score)
            
            return clever_response
            
        except Exception as e:
            self.logger.error("Failed to generate clever response", error=str(e))
            
            # Fallback to basic response
            if detected_language == "english":
                return "Let's keep our conversation focused on your business goals. How can I help you with your startup?"
            else:
                return "Mantengamos nuestra conversación enfocada en tus objetivos de negocio. ¿Cómo puedo ayudarte con tu startup?"
    
    async def _gemini_comprehensive_analysis(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Use Gemini for comprehensive spam analysis"""
        
        context_str = ""
        if context:
            context_str = f"\nContext: {context}"
        
        prompt = f"""
You are an expert anti-spam system for a business intelligence platform that helps entrepreneurs.

Analyze this message for spam/inappropriate content:

Message: "{message}"{context_str}

Rate the message on spam likelihood (0-100) based on:
- Promotional/sales language unrelated to business advice
- Suspicious links or requests for personal info
- Repetitive or nonsensical content
- Off-topic content not related to startups/business
- Inappropriate or offensive language
- Content that seems automated or bot-like

Respond in this exact format:
SPAM_SCORE: [0-100]
IS_SPAM: [true/false]
PATTERNS: [comma-separated list of detected issues]
REASONING: [brief explanation]
ACTION: [allow/warn/block]
SEVERITY: [low/medium/high]
"""
        
        try:
            response = model.generate_content(prompt)
            lines = response.text.strip().split('\n')
            data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip()
            
            # Parse patterns
            patterns = []
            pattern_text = data.get('PATTERNS', '')
            if pattern_text and pattern_text.lower() not in ['none', 'no issues']:
                patterns = [p.strip() for p in pattern_text.split(',')]
            
            return {
                'spam_score': int(data.get('SPAM_SCORE', '0')),
                'is_spam': data.get('IS_SPAM', 'false').lower() == 'true',
                'patterns': patterns,
                'reasoning': data.get('REASONING', 'Content analysis completed'),
                'action': data.get('ACTION', 'allow'),
                'severity': data.get('SEVERITY', 'low')
            }
            
        except Exception as e:
            self.logger.error("Gemini spam analysis failed", error=str(e))
            return {
                'spam_score': 0,
                'is_spam': False,
                'patterns': [],
                'reasoning': 'Analysis failed',
                'action': 'allow',
                'severity': 'low'
            }
    
    def _build_response_prompt(
        self, 
        spam_result: AntiSpamResult, 
        language: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for generating clever anti-spam response"""
        
        context_str = ""
        if user_context:
            context_str = f"\nUser context: {user_context}"
        
        language_instruction = "in Spanish" if language == "spanish" else "in English"
        
        return f"""
You are a witty, intelligent business mentor for entrepreneurs. A user has sent spam/inappropriate content.

Spam details:
- Message: "{spam_result.user_input}"
- Spam score: {spam_result.spam_score}/100
- Detected issues: {', '.join(spam_result.detected_patterns or ['general spam'])}
- Reasoning: {spam_result.reasoning}{context_str}

Generate a clever, unique response {language_instruction} that:
1. Politely redirects to business topics
2. Shows intelligence and wit (not robotic)
3. Maintains a helpful, mentor-like tone
4. Is contextual to their specific spam type
5. Encourages legitimate business discussion
6. Is brief but memorable

Examples of tone (adapt, don't copy):
- "I'm here to help build empires, not pyramid schemes"
- "Let's channel that sales energy into your actual startup"
- "I prefer conversations that scale like good businesses - with substance"

Create a UNIQUE response (never repeat examples):
"""
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            self.logger.error("Gemini API call failed", error=str(e))
            raise


# Global instance
anti_spam_system = AntiSpamSystem()