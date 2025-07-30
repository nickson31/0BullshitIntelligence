"""
Language Detection System
"""

from app.core.logging import get_logger
from app.models import LanguageDetection, Language

logger = get_logger(__name__)


class LanguageDetectionSystem:
    """
    System for detecting user language and determining response language
    """
    
    def __init__(self):
        pass
    
    async def detect_language(self, text: str) -> LanguageDetection:
        """Detect language from user text"""
        
        # Simple language detection logic
        # In production, this would use more sophisticated detection
        
        spanish_indicators = [
            "qué", "cómo", "dónde", "cuándo", "por qué", "sí", "no", "gracias",
            "hola", "necesito", "quiero", "busco", "ayuda", "startup", "empresa"
        ]
        
        english_indicators = [
            "what", "how", "where", "when", "why", "yes", "no", "thanks",
            "hello", "need", "want", "looking", "help", "startup", "company"
        ]
        
        text_lower = text.lower()
        
        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        if spanish_count > english_count:
            detected = Language.SPANISH
            confidence = min(0.7 + (spanish_count * 0.1), 1.0)
        elif english_count > spanish_count:
            detected = Language.ENGLISH
            confidence = min(0.7 + (english_count * 0.1), 1.0)
        else:
            # Default to Spanish if unclear
            detected = Language.SPANISH
            confidence = 0.5
        
        return LanguageDetection(
            detected_language=detected,
            confidence=confidence,
            response_language=detected,
            is_mixed_language=spanish_count > 0 and english_count > 0
        )