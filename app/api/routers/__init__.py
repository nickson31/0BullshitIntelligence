"""
API Routers for 0BullshitIntelligence
"""

from .chat import router as chat_router
from .search import router as search_router  
from .webhooks import router as webhooks_router
from .health import router as health_router

__all__ = [
    "chat_router",
    "search_router", 
    "webhooks_router",
    "health_router"
]