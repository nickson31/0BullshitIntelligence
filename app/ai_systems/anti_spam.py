"""
Anti-Spam System
"""

from app.core.logging import get_logger
from app.models import AntiSpamResult, SpamIndicators, UserContext, Language

logger = get_logger(__name__)


class AntiSpamSystem:
    """
    System for detecting and responding to spam content
    """
    
    def __init__(self):
        pass
    
    async def check_message(self, text: str, user_context: UserContext = None) -> AntiSpamResult:
        """Check if message is spam"""
        
        # Simple spam detection logic
        spam_indicators = SpamIndicators()
        spam_score = 0.0
        
        # Check for repeated content
        if len(text) > 100 and len(set(text.lower().split())) < 10:
            spam_indicators.repeated_content = True
            spam_score += 20
        
        # Check for excessive length
        if len(text) > 2000:
            spam_indicators.excessive_length = True
            spam_score += 15
        
        # Check for nonsensical text
        if len(text.split()) > 20 and text.count(' ') / len(text) < 0.1:
            spam_indicators.nonsensical_text = True
            spam_score += 25
        
        # Check for off-topic content
        business_keywords = [
            "startup", "business", "investor", "funding", "company", "revenue",
            "empresa", "negocio", "inversor", "financiación", "ingresos"
        ]
        
        if not any(keyword in text.lower() for keyword in business_keywords) and len(text) > 50:
            spam_indicators.off_topic = True
            spam_score += 10
        
        is_spam = spam_score >= 30
        confidence = min(spam_score / 100, 1.0)
        
        if is_spam:
            reason = "Contenido detectado como spam"
            suggested_action = "warn" if spam_score < 50 else "block"
            response_tone = "warning" if spam_score < 50 else "strict"
        else:
            reason = "Contenido válido"
            suggested_action = "allow"
            response_tone = "normal"
        
        return AntiSpamResult(
            is_spam=is_spam,
            spam_score=spam_score,
            confidence=confidence,
            reason=reason,
            indicators=spam_indicators,
            suggested_action=suggested_action,
            response_tone=response_tone
        )
    
    async def generate_response(self, spam_result: AntiSpamResult, language: Language) -> str:
        """Generate anti-spam response"""
        
        if language == Language.SPANISH:
            if spam_result.response_tone == "warning":
                return "Por favor, mantén tus mensajes relacionados con startups y emprendimiento. Estoy aquí para ayudarte con tu negocio."
            else:
                return "No puedo ayudarte con ese tipo de contenido. Enfoquémonos en tu startup."
        else:
            if spam_result.response_tone == "warning":
                return "Please keep your messages related to startups and entrepreneurship. I'm here to help you with your business."
            else:
                return "I can't help you with that type of content. Let's focus on your startup."