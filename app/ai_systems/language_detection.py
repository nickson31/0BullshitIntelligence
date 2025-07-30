"""
Language Detection System for 0BullshitIntelligence.
Uses Gemini to intelligently detect language and provide contextual responses.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.ai_systems import LanguageDetection
import google.generativeai as genai

logger = get_logger(__name__)
settings = get_settings()

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)


class LanguageDetectionSystem:
    """Gemini-powered language detection with contextual understanding"""
    
    def __init__(self):
        self.logger = logger
    
    async def detect_language(
        self,
        text: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LanguageDetection:
        """Intelligently detect language using Gemini"""
        
        try:
            self.logger.info("Language detection started",
                           conversation_id=conversation_id,
                           text_length=len(text))
            
            # Build context-aware prompt
            prompt = self._build_detection_prompt(text, context)
            
            # Get Gemini analysis
            response = await self._call_gemini(prompt)
            
            # Parse response
            detection = self._parse_response(response, conversation_id, text)
            
            self.logger.info("Language detection completed",
                           conversation_id=conversation_id,
                           detected_language=detection.detected_language,
                           confidence=detection.confidence_score)
            
            return detection
            
        except Exception as e:
            self.logger.error("Language detection failed",
                            conversation_id=conversation_id,
                            error=str(e))
            
            # Fallback to simple detection
            return self._fallback_detection(text, conversation_id)
    
    def _build_detection_prompt(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build contextual language detection prompt"""
        
        context_str = ""
        if context:
            context_str = f"\nConversation context: {context}"
        
        return f"""
You are an expert language detection system for a business intelligence platform.

Analyze this text and detect the language:

Text: "{text}"{context_str}

Consider:
- Primary language used
- Mixed language usage
- Business context
- Regional variations
- Confidence level

Respond in this exact format:
LANGUAGE: [spanish/english/other]
CONFIDENCE: [0.0-1.0]
ALTERNATIVES: [comma-separated list if mixed]
REGIONAL_VARIANT: [es-ES, en-US, etc. if detectable]
BUSINESS_CONTEXT: [formal/informal/technical]
REASONING: [brief explanation of detection]
"""
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API for language detection"""
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            self.logger.error("Gemini language detection failed", error=str(e))
            raise
    
    def _parse_response(self, response: str, conversation_id: str, text: str) -> LanguageDetection:
        """Parse Gemini response into LanguageDetection model"""
        
        try:
            lines = response.strip().split('\n')
            data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip()
            
            # Parse alternatives
            alternatives = []
            alt_text = data.get('ALTERNATIVES', '')
            if alt_text and alt_text.lower() != 'none':
                alternatives = [lang.strip() for lang in alt_text.split(',')]
            
            return LanguageDetection(
                conversation_id=conversation_id,
                text_sample=text[:500],  # Truncate for storage
                detected_language=data.get('LANGUAGE', 'spanish'),
                confidence_score=float(data.get('CONFIDENCE', '0.8')),
                alternative_languages=alternatives if alternatives else None
            )
            
        except Exception as e:
            self.logger.error("Failed to parse language detection response",
                            response=response, error=str(e))
            
            return self._fallback_detection(text, conversation_id)
    
    def _fallback_detection(self, text: str, conversation_id: str) -> LanguageDetection:
        """Simple fallback language detection"""
        
        # Basic Spanish indicators
        spanish_indicators = [
            'el', 'la', 'es', 'de', 'que', 'y', 'en', 'un', 'una', 'con',
            'por', 'para', 'como', 'pero', 'del', 'los', 'las', 'se', 'le'
        ]
        
        # Basic English indicators  
        english_indicators = [
            'the', 'and', 'is', 'of', 'to', 'in', 'a', 'that', 'it', 'with',
            'for', 'as', 'was', 'on', 'are', 'you', 'this', 'be', 'at', 'by'
        ]
        
        text_lower = text.lower()
        spanish_score = sum(1 for word in spanish_indicators if word in text_lower)
        english_score = sum(1 for word in english_indicators if word in text_lower)
        
        if spanish_score > english_score:
            detected = "spanish"
            confidence = min(0.7, spanish_score / 10)
        elif english_score > spanish_score:
            detected = "english"
            confidence = min(0.7, english_score / 10)
        else:
            detected = "spanish"  # Default for business context
            confidence = 0.5
        
        return LanguageDetection(
            conversation_id=conversation_id,
            text_sample=text[:500],
            detected_language=detected,
            confidence_score=confidence
        )


# Global instance
language_detection_system = LanguageDetectionSystem()