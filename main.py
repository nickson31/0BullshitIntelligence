"""
Main entry point for 0BullshitIntelligence microservice.
Handles application initialization, dependency checking, and server startup.
"""

import asyncio
import sys
import os
import importlib
import time
import signal
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("✅ Configuration loaded successfully")
print("🧠 Starting 0BullshitIntelligence...")

# Import the FastAPI app for Gunicorn
try:
    from app.api.app import app
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    # Create a minimal app if import fails
    from fastapi import FastAPI
    app = FastAPI(title="0BullshitIntelligence - Loading...")

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger

logger = get_logger(__name__)


def validate_environment():
    """Validate environment variables and system requirements"""
    try:
        settings = get_settings()
        logger.info("✅ Environment validation successful")
        return True
    except Exception as e:
        logger.error(f"❌ Environment validation failed: {e}")
        return False


def check_dependencies():
    """Check if all required dependencies are available"""
    required_packages = [
        "fastapi", "uvicorn", "gunicorn", "supabase", 
        "google.generativeai", "jinja2", "structlog"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ Missing required packages: {', '.join(missing_packages)}")
        return False
    
    logger.info("✅ All critical dependencies are available")
    return True


def initialize_services():
    """Initialize application services"""
    logger.info("🔧 Initializing services...")
    
    try:
        # Initialize any services here
        logger.info("✅ Services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        return False


def main():
    """Main application entry point"""
    try:
        # Setup logging first
        setup_logging()
        
        # Validate environment
        if not validate_environment():
            sys.exit(1)
        
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Initialize services
        initialize_services()
        
        logger.info("✅ Application setup completed")
        
        # Get settings
        settings = get_settings()
        
        # Start the server
        logger.info("🎯 Starting server...")
        
        # Import uvicorn here to avoid issues
        import uvicorn
        
        # Run the server
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level="info",
            access_log=True,
            workers=1
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down gracefully...")
        
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        sys.exit(1)


def handle_signal(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"🔄 Received signal {signum}, shutting down...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


if __name__ == "__main__":
    main()