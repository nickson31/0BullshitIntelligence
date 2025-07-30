"""
Upselling System
"""

from app.core.logging import get_logger
from app.models import UpsellOpportunity, UserContext, Language

logger = get_logger(__name__)


class UpsellingSystem:
    """
    System for detecting upselling opportunities and generating messages
    """
    
    def __init__(self):
        pass
    
    async def analyze_opportunity(
        self,
        user_context: UserContext,
        judge_decision,
        language: Language
    ) -> UpsellOpportunity:
        """Analyze if upselling opportunity exists"""
        
        try:
            should_upsell = False
            message = None
            opportunity_type = None
            confidence = 0.0
            
            # Free to Pro upselling
            if user_context.plan == "free":
                if judge_decision.decision == "search_investors":
                    should_upsell = True
                    opportunity_type = "free_to_pro"
                    confidence = 0.8
                    
                    if language == Language.SPANISH:
                        message = "💡 Con el Plan Pro podrías buscar inversores específicos para tu startup y obtener acceso a nuestra base de datos completa de +10,000 inversores."
                    else:
                        message = "💡 With the Pro Plan you could search for specific investors for your startup and get access to our complete database of +10,000 investors."
            
            # Pro to Outreach upselling
            elif user_context.plan == "pro":
                if judge_decision.decision == "search_investors" and hasattr(judge_decision, 'extracted_data'):
                    should_upsell = True
                    opportunity_type = "pro_to_outreach"
                    confidence = 0.7
                    
                    if language == Language.SPANISH:
                        message = "🚀 Con el Plan Outreach puedes automatizar el contacto con estos inversores a través de LinkedIn y enviar mensajes personalizados a escala."
                    else:
                        message = "🚀 With the Outreach Plan you can automate contact with these investors through LinkedIn and send personalized messages at scale."
            
            return UpsellOpportunity(
                should_upsell=should_upsell,
                opportunity_type=opportunity_type or "none",
                confidence=confidence,
                message=message,
                target_plan="pro" if opportunity_type == "free_to_pro" else "outreach"
            )
            
        except Exception as e:
            logger.error(f"Upselling analysis failed: {e}")
            return UpsellOpportunity(
                should_upsell=False,
                opportunity_type="error",
                confidence=0.0,
                target_plan="none"
            )