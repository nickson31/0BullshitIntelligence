"""
Anti-Spam System for 0BullshitIntelligence.
Uses Gemini to detect spam and inappropriate content.
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
    """AI-powered anti-spam system using Gemini"""
    
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
        """Analyze message for spam content"""
        
        try:
            self.logger.info("Anti-spam analysis started",
                           conversation_id=conversation_id,
                           message_length=len(message))
            
            # Quick pattern check first
            quick_score = self._quick_spam_check(message)
            
            # If quick check is high, use Gemini for detailed analysis
            if quick_score > 30:
                detailed_score = await self._gemini_spam_analysis(message)
                final_score = max(quick_score, detailed_score)
            else:
                final_score = quick_score
            
            # Determine if it's spam
            is_spam = final_score > 70
            
            # Create result
            result = AntiSpamResult(
                conversation_id=conversation_id,
                user_input=message,
                spam_score=int(final_score),
                is_spam=is_spam,
                detected_patterns=self._get_detected_patterns(message),
                reasoning=f"Spam score: {final_score}/100",
                action_taken="block" if is_spam else "allow"
            )
            
            self.logger.info("Anti-spam analysis completed",
                           conversation_id=conversation_id,
                           spam_score=final_score,
                           is_spam=is_spam)
            
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
    
    def _quick_spam_check(self, message: str) -> float:
        """Quick pattern-based spam check"""
        
        message_lower = message.lower()
        score = 0.0
        
        # Check for spam patterns
        for pattern in self.spam_patterns:
            if pattern in message_lower:
                score += 20
        
        # Check for excessive caps
        if len(message) > 10:
            caps_ratio = sum(1 for c in message if c.isupper()) / len(message)
            if caps_ratio > 0.5:
                score += 30
        
        # Check for excessive punctuation
        punct_count = sum(1 for c in message if c in "!!!!!????")
        if punct_count > 3:
            score += 20
        
        # Check for very short/nonsensical messages
        if len(message.strip()) < 3:
            score += 40
        
        return min(score, 100)
    
    async def _gemini_spam_analysis(self, message: str) -> float:
        """Use Gemini for detailed spam analysis"""
        
        try:
            prompt = f"""
Analyze this message for spam content:

Message: "{message}"

Rate the spam likelihood from 0-100 based on:
- Promotional language
- Suspicious links or requests
- Repetitive content
- Inappropriate content
- Off-topic business content

Respond with just a number (0-100):
"""
            
            response = model.generate_content(prompt)
            score_text = response.text.strip()
            
            # Extract numeric score
            import re
            numbers = re.findall(r'\d+', score_text)
            if numbers:
                return min(float(numbers[0]), 100)
            else:
                return 30  # Default moderate score
                
        except Exception as e:
            self.logger.error("Gemini spam analysis failed", error=str(e))
            return 30  # Default score on error
    
    def _get_detected_patterns(self, message: str) -> List[str]:
        """Get list of detected spam patterns"""
        
        detected = []
        message_lower = message.lower()
        
        for pattern in self.spam_patterns:
            if pattern in message_lower:
                detected.append(pattern)
        
        # Check for caps
        if len(message) > 10:
            caps_ratio = sum(1 for c in message if c.isupper()) / len(message)
            if caps_ratio > 0.5:
                detected.append("excessive_caps")
        
        return detected


# Global instance
anti_spam_system = AntiSpamSystem()