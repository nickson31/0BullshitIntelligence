#!/usr/bin/env python3
"""
0BullshitIntelligence - AI Chat Application
==========================================

AI-powered chat application with modern UI and Gemini integration.

Author: 0Bullshit Team
Version: 1.0.0
"""

import sys
import asyncio
from pathlib import Path

# Add app directory to Python path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings, validate_environment, features
from app.core.logging import setup_logging, get_logger

logger = get_logger(__name__)


def check_dependencies():
    """Check that all required dependencies are available"""
    try:
        import fastapi
        import supabase
        import google.generativeai
        import pydantic
        import uvicorn
        import jinja2
        logger.info("✅ All critical dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing critical dependency: {e}")
        logger.error("Please run: pip install -r requirements.txt")
        return False


async def initialize_services():
    """Initialize core services"""
    logger.info("🔧 Initializing services...")
    
    try:
        # Initialize database connections
        from app.database import database_manager
        await database_manager.initialize()
        logger.info("✅ Database connections initialized")
        
        # Initialize AI systems
        from app.ai_systems import ai_coordinator
        await ai_coordinator.initialize()
        logger.info("✅ AI systems initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        return False


def main():
    """Main application entry point"""
    print("🧠 Starting 0BullshitIntelligence...")
    
    # Setup logging first
    setup_logging()
    
    logger.info("🚀 Starting 0BullshitIntelligence...")
    logger.info(f"Version: {settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {features.is_debug_mode()}")
    
    # Validate environment
    try:
        validate_environment()
        logger.info("✅ Environment validation successful")
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Initialize services
    try:
        asyncio.run(initialize_services())
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        sys.exit(1)
    
    # Import and start the application
    try:
        from app.api.app import app
        logger.info("✅ Application imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import application: {e}")
        sys.exit(1)
    
    # Server configuration
    logger.info(f"🌐 Server configuration:")
    logger.info(f"   Host: {settings.host}")
    logger.info(f"   Port: {settings.port}")
    logger.info(f"   Workers: {settings.workers}")
    logger.info(f"   Debug: {features.is_debug_mode()}")
    
    # Start server
    try:
        import uvicorn
        
        logger.info("🎯 Starting server...")
        uvicorn.run(
            "app.api.app:app",
            host=settings.host,
            port=settings.port,
            reload=features.is_debug_mode(),
            log_level="info" if features.is_debug_mode() else "warning",
            access_log=features.is_debug_mode(),
            loop="asyncio",
            workers=1 if features.is_debug_mode() else settings.workers
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()