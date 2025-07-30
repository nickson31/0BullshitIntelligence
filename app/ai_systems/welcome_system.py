"""
Welcome System
"""

from app.core.logging import get_logger
from app.models import UserContext, Language

logger = get_logger(__name__)


class WelcomeSystem:
    """
    System for generating personalized welcome messages
    """
    
    def __init__(self):
        pass
    
    async def generate_welcome_message(
        self,
        user_context: UserContext,
        project_id: str = None,
        language: Language = Language.SPANISH
    ) -> str:
        """Generate personalized welcome message"""
        
        try:
            if language == Language.SPANISH:
                if user_context.plan == "free":
                    return f"""¡Hola! 👋 Soy tu mentor de startup especializado. 

Estoy aquí para ayudarte con:
• Consejos estratégicos para tu startup
• Guía sobre financiación y crecimiento
• Análisis de tu modelo de negocio

Tienes {user_context.credits} créditos disponibles. ¿En qué puedo ayudarte hoy con tu proyecto?"""
                
                elif user_context.plan == "pro":
                    return f"""¡Bienvenido de vuelta! 🚀 

Como usuario Pro, puedes:
• Obtener consejos expertos personalizados
• Buscar inversores específicos para tu startup
• Acceder a nuestra base de datos de +10,000 inversores

Créditos disponibles: {user_context.credits}. ¿Qué necesitas para hacer crecer tu startup?"""
                
                else:  # outreach
                    return f"""¡Hola! 💼 Tienes acceso completo a todas las funciones.

Puedes:
• Recibir mentoría especializada
• Buscar inversores relevantes
• Automatizar outreach por LinkedIn
• Crear campañas personalizadas

Créditos: {user_context.credits}. ¿Empezamos a buscar inversores para tu startup?"""
            
            else:  # English
                if user_context.plan == "free":
                    return f"""Hello! 👋 I'm your specialized startup mentor.

I'm here to help you with:
• Strategic advice for your startup  
• Funding and growth guidance
• Business model analysis

You have {user_context.credits} credits available. How can I help you with your project today?"""
                
                elif user_context.plan == "pro":
                    return f"""Welcome back! 🚀

As a Pro user, you can:
• Get personalized expert advice
• Search for specific investors for your startup
• Access our database of +10,000 investors

Available credits: {user_context.credits}. What do you need to grow your startup?"""
                
                else:  # outreach
                    return f"""Hello! 💼 You have full access to all features.

You can:
• Receive specialized mentoring
• Search for relevant investors
• Automate LinkedIn outreach
• Create personalized campaigns

Credits: {user_context.credits}. Shall we start looking for investors for your startup?"""
                    
        except Exception as e:
            logger.error(f"Welcome message generation failed: {e}")
            return "¡Hola! Soy tu mentor de startup. ¿En qué puedo ayudarte hoy?"