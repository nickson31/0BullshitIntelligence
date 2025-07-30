"""
Y-Combinator Mentor System
"""

import google.generativeai as genai
from app.core.config import settings
from app.core.logging import get_logger
from app.models import UserContext, Language

logger = get_logger(__name__)


class YCMentorSystem:
    """
    Y-Combinator style mentor system for startup advice
    """
    
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1000,
            }
        )
        
        self.yc_principles = """
        Eres un mentor estilo Y-Combinator. Tus respuestas deben ser:
        - DIRECTAS y ACCIONABLES
        - CONCISAS (máximo 3-4 frases)
        - ENFOCADAS EN EJECUCIÓN
        - BASADAS EN DATOS Y MÉTRICAS
        - SIN FLUFF ni teoría innecesaria
        
        Principios Y-Combinator:
        1. "Make something people want"
        2. Habla con tus usuarios
        3. Lanza rápido, itera rápido
        4. Enfócate en métricas que importan (ARR, MRR, crecimiento)
        5. Tracción > Ideas
        6. Problem-solution fit antes que product-market fit
        """
    
    async def generate_response(
        self,
        user_message: str,
        user_context: UserContext,
        extracted_data=None,
        language: Language = Language.SPANISH
    ) -> str:
        """Generate Y-Combinator style mentor response"""
        
        try:
            # Build context for the prompt
            context = f"""
            Usuario: Plan {user_context.plan}, {user_context.credits} créditos
            Mensaje: {user_message}
            """
            
            if language == Language.SPANISH:
                prompt = f"""
                {self.yc_principles}
                
                Responde en ESPAÑOL como mentor de Y-Combinator.
                
                Contexto del usuario:
                {context}
                
                Da una respuesta directa, accionable y concisa. Máximo 3-4 frases.
                Enfócate en qué debe HACER el usuario, no en teoría.
                """
            else:
                prompt = f"""
                You are a Y-Combinator mentor. Your responses should be:
                - DIRECT and ACTIONABLE
                - CONCISE (max 3-4 sentences)
                - EXECUTION-FOCUSED
                - DATA and METRICS driven
                - NO fluff or unnecessary theory
                
                User context:
                {context}
                
                Give a direct, actionable and concise response. Max 3-4 sentences.
                Focus on what the user should DO, not theory.
                """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Mentor response generation failed: {e}")
            
            if language == Language.SPANISH:
                return "Como mentor de Y-Combinator te diría: Enfócate en hacer algo que la gente quiera. Habla con tus usuarios, valida tu idea rápidamente y lanza tu MVP lo antes posible."
            else:
                return "As a Y-Combinator mentor I'd tell you: Focus on making something people want. Talk to your users, validate your idea quickly and launch your MVP as soon as possible."
    
    async def generate_search_context_response(
        self,
        search_results,
        user_message: str,
        language: Language
    ) -> str:
        """Generate response contextualizing investor search results"""
        
        try:
            results_count = search_results.get("metadata", {}).get("total_results", 0)
            
            if language == Language.SPANISH:
                return f"He encontrado {results_count} inversores relevantes para tu startup. Antes de contactarlos, asegúrate de tener: 1) Métricas claras (usuarios, ingresos), 2) Tracción demostrable, 3) Un pitch deck sólido. Los mejores inversores quieren ver resultados, no solo ideas."
            else:
                return f"Found {results_count} relevant investors for your startup. Before contacting them, make sure you have: 1) Clear metrics (users, revenue), 2) Demonstrable traction, 3) A solid pitch deck. The best investors want to see results, not just ideas."
                
        except Exception as e:
            logger.error(f"Search context response generation failed: {e}")
            return "Aquí tienes los resultados de inversores. Prepárate bien antes de contactarlos."
    
    async def generate_company_context_response(
        self,
        search_results,
        user_message: str,
        language: Language
    ) -> str:
        """Generate response contextualizing company search results"""
        
        try:
            results_count = search_results.get("metadata", {}).get("total_results", 0)
            
            if language == Language.SPANISH:
                return f"He encontrado {results_count} empresas que pueden ayudarte. Como mentor te recomiendo: 1) Define claramente qué necesitas, 2) Compara precios y referencias, 3) Empieza con proyectos pequeños para probar la calidad. No gastes todo tu presupuesto de una vez."
            else:
                return f"Found {results_count} companies that can help you. As a mentor I recommend: 1) Clearly define what you need, 2) Compare prices and references, 3) Start with small projects to test quality. Don't spend all your budget at once."
                
        except Exception as e:
            logger.error(f"Company context response generation failed: {e}")
            return "Aquí tienes empresas que pueden ayudarte. Elige sabiamente."