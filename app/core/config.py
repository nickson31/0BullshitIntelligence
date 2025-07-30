"""
Configuration settings for 0BullshitIntelligence microservice.
Manages environment variables, database connections, and AI configurations.
"""

import os
from typing import Optional, List
try:
    from pydantic import BaseSettings, validator
except ImportError:
    # Fallback for when pydantic is not available
    class BaseSettings:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        class Config:
            env_file = ".env"
    
    def validator(field):
        def decorator(func):
            return func
        return decorator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # ==========================================
    # APPLICATION SETTINGS
    # ==========================================
    app_name: str = "0BullshitIntelligence"
    app_version: str = "1.0.0"
    environment: str = "production"
    debug: bool = False
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # ==========================================
    # DATABASE CONFIGURATION
    # ==========================================
    
    # Supabase configuration
    supabase_url: str
    supabase_key: str
    supabase_service_key: Optional[str] = None
    
    @validator("supabase_url", "supabase_key")
    def validate_required_supabase(cls, v):
        if not v:
            raise ValueError("Supabase URL and KEY are required")
        return v
    
    # ==========================================
    # AI CONFIGURATION
    # ==========================================
    
    # Google Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 3000
    
    @validator("gemini_api_key")
    def validate_gemini_key(cls, v):
        if not v:
            raise ValueError("Gemini API key is required")
        return v
    
    # ==========================================
    # API CONFIGURATION
    # ==========================================
    
    # CORS settings
    allowed_origins: List[str] = [
        "https://*.onrender.com",
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # ==========================================
    # AI SYSTEM CONFIGURATION
    # ==========================================
    
    # Language detection
    default_language: str = "spanish"
    supported_languages: List[str] = ["spanish", "english"]
    
    # ==========================================
    # LOGGING CONFIGURATION
    # ==========================================
    
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Field aliases for environment variables
        fields = {
            "supabase_url": {"env": "SUPABASE_URL"},
            "supabase_key": {"env": "SUPABASE_KEY"},
            "supabase_service_key": {"env": "SUPABASE_SERVICE_KEY"},
            "gemini_api_key": {"env": "GEMINI_API_KEY"},
            "gemini_model": {"env": "GEMINI_MODEL"},
            "environment": {"env": "ENVIRONMENT"},
            "debug": {"env": "DEBUG"},
            "host": {"env": "HOST"},
            "port": {"env": "PORT"},
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenient access to settings
settings = get_settings()


# ==========================================
# VALIDATION FUNCTIONS
# ==========================================

def validate_environment() -> None:
    """Validate that all required environment variables are set"""
    try:
        settings = get_settings()
        
        # Test critical connections
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("Supabase configuration is incomplete")
            
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key is required")
            
        print("✅ Environment validation successful")
        
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        raise


# ==========================================
# FEATURE FLAGS
# ==========================================

class FeatureFlags:
    """Feature flags for enabling/disabling functionality"""
    
    @staticmethod
    def is_debug_mode() -> bool:
        return settings.debug or settings.environment == "development"


# Convenient access to feature flags
features = FeatureFlags()