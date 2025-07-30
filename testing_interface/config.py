"""
Configuration for 0BullshitIntelligence Testing Interface
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Main App Configuration (Optional)
    MAIN_APP_URL: str = os.getenv("MAIN_APP_URL", "http://localhost:8000")
    MAIN_APP_API_KEY: str = os.getenv("MAIN_APP_API_KEY", "")
    
    def validate(self) -> bool:
        """Validate required configuration"""
        missing = []
        
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_ANON_KEY:
            missing.append("SUPABASE_ANON_KEY")
        if not self.SUPABASE_SERVICE_KEY:
            missing.append("SUPABASE_SERVICE_KEY")
        if not self.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
            
        if missing:
            print(f"❌ Missing required environment variables: {', '.join(missing)}")
            print("📄 Please check your .env file and the .env.example template")
            return False
            
        return True

# Create global settings instance
settings = Settings()