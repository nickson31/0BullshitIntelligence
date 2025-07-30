"""
WebSocket Manager for real-time chat communication
"""

import json
import asyncio
from typing import Dict, Set, List, Any, Optional
from datetime import datetime

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
        
        logger.debug(
            "Message broadcasted",
            conversation_id=conversation_id,
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
        message = {
            "type": "ai_response",
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            **response_data
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