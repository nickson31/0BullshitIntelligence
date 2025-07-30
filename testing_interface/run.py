#!/usr/bin/env python3
"""
0BullshitIntelligence Testing Interface - Run Script
"""

import sys
import os
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import supabase
        import google.generativeai
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please install dependencies: pip install -r requirements.txt")
        return False

def check_environment():
    """Check if environment variables are set"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("📄 Please copy .env.example to .env and configure your credentials")
        return False
    
    print("✅ .env file found")
    return True

def main():
    """Main function to run the testing interface"""
    print("🚀 0BullshitIntelligence Testing Interface")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Import and run the app
    try:
        from app import app
        import uvicorn
        from config import settings
        
        print(f"🌐 Starting server on http://{settings.HOST}:{settings.PORT}")
        print(f"📚 API documentation available at http://{settings.HOST}:{settings.PORT}/docs")
        print("🔗 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        uvicorn.run(
            "app:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()