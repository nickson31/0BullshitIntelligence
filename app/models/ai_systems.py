"""
AI Systems models for 0BullshitIntelligence microservice.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pydantic import Field

from .base import BaseModel, Language, ProjectStage, ProjectCategory, PlanType


# ==========================================
# JUDGE SYSTEM MODELS
# ==========================================

class JudgeDecision(BaseModel):
    """Judge system decision model"""
    conversation_id: UUID
    user_input: str = Field(max_length=1000)
    detected_intent: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    should_search: bool = False
    should_ask_questions: bool = False
    should_upsell: bool = False
    search_type: Optional[str] = None
    reasoning: str = Field(max_length=2000)
    language_detected: Language = Language.SPANISH
    
    # Timestamp fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# ==========================================
# LANGUAGE DETECTION
# ==========================================

class LanguageDetection(BaseModel):
    """Language detection result"""
    conversation_id: UUID
    text_sample: str = Field(max_length=500)
    detected_language: Language
    confidence_score: float = Field(ge=0.0, le=1.0)
    alternative_languages: Optional[List[Language]] = None
    
    # Timestamp fields
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# ANTI-SPAM SYSTEM
# ==========================================

class AntiSpamResult(BaseModel):
    """Anti-spam analysis result"""
    conversation_id: UUID
    user_input: str = Field(max_length=1000)
    spam_score: int = Field(ge=0, le=100)
    is_spam: bool = False
    detected_patterns: Optional[List[str]] = None
    reasoning: Optional[str] = Field(max_length=1000)
    action_taken: Optional[str] = None
    
    # Timestamp fields
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# UPSELLING SYSTEM
# ==========================================

class UpsellOpportunity(BaseModel):
    """Upselling opportunity detection"""
    conversation_id: UUID
    user_id: UUID
    current_plan: PlanType = PlanType.FREE
    suggested_plan: PlanType
    trigger_context: str = Field(max_length=500)
    confidence_score: float = Field(ge=0.0, le=1.0)
    message_template: str = Field(max_length=2000)
    should_present: bool = False
    cooldown_until: Optional[datetime] = None
    
    # Timestamp fields
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# WELCOME SYSTEM
# ==========================================

class WelcomeMessage(BaseModel):
    """Welcome message configuration"""
    conversation_id: UUID
    user_id: UUID
    onboarding_stage: int = Field(ge=1, le=5)
    message_content: str = Field(max_length=2000)
    next_questions: Optional[List[str]] = None
    completed_stages: List[int] = Field(default_factory=list)
    is_returning_user: bool = False
    
    # Timestamp fields
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# AI SYSTEM RESPONSES
# ==========================================

class AISystemResponse(BaseModel):
    """Generic AI system response"""
    system_name: str
    conversation_id: UUID
    processing_time_ms: float
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Timestamp fields
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# PROJECT DATA EXTRACTION
# ==========================================

class ProjectDataExtraction(BaseModel):
    """Extracted project data from conversation"""
    conversation_id: UUID
    user_id: UUID
    project_name: Optional[str] = None
    project_description: Optional[str] = Field(max_length=2000)
    project_stage: Optional[ProjectStage] = None
    project_category: Optional[ProjectCategory] = None
    target_market: Optional[str] = None
    business_model: Optional[str] = None
    team_size: Optional[int] = None
    current_revenue: Optional[str] = None
    competitive_advantage: Optional[str] = None
    funding_needs: Optional[str] = None
    use_of_funds: Optional[str] = None


class LibrarianUpdate(BaseModel):
    """Librarian system update - fixed MRO issue"""
    conversation_id: UUID
    project_id: UUID
    user_message: str = Field(max_length=500)  # Truncated for storage
    assistant_response: str = Field(max_length=500)  # Truncated for storage
    message_pair_id: UUID = Field(default_factory=uuid4)
    context_extracted: Optional[Dict[str, Any]] = None
    embedding_vector: Optional[List[float]] = None
    relevance_score: Optional[float] = Field(ge=0.0, le=1.0)
    success: bool = True
    
    # Timestamp fields directly in the model
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# ==========================================
# CONVERSATION CONTEXT
# ==========================================

class ConversationContextUpdate(BaseModel):
    """Context update for conversation memory"""
    conversation_id: UUID
    user_id: UUID
    context_type: str = Field(max_length=50)
    context_data: Dict[str, Any]
    importance_score: float = Field(ge=0.0, le=1.0)
    expires_at: Optional[datetime] = None
    
    # Timestamp fields
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# METRICS AND MONITORING
# ==========================================

class AISystemMetrics(BaseModel):
    """Metrics for AI system performance"""
    system_name: str
    conversation_id: UUID
    operation_type: str
    processing_time_ms: float
    memory_usage_mb: Optional[float] = None
    tokens_used: Optional[int] = None
    api_calls_made: int = 0
    success_rate: float = Field(ge=0.0, le=1.0)
    error_count: int = 0
    
    # Timestamp fields
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemHealthCheck(BaseModel):
    """System health check result"""
    system_name: str
    status: str = Field(default="healthy")  # healthy, degraded, down
    response_time_ms: float
    last_error: Optional[str] = None
    uptime_percentage: float = Field(ge=0.0, le=100.0)
    dependencies_status: Optional[Dict[str, str]] = None
    
    # Timestamp fields
    created_at: datetime = Field(default_factory=datetime.utcnow)