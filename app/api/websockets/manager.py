"""
WebSocket Manager for real-time chat communication
"""

import json
import asyncio
from typing import Dict, Set, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time chat communication
    """
    
    def __init__(self):
        # Active connections: {conversation_id: Set[WebSocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Connection metadata: {WebSocket: {conversation_id, user_id, connected_at}}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
        # Message queues for offline users: {conversation_id: List[Dict]}
        self.message_queues: Dict[str, List[Dict[str, Any]]] = {}
        
        # Maximum queue size per conversation
        self.max_queue_size = 100
    
    async def connect(self, websocket: WebSocket, conversation_id: str, user_id: Optional[str] = None):
        """Connect a new WebSocket client"""
        try:
            await websocket.accept()
            
            # Add to active connections
            if conversation_id not in self.active_connections:
                self.active_connections[conversation_id] = set()
            
            self.active_connections[conversation_id].add(websocket)
            
            # Store metadata
            self.connection_metadata[websocket] = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "connected_at": datetime.utcnow().isoformat()
            }
            
            logger.info(
                "WebSocket connected",
                conversation_id=conversation_id,
                user_id=user_id,
                total_connections=len(self.active_connections[conversation_id])
            )
            
            # Send any queued messages for this conversation
            await self._send_queued_messages(websocket, conversation_id)
            
            # Send connection confirmation
            await self._send_to_websocket(websocket, {
                "type": "connection_established",
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to chat"
            })
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            await self.disconnect(websocket, conversation_id)
    
    async def disconnect(self, websocket: WebSocket, conversation_id: str):
        """Disconnect a WebSocket client"""
        try:
            # Remove from active connections
            if conversation_id in self.active_connections:
                self.active_connections[conversation_id].discard(websocket)
                
                # Clean up empty conversation rooms
                if not self.active_connections[conversation_id]:
                    del self.active_connections[conversation_id]
            
            # Remove metadata
            metadata = self.connection_metadata.pop(websocket, {})
            user_id = metadata.get("user_id")
            
            logger.info(
                "WebSocket disconnected",
                conversation_id=conversation_id,
                user_id=user_id,
                remaining_connections=len(self.active_connections.get(conversation_id, []))
            )
            
            # Close connection if still open
            try:
                await websocket.close()
            except:
                pass  # Connection might already be closed
                
        except Exception as e:
            logger.error(f"WebSocket disconnect error: {e}")
    
    async def disconnect_all(self):
        """Disconnect all WebSocket connections (for shutdown)"""
        logger.info("Disconnecting all WebSocket connections")
        
        for conversation_id in list(self.active_connections.keys()):
            for websocket in list(self.active_connections[conversation_id]):
                await self.disconnect(websocket, conversation_id)
    
    async def broadcast_to_conversation(self, conversation_id: str, message: Dict[str, Any]):
        """Broadcast message to all clients in a conversation"""
        if conversation_id not in self.active_connections:
            logger.debug(f"No active connections for conversation {conversation_id}")
            await self._queue_message(conversation_id, message)
            return
        
        # Get active connections for this conversation
        connections = self.active_connections[conversation_id].copy()
        
        if not connections:
            logger.debug(f"No active connections for conversation {conversation_id}")
            await self._queue_message(conversation_id, message)
            return
        
        # Send to all connected clients
        disconnected = []
        for websocket in connections:
            success = await self._send_to_websocket(websocket, message)
            if not success:
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket, conversation_id)
        
        logger.info(
            "Message broadcasted",
            conversation_id=conversation_id,
            message_type=message.get('type', 'unknown'),
            connections_count=len(connections) - len(disconnected),
            disconnected_count=len(disconnected)
        )
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections of a specific user"""
        sent_count = 0
        
        for websocket, metadata in self.connection_metadata.items():
            if metadata.get("user_id") == user_id:
                success = await self._send_to_websocket(websocket, message)
                if success:
                    sent_count += 1
        
        logger.debug(f"Message sent to user {user_id}, {sent_count} connections")
    
    async def handle_message(self, conversation_id: str, data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        try:
            message_type = data.get("type", "unknown")
            
            logger.debug(
                "WebSocket message received",
                conversation_id=conversation_id,
                message_type=message_type
            )
            
            if message_type == "ping":
                # Respond to ping with pong
                response = {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.broadcast_to_conversation(conversation_id, response)
            
            elif message_type == "chat_message":
                # Handle chat messages - process through AI systems
                await self._handle_chat_message(conversation_id, data)
            
            elif message_type == "search_status":
                # Handle search status updates (for real-time search progress)
                await self._handle_search_status(conversation_id, data)
            
            elif message_type == "typing":
                # Handle typing indicators
                await self._handle_typing_indicator(conversation_id, data)
            
            else:
                logger.warning(f"Unknown WebSocket message type: {message_type}")
        
        except Exception as e:
            logger.error(f"WebSocket message handling failed: {e}")
    
    async def _handle_chat_message(self, conversation_id: str, data: Dict[str, Any]):
        """Handle chat message processing through AI systems"""
        try:
            logger.info("Starting chat message processing", 
                       conversation_id=conversation_id,
                       data_keys=list(data.keys()),
                       raw_data=data)
            
            # Get message content (try both 'content' and 'message' fields)
            content = data.get("content", "") or data.get("message", "")
            content = content.strip() if content else ""
            session_id = data.get("session_id", str(uuid4()))
            
            if not content:
                logger.warning("Empty message content received")
                await self.send_error_message(conversation_id, "Message content is required")
                return
            
            logger.info("Processing chat message", 
                       conversation_id=conversation_id,
                       session_id=session_id,
                       content_length=len(content))
            
            # Send typing indicator
            await self.broadcast_to_conversation(conversation_id, {
                "type": "ai_typing",
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Session context for anonymous users
            session_data = {"session_id": session_id}
            
            try:
                # Import AI systems
                from app.ai_systems.judge_system import judge_system
                from app.ai_systems.anti_spam import anti_spam_system
                from app.ai_systems.language_detection import language_detection_system
                from app.ai_systems.librarian import librarian_bot
                
                logger.info("AI systems imported successfully")
                
                # 1. Anti-spam check
                logger.info("Starting anti-spam analysis")
                spam_result = await anti_spam_system.analyze_message(
                    content, conversation_id, session_data
                )
                logger.info("Anti-spam analysis complete", is_spam=spam_result.is_spam)
                
                if spam_result.is_spam:
                    # Generate clever anti-spam response
                    spam_response = await anti_spam_system.generate_clever_response(
                        spam_result, "spanish", session_data
                    )
                    
                    await self.send_ai_response(conversation_id, {
                        "content": spam_response,
                        "metadata": {
                            "spam_detected": True,
                            "spam_score": spam_result.spam_score
                        }
                    })
                    return
                
                # 2. Language detection
                logger.info("Starting language detection")
                language_detection = await language_detection_system.detect_language(
                    content, conversation_id, session_data
                )
                logger.info("Language detection complete", language=language_detection.detected_language)
                
                # 3. Judge system - determine intent
                logger.info("Starting judge system analysis")
                judge_decision = await judge_system.analyze_message(
                    content, conversation_id, session_data
                )
                logger.info("Judge system analysis complete", intent=judge_decision.detected_intent)
                
                # 4. Generate response with Gemini
                logger.info("Starting AI response generation")
                ai_response = await self._generate_ai_response(
                    content, conversation_id, session_data, judge_decision
                )
                logger.info("AI response generated", response_length=len(ai_response))
                
                # 5. Librarian - extract and store project data
                logger.info("Starting librarian processing")
                librarian_result = await librarian_bot.process_conversation_update(
                    session_id,
                    conversation_id, 
                    content,
                    ai_response,
                    session_data.get('project_data')
                )
                logger.info("Librarian processing complete", completeness_score=librarian_result['completeness_score'])
                
                # Send AI response
                await self.send_ai_response(conversation_id, {
                    "content": ai_response,
                    "metadata": {
                        "intent": judge_decision.detected_intent,
                        "language": language_detection.detected_language,
                        "confidence": judge_decision.confidence_score,
                        "completeness_score": librarian_result['completeness_score'],
                        "extracted_fields": librarian_result['extracted_fields']
                    }
                })
                
                logger.info("Chat message processed successfully",
                           conversation_id=conversation_id,
                           intent=judge_decision.detected_intent,
                           completeness_score=librarian_result['completeness_score'])
                
            except Exception as ai_error:
                logger.error("AI systems processing failed", error=str(ai_error), error_type=type(ai_error).__name__)
                # Send a simple response as fallback
                await self.send_ai_response(conversation_id, {
                    "content": "Hola! Soy tu asistente de IA. ¿En qué puedo ayudarte con tu startup? 🚀",
                    "metadata": {"fallback_response": True}
                })
            
        except Exception as e:
            logger.error("Chat message handling failed completely", error=str(e), error_type=type(e).__name__)
            try:
                await self.send_error_message(conversation_id, 
                    "Lo siento, hubo un problema técnico. ¿Podrías intentar de nuevo?")
            except Exception as send_error:
                logger.error("Failed to send error message", error=str(send_error))
    
    async def _generate_ai_response(self, user_message: str, conversation_id: str, 
                                  session_data: Dict[str, Any], judge_decision: Any) -> str:
        """Generate AI response using Gemini"""
        try:
            from app.core.config import get_settings
            import google.generativeai as genai
            
            settings = get_settings()
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(settings.gemini_model)
            
            # Build context-aware prompt
            context_info = ""
            project_data = session_data.get('project_data')
            if project_data:
                context_info = f"""
Context about user's project:
- Categories: {project_data.get('categories', [])}
- Stage: {project_data.get('stage', 'unknown')}
- Problem solved: {project_data.get('problem_solved', '')}
- Business model: {project_data.get('business_model', '')}
"""
            
            # Create intelligent prompt based on intent
            if judge_decision.detected_intent == "search_investors":
                prompt = f"""You are a Y-Combinator mentor helping entrepreneurs find investors.

User message: "{user_message}"
{context_info}

The user wants to find investors. Provide specific, actionable advice about:
1. What stage they should be at for investor search
2. What metrics they need to prepare
3. Types of investors to target based on their business
4. How to approach investors effectively

Be direct, practical, and encouraging. Respond in Spanish if the user wrote in Spanish.
"""
            elif judge_decision.detected_intent == "search_companies":
                prompt = f"""You are a business mentor helping entrepreneurs find B2B services and partners.

User message: "{user_message}"
{context_info}

The user is looking for companies/services. Help them:
1. Identify what type of service they really need
2. Key criteria to evaluate providers
3. Questions to ask potential partners
4. Red flags to avoid

Be practical and specific. Respond in Spanish if the user wrote in Spanish.
"""
            else:
                prompt = f"""You are a brilliant Y-Combinator mentor with deep startup experience.

User message: "{user_message}"
{context_info}

Provide expert startup advice that is:
- Direct and actionable
- Based on real experience
- Focused on execution over theory
- Encouraging but realistic

If they mention their business, ask insightful follow-up questions to understand their needs better.
Respond in Spanish if the user wrote in Spanish, English if they wrote in English.
"""
            
            # Generate response with Gemini
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error("AI response generation failed", error=str(e))
            return "Lo siento, hubo un problema técnico. ¿Podrías intentar de nuevo? / Sorry, there was a technical issue. Could you try again?"

    async def send_search_progress(self, conversation_id: str, progress_data: Dict[str, Any]):
        """Send search progress updates to connected clients"""
        message = {
            "type": "search_progress",
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            **progress_data
        }
        
        await self.broadcast_to_conversation(conversation_id, message)
    
    async def send_search_results(self, conversation_id: str, results: Dict[str, Any]):
        """Send search results to connected clients"""
        message = {
            "type": "search_results",
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }
        
        await self.broadcast_to_conversation(conversation_id, message)
    
    async def send_ai_response(self, conversation_id: str, response_data: Dict[str, Any]):
        """Send AI response to connected clients"""
        logger.info("Sending AI response", 
                   conversation_id=conversation_id,
                   content_length=len(response_data.get('content', '')),
                   has_metadata=bool(response_data.get('metadata')))
        
        message = {
            "type": "ai_response",
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            **response_data
        }
        
        await self.broadcast_to_conversation(conversation_id, message)
        logger.info("AI response sent successfully", conversation_id=conversation_id)
    
    async def send_error_message(self, conversation_id: str, error_message: str):
        """Send error message to connected clients"""
        message = {
            "type": "error",
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "content": error_message
        }
        
        await self.broadcast_to_conversation(conversation_id, message)

    async def _send_to_websocket(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """Send message to a single WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
            return True
        except WebSocketDisconnect:
            logger.debug("WebSocket disconnected during send")
            return False
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            return False
    
    async def _queue_message(self, conversation_id: str, message: Dict[str, Any]):
        """Queue message for offline users"""
        if conversation_id not in self.message_queues:
            self.message_queues[conversation_id] = []
        
        # Add timestamp
        message["queued_at"] = datetime.utcnow().isoformat()
        
        # Add to queue
        self.message_queues[conversation_id].append(message)
        
        # Limit queue size
        if len(self.message_queues[conversation_id]) > self.max_queue_size:
            self.message_queues[conversation_id] = self.message_queues[conversation_id][-self.max_queue_size:]
        
        logger.debug(f"Message queued for conversation {conversation_id}")
    
    async def _send_queued_messages(self, websocket: WebSocket, conversation_id: str):
        """Send queued messages to newly connected client"""
        if conversation_id not in self.message_queues:
            return
        
        queued_messages = self.message_queues[conversation_id]
        if not queued_messages:
            return
        
        logger.info(f"Sending {len(queued_messages)} queued messages to {conversation_id}")
        
        for message in queued_messages:
            # Add replay indicator
            message["replayed"] = True
            await self._send_to_websocket(websocket, message)
        
        # Clear queue after sending
        self.message_queues[conversation_id] = []
    
    async def _handle_search_status(self, conversation_id: str, data: Dict[str, Any]):
        """Handle search status updates"""
        status = data.get("status", "unknown")
        
        response = {
            "type": "search_status_ack",
            "conversation_id": conversation_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_conversation(conversation_id, response)
    
    async def _handle_typing_indicator(self, conversation_id: str, data: Dict[str, Any]):
        """Handle typing indicators"""
        typing_data = {
            "type": "typing_indicator",
            "conversation_id": conversation_id,
            "user_id": data.get("user_id"),
            "is_typing": data.get("is_typing", False),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_conversation(conversation_id, typing_data)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        active_conversations = len(self.active_connections)
        queued_conversations = len(self.message_queues)
        total_queued_messages = sum(len(queue) for queue in self.message_queues.values())
        
        return {
            "total_connections": total_connections,
            "active_conversations": active_conversations,
            "queued_conversations": queued_conversations,
            "total_queued_messages": total_queued_messages,
            "timestamp": datetime.utcnow().isoformat()
        }