"""
WebSocket management for 0BullshitIntelligence
"""

from .manager import WebSocketManager

# Create singleton instance
websocket_manager = WebSocketManager()

__all__ = ["websocket_manager", "WebSocketManager"]