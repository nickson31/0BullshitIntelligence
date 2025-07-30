"""
Configuration settings for 0BullshitIntelligence microservice.
Manages environment variables, database connections, and AI configurations.
"""

import os
from typing import Optional, List
try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator, Field
except ImportError:
    try:
        from pydantic import BaseSettings, field_validator, Field
    except ImportError:
        # Fallback for when pydantic is not available
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        def field_validator(field):
            def decorator(func):
                return func
            return decorator
            
        def Field(**kwargs):
            return None
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # ==========================================
    # APPLICATION SETTINGS
    # ==========================================
    app_name: str = "0BullshitIntelligence"
    app_version: str = "1.0.0"
    environment: str = Field(default="production", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = 1
    
    # ==========================================
    # DATABASE CONFIGURATION
    # ==========================================
    
    # Supabase configuration - match Render's variable names
    supabase_url: str = Field(env="SUPABASE_URL")
    supabase_key: str = Field(env="SUPABASE_ANON_KEY")  # Render uses SUPABASE_ANON_KEY
    supabase_service_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_KEY")
    
    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v):
        if not v:
            raise ValueError("Supabase URL is required - set SUPABASE_URL environment variable")
        return v
        
    @field_validator("supabase_key")
    @classmethod
    def validate_supabase_key(cls, v):
        if not v:
            raise ValueError("Supabase KEY is required - set SUPABASE_ANON_KEY environment variable")
        return v
    
    # ==========================================
    # AI CONFIGURATION
    # ==========================================
    
    # Google Gemini
    gemini_api_key: str = Field(env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", env="GEMINI_MODEL")
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 3000
    
    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_key(cls, v):
        if not v:
            raise ValueError("Gemini API key is required - set GEMINI_API_KEY environment variable")
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
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow"
    }


def get_settings() -> Settings:
    """Get settings instance - removed caching for better env var detection"""
    try:
        return Settings()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("📋 Required environment variables:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY (or SUPABASE_KEY)") 
        print("   - GEMINI_API_KEY")
        print(f"🔍 Current environment variables: {list(os.environ.keys())}")
        raise


# Convenient access to settings
try:
    settings = get_settings()
except Exception:
    # Create minimal settings for import - will fail on first use
    settings = None


# ==========================================
# VALIDATION FUNCTIONS
# ==========================================

def validate_environment() -> None:
    """Validate that all required environment variables are set"""
    try:
        global settings
        if settings is None:
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
        global settings
        if settings is None:
            return False
        return settings.debug or settings.environment == "development"


# Convenient access to feature flags
features = FeatureFlags()