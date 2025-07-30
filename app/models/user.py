"""
User models for authentication, plans, and project management
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from enum import Enum


class UserPlan(str, Enum):
    FREE = "free"
    PRO = "pro" 
    OUTREACH = "outreach"


class UserProfile(BaseModel):
    id: str
    email: str
    password_hash: str
    full_name: Optional[str] = None
    plan: UserPlan = UserPlan.FREE
    credits: int = 200  # Free plan starts with 200 credits
    daily_credits: int = 50  # Free plan gets 50 daily credits
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    subscription_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

    class Config:
        model_config = {"from_attributes": True}


class Project(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    
    # Project data for searches and memory
    categories: List[str] = []
    stage: Optional[str] = None
    problem_solved: Optional[str] = None
    business_model: Optional[str] = None
    target_audience: Optional[str] = None
    funding_stage: Optional[str] = None
    team_size: Optional[int] = None
    monthly_revenue: Optional[float] = None
    
    # Completeness tracking
    completeness_score: float = 0.0
    
    # Memory storage
    extracted_data: dict = {}
    
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        model_config = {"from_attributes": True}


class UserRegistration(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    plan: UserPlan
    credits: int
    daily_credits: int
    created_at: datetime
    last_login: Optional[datetime]


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    categories: List[str]
    stage: Optional[str]
    completeness_score: float
    created_at: datetime
    updated_at: datetime


class CreditPackage(BaseModel):
    id: str
    name: str
    credits: int
    price: float  # in USD
    stripe_price_id: str


class SubscriptionPlan(BaseModel):
    id: str
    name: str
    plan_type: UserPlan
    price: float  # in USD per month
    credits_monthly: int
    credits_daily: int
    features: List[str]
    stripe_price_id: str


# Credit packages available for purchase
CREDIT_PACKAGES = [
    CreditPackage(
        id="credits_4900",
        name="4,900 Credits",
        credits=4900,
        price=19.0,
        stripe_price_id="price_credits_4900"  # To be replaced with actual Stripe price ID
    ),
    CreditPackage(
        id="credits_19900", 
        name="19,900 Credits",
        credits=19900,
        price=59.0,
        stripe_price_id="price_credits_19900"
    ),
    CreditPackage(
        id="credits_49900",
        name="49,900 Credits", 
        credits=49900,
        price=149.0,
        stripe_price_id="price_credits_49900"
    )
]

# Subscription plans
SUBSCRIPTION_PLANS = [
    SubscriptionPlan(
        id="free",
        name="Free Plan",
        plan_type=UserPlan.FREE,
        price=0.0,
        credits_monthly=0,  # Only daily credits
        credits_daily=50,
        features=["Mentor AI", "200 Free Credits", "50 Daily Credits"],
        stripe_price_id=""
    ),
    SubscriptionPlan(
        id="pro",
        name="Pro Plan",
        plan_type=UserPlan.PRO,
        price=24.50,
        credits_monthly=10000,
        credits_daily=150,
        features=["Mentor AI", "Investor Search", "10,000 Monthly Credits", "150 Daily Credits"],
        stripe_price_id="price_pro_monthly"  # To be replaced with actual Stripe price ID
    ),
    SubscriptionPlan(
        id="outreach",
        name="Outreach Plan", 
        plan_type=UserPlan.OUTREACH,
        price=94.50,
        credits_monthly=29900,
        credits_daily=200,
        features=["Mentor AI", "Investor Search", "LinkedIn Automation", "29,900 Monthly Credits", "200 Daily Credits", "Unlimited Chat"],
        stripe_price_id="price_outreach_monthly"
    )
]


# Credit costs for different actions
class CreditCosts:
    CHAT_FREE = 10      # Free plan: 10 credits per chat
    CHAT_PRO = 5        # Pro plan: 5 credits per chat  
    CHAT_OUTREACH = 0   # Outreach plan: unlimited chat
    
    INVESTOR_SEARCH = 1000   # 1000 credits per investor search (15 results)
    COMPANY_SEARCH = 250     # 250 credits per company search


# Temporary UserContext for backward compatibility
class UserContext(BaseModel):
    """Lightweight user context for AI systems - TEMPORARY"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    plan: str = "free"
    language: str = "spanish"
    credits: int = 0
    session_data: dict = {}

    class Config:
        model_config = {"from_attributes": True}


# Temporary ProjectData for backward compatibility
class ProjectData(BaseModel):
    """Project data structure - TEMPORARY"""
    categories: List[str] = []
    stage: Optional[str] = None
    problem_solved: Optional[str] = None
    business_model: Optional[str] = None
    
    class Config:
        model_config = {"from_attributes": True}