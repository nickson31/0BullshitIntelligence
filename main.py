"""
Main entry point for 0BullshitIntelligence
Production-ready FastAPI application with Gemini AI integration
"""

import sys
import asyncio
import signal
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging

# Initialize logging first
setup_logging()
logger = get_logger(__name__)

def check_dependencies():
    """Check if all critical dependencies are available"""
    try:
        import fastapi
        import uvicorn
        import gunicorn
        import supabase
        import google.generativeai
        import jinja2
        import structlog
        logger.info("✅ All critical dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing critical dependency: {e}")
        return False


def validate_environment():
    """Validate environment configuration"""
    try:
        settings = get_settings()
        
        # Check required environment variables
        required_vars = ['supabase_url', 'supabase_key', 'gemini_api_key']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(settings, var, None):
                missing_vars.append(var.upper())
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            return False
            
        logger.info("✅ Environment validation successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        return False


def initialize_services():
    """Initialize application services"""
    try:
        logger.info("🔧 Initializing services...")
        
        # Services will be initialized by their respective modules
        # when imported by the FastAPI app
        
        logger.info("✅ Services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        return False


# Import the FastAPI app instance
try:
    from app.api.app import app
    logger.info("✅ Configuration loaded successfully")
    logger.info("🧠 Starting 0BullshitIntelligence...")
    
except ImportError as e:
    logger.error(f"❌ Failed to import app: {e}")
    # Create a minimal fallback FastAPI app
    from fastapi import FastAPI
    app = FastAPI(title="0BullshitIntelligence - Import Error", 
                  description="Application failed to start due to import error")
    
    @app.get("/")
    async def error_page():
        return {"error": "Application failed to start", "details": str(e)}


def main():
    """Main entry point for direct execution"""
    try:
        # Load configuration
        settings = get_settings()
        logger.info("✅ Configuration loaded successfully")
        
        # Validate environment
        if not validate_environment():
            sys.exit(1)
            
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
            
        # Initialize services
        if not initialize_services():
            sys.exit(1)
            
        logger.info("✅ Application setup completed")
        logger.info("🎯 Starting server...")
        
        # Run the application
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8001,
            reload=False,
            log_level="info",
            access_log=True,
            workers=1
        )
        
    except KeyboardInterrupt:
        logger.info("🔄 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()