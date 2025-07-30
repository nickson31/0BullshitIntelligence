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

# Import the FastAPI app for Gunicorn
try:
    from app.api.app import app
except ImportError:
    # Create a minimal app if import fails
    from fastapi import FastAPI
    app = FastAPI(title="0BullshitIntelligence - Loading...")

from app.core.config import validate_environment, features
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
    """Main application entry point for direct execution"""
    print("🧠 Starting 0BullshitIntelligence...")
    
    # Setup logging first
    setup_logging()
    
    logger.info("🚀 Starting 0BullshitIntelligence...")
    
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
    
    logger.info("✅ Application setup completed")
    
    # Start server with uvicorn when run directly
    try:
        import uvicorn
        from app.core.config import settings
        
        logger.info("🎯 Starting server...")
        uvicorn.run(
            "main:app",
            host=settings.host if settings else "0.0.0.0",
            port=settings.port if settings else 8000,
            reload=features.is_debug_mode() if features else False,
            log_level="info",
            access_log=True,
            loop="asyncio"
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()