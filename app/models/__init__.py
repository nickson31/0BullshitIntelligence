"""
Data models and schemas for 0BullshitIntelligence microservice.
"""

from .base import *
from .chat import *
from .user import *
from .ai_systems import *

__all__ = [
    # Base models - only include what actually exists
    "BaseModel",
    
    # Chat models
    "ChatMessage",
    "ChatResponse",
    "Conversation",
    "Message",
    "ConversationCreate",
    "ConversationResponse",
    
    # User models
    "UserProfile",
    "Project", 
    "UserRegistration",
    "UserLogin",
    "UserResponse",
    "ProjectCreate",
    "ProjectResponse",
    "UserPlan",
    "CreditPackage",
    "SubscriptionPlan",
    "CREDIT_PACKAGES",
    "SUBSCRIPTION_PLANS",
    "CreditCosts",
    "UserContext",  # Temporary for backward compatibility
    "ProjectData",  # Temporary for backward compatibility
    
    # AI Systems models
    "JudgeDecision",
    "LanguageDetectionResult",
    "AntiSpamResult",
    "UpsellOpportunity",
    "WelcomeMessage",
    "LibrarianUpdate",
    "ProjectDataExtraction",
    "ConversationContextUpdate",
    "AISystemMetrics",
    "SystemHealthCheck",
    "AISystemResponse",
    "Language",
]