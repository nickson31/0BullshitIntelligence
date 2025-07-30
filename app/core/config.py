"""
Configuration settings for 0BullshitIntelligence microservice.
Manages environment variables, database connections, and AI configurations.
"""

import os
from typing import Optional, List


class Settings:
    """Application settings with environment variable support"""
    
    def __init__(self):
        # ==========================================
        # APPLICATION SETTINGS
        # ==========================================
        self.app_name: str = "0BullshitIntelligence"
        self.app_version: str = "1.0.0"
        self.environment: str = os.getenv("ENVIRONMENT", "production")
        self.debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        
        # Server configuration
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.workers: int = 1
        
        # ==========================================
        # DATABASE CONFIGURATION
        # ==========================================
        
        # Supabase configuration
        self.supabase_url: str = os.getenv("SUPABASE_URL", "")
        # Try both possible names for the Supabase key
        self.supabase_key: str = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY", "")
        self.supabase_service_key: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")
        
        # ==========================================
        # AI CONFIGURATION
        # ==========================================
        
        # Google Gemini
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.gemini_temperature: float = 0.7
        self.gemini_max_tokens: int = 3000
        
        # ==========================================
        # API CONFIGURATION
        # ==========================================
        
        # CORS settings
        self.allowed_origins: List[str] = [
            "https://*.onrender.com",
            "http://localhost:3000",
            "http://localhost:8000"
        ]
        
        # Rate limiting
        self.rate_limit_per_minute: int = 60
        self.rate_limit_per_hour: int = 1000
        
        # ==========================================
        # AI SYSTEM CONFIGURATION
        # ==========================================
        
        # Language detection
        self.default_language: str = "spanish"
        self.supported_languages: List[str] = ["spanish", "english"]
        
        # ==========================================
        # LOGGING CONFIGURATION
        # ==========================================
        
        self.log_level: str = "INFO"
        self.log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_settings() -> Settings:
    """Get settings instance"""
    try:
        settings = Settings()
        
        # Validate required fields
        missing_vars = []
        if not settings.supabase_url:
            missing_vars.append("SUPABASE_URL")
        if not settings.supabase_key:
            missing_vars.append("SUPABASE_ANON_KEY (or SUPABASE_KEY)")
        if not settings.gemini_api_key:
            missing_vars.append("GEMINI_API_KEY")
            
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        return settings
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("📋 Required environment variables:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY (or SUPABASE_KEY)") 
        print("   - GEMINI_API_KEY")
        
        # Debug info
        available_vars = [var for var in os.environ.keys() if any(key in var for key in ['SUPABASE', 'GEMINI', 'DEBUG', 'HOST', 'PORT'])]
        print(f"🔍 Relevant environment variables found: {available_vars}")
        raise


# Initialize settings
try:
    settings = get_settings()
    print("✅ Configuration loaded successfully")
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