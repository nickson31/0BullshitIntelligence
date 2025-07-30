"""
Chat Service - Main business logic for AI chat interactions
"""

import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from app.core.logging import get_logger
from app.models import ChatMessage, ChatResponse, UserContext
from app.ai_systems.judge_system import JudgeSystem
from app.ai_systems.language_detection import LanguageDetectionSystem
from app.ai_systems.anti_spam import AntiSpamSystem
from app.ai_systems.mentor_system import YCMentorSystem
from app.ai_systems.upselling_system import UpsellingSystem
from app.ai_systems.welcome_system import WelcomeSystem
from app.search.investor_search import investor_search_engine
from app.search.company_search import company_search_engine
from app.database import database_manager
from app.api.websockets import websocket_manager

logger = get_logger(__name__)


class ChatService:
    """
    Main service for processing chat messages and coordinating AI systems
    """
    
    def __init__(self):
        # Initialize AI systems
        self.judge_system = JudgeSystem()
        self.language_detection = LanguageDetectionSystem()
        self.anti_spam = AntiSpamSystem()
        self.mentor_system = YCMentorSystem()
        self.upselling_system = UpsellingSystem()
        self.welcome_system = WelcomeSystem()
        
        # Processing statistics
        self.processed_messages = 0
        self.last_processing_time = None
    
    async def process_message(
        self,
        message: ChatMessage,
        user_context: UserContext
    ) -> ChatResponse:
        """
        Process a user message through the complete AI pipeline
        
        This is the main entry point for chat processing. It:
        1. Detects language and spam
        2. Uses Judge system to decide actions
        3. Executes appropriate AI systems
        4. Returns structured response
        """
        start_time = datetime.utcnow()
        
        try:
            self.processed_messages += 1
            self.last_processing_time = start_time
            
            logger.info(
                "Processing chat message",
                user_id=user_context.user_id,
                conversation_id=str(message.conversation_id),
                message_length=len(message.content)
            )
            
            # Step 1: Language Detection
            language_result = await self.language_detection.detect_language(
                message.content
            )
            
            logger.debug(f"Language detected: {language_result.detected_language}")
            
            # Step 2: Anti-spam Detection
            spam_result = await self.anti_spam.check_message(
                message.content,
                user_context=user_context
            )
            
            if spam_result.is_spam:
                logger.warning(f"Spam detected: {spam_result.reason}")
                
                # Generate anti-spam response
                anti_spam_response = await self.anti_spam.generate_response(
                    spam_result,
                    language_result.response_language
                )
                
                return ChatResponse(
                    success=True,
                    message="Anti-spam response generated",
                    ai_response=anti_spam_response,
                    processing_time_ms=self._calculate_processing_time(start_time)
                )
            
            # Step 3: Judge System Decision
            judge_decision = await self.judge_system.analyze_user_intent(
                user_message=message.content,
                user_language=language_result.detected_language,
                user_context=user_context
            )
            
            logger.info(
                "Judge decision made",
                decision=judge_decision.decision,
                confidence=judge_decision.confidence
            )
            
            # Send judge decision via WebSocket for real-time updates
            if message.conversation_id:
                await websocket_manager.send_ai_response(
                    str(message.conversation_id),
                    {
                        "type": "judge_decision",
                        "decision": judge_decision.decision,
                        "confidence": judge_decision.confidence,
                        "reasoning": judge_decision.reasoning
                    }
                )
            
            # Step 4: Execute Actions Based on Judge Decision
            response_data = await self._execute_judge_decision(
                judge_decision,
                message,
                user_context,
                language_result
            )
            
            # Step 5: Check for Upselling Opportunities
            upsell_message = await self._check_upselling(
                judge_decision,
                user_context,
                language_result.response_language
            )
            
            # Step 6: Prepare Final Response
            final_response = ChatResponse(
                success=True,
                message="Message processed successfully",
                data=response_data,
                ai_response=response_data.get("ai_response"),
                search_results=response_data.get("search_results"),
                upsell_message=upsell_message,
                processing_time_ms=self._calculate_processing_time(start_time)
            )
            
            logger.info(
                "Chat message processed successfully",
                processing_time_ms=final_response.processing_time_ms,
                has_search_results=bool(response_data.get("search_results")),
                has_upsell=bool(upsell_message)
            )
            
            return final_response
            
        except Exception as e:
            logger.error(f"Chat message processing failed: {e}", exc_info=True)
            
            # Return error response
            return ChatResponse(
                success=False,
                message="Failed to process message",
                ai_response="Lo siento, hubo un error procesando tu mensaje. Por favor intenta de nuevo.",
                processing_time_ms=self._calculate_processing_time(start_time)
            )
    
    async def _execute_judge_decision(
        self,
        judge_decision,
        message: ChatMessage,
        user_context: UserContext,
        language_result
    ) -> Dict[str, Any]:
        """Execute the actions determined by the Judge system"""
        
        response_data = {}
        
        # Handle different judge decisions
        if judge_decision.decision == "search_investors":
            logger.info("Executing investor search")
            
            # Extract search parameters from judge decision
            extracted_data = judge_decision.extracted_data
            keywords = extracted_data.categories if extracted_data else []
            stage_keywords = [extracted_data.stage] if extracted_data and extracted_data.stage else []
            
            # Execute investor search
            search_results = await investor_search_engine.search_investors(
                keywords=keywords,
                stage_keywords=stage_keywords,
                user_context=user_context,
                limit=15
            )
            
            response_data["search_results"] = search_results
            response_data["search_type"] = "investors"
            
            # Generate contextual response
            ai_response = await self.mentor_system.generate_search_context_response(
                search_results,
                message.content,
                language_result.response_language
            )
            response_data["ai_response"] = ai_response
            
        elif judge_decision.decision == "search_companies":
            logger.info("Executing company search")
            
            # Extract service keywords from message
            service_keywords = await self._extract_service_keywords(
                message.content,
                judge_decision.extracted_data
            )
            
            # Execute company search
            search_results = await company_search_engine.search_companies(
                service_keywords=service_keywords,
                user_context=user_context,
                limit=10
            )
            
            response_data["search_results"] = search_results
            response_data["search_type"] = "companies"
            
            # Generate contextual response
            ai_response = await self.mentor_system.generate_company_context_response(
                search_results,
                message.content,
                language_result.response_language
            )
            response_data["ai_response"] = ai_response
            
        elif judge_decision.decision == "welcome":
            logger.info("Generating welcome message")
            
            # Generate welcome message
            welcome_response = await self.welcome_system.generate_welcome_message(
                user_context=user_context,
                language=language_result.response_language
            )
            
            response_data["ai_response"] = welcome_response
            response_data["message_type"] = "welcome"
            
        elif judge_decision.decision == "mentor_response":
            logger.info("Generating mentor response")
            
            # Generate Y-Combinator style mentor response
            mentor_response = await self.mentor_system.generate_response(
                user_message=message.content,
                user_context=user_context,
                extracted_data=judge_decision.extracted_data,
                language=language_result.response_language
            )
            
            response_data["ai_response"] = mentor_response
            response_data["message_type"] = "mentor"
            
        else:
            # Default mentor response for unknown decisions
            logger.warning(f"Unknown judge decision: {judge_decision.decision}")
            
            mentor_response = await self.mentor_system.generate_response(
                user_message=message.content,
                user_context=user_context,
                language=language_result.response_language
            )
            
            response_data["ai_response"] = mentor_response
            response_data["message_type"] = "mentor"
        
        return response_data
    
    async def _extract_service_keywords(
        self,
        message_content: str,
        extracted_data: Any = None
    ) -> list[str]:
        """Extract service keywords from user message"""
        
        # Basic keyword extraction - could be enhanced with NLP
        service_keywords = []
        
        # Common service types
        service_patterns = [
            "marketing", "publicidad", "seo", "sem", "social media",
            "desarrollo", "software", "app", "web", "programación",
            "diseño", "branding", "ui", "ux", "gráfico",
            "legal", "abogado", "asesoría", "compliance",
            "contabilidad", "finanzas", "accounting",
            "recursos humanos", "hr", "recruitment"
        ]
        
        message_lower = message_content.lower()
        
        for pattern in service_patterns:
            if pattern in message_lower:
                service_keywords.append(pattern)
        
        # If no specific keywords found, use general business services
        if not service_keywords:
            service_keywords = ["business services", "consulting"]
        
        return service_keywords
    
    async def _check_upselling(
        self,
        judge_decision,
        user_context: UserContext,
        language
    ) -> Optional[str]:
        """Check if upselling opportunity exists"""
        
        try:
            upsell_opportunity = await self.upselling_system.analyze_opportunity(
                user_context=user_context,
                judge_decision=judge_decision,
                language=language
            )
            
            if upsell_opportunity.should_upsell:
                return upsell_opportunity.message
            
            return None
            
        except Exception as e:
            logger.error(f"Upselling check failed: {e}")
            return None
    
    async def regenerate_response(
        self,
        conversation_id: str,
        message_id: str,
        user_context: UserContext
    ) -> ChatResponse:
        """Regenerate the last AI response"""
        
        try:
            # Get the original message from database
            # This would need to be implemented
            logger.info(f"Regenerating response for message {message_id}")
            
            # For now, return a placeholder
            return ChatResponse(
                success=True,
                message="Response regeneration not yet implemented",
                ai_response="Esta función estará disponible pronto."
            )
            
        except Exception as e:
            logger.error(f"Response regeneration failed: {e}")
            raise
    
    async def stream_response(
        self,
        conversation_id: str,
        user_context: UserContext
    ) -> AsyncGenerator[str, None]:
        """Stream chat response for real-time updates"""
        
        try:
            # This would stream the AI processing in real-time
            yield "Starting processing..."
            yield "Analyzing message..."
            yield "Generating response..."
            yield "Complete!"
            
        except Exception as e:
            logger.error(f"Response streaming failed: {e}")
            yield f"Error: {str(e)}"
    
    def _calculate_processing_time(self, start_time: datetime) -> float:
        """Calculate processing time in milliseconds"""
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        return round(duration * 1000, 2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chat service statistics"""
        return {
            "processed_messages": self.processed_messages,
            "last_processing_time": self.last_processing_time.isoformat() if self.last_processing_time else None
        }


# Create singleton instance
chat_service = ChatService()