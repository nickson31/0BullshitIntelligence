"""
0BullshitIntelligence Testing Interface
FastAPI Application
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os

from config import settings
from database import db_manager

# Initialize FastAPI app
app = FastAPI(
    title="0BullshitIntelligence Testing Interface",
    description="Testing and monitoring interface for the AI chat system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Pydantic models for API requests
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 100

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and AI connections on startup"""
    if not settings.validate():
        print("❌ Configuration validation failed!")
        return
    
    print("🚀 Starting 0BullshitIntelligence Testing Interface...")
    
    # Initialize database connection
    success = await db_manager.initialize()
    if success:
        print("✅ Testing interface started successfully!")
        print(f"🌐 Access the interface at: http://{settings.HOST}:{settings.PORT}")
        print(f"📚 API Documentation at: http://{settings.HOST}:{settings.PORT}/docs")
    else:
        print("❌ Failed to initialize database connections")

# Root endpoint - Main interface
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main testing interface"""
    return templates.TemplateResponse("index.html", {"request": request})

# Health and connection endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/test-connection")
async def test_connection():
    """Test database and AI connections"""
    try:
        result = await db_manager.test_connection()
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Dashboard API endpoints
@app.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        stats = await db_manager.get_dashboard_stats()
        return stats
    except Exception as e:
        return {"error": str(e)}

# Chat API endpoints
@app.post("/api/simulate-chat")
async def simulate_chat(chat_message: ChatMessage):
    """Simulate a chat message through the AI system"""
    try:
        result = await db_manager.simulate_chat_message(
            message=chat_message.message,
            user_id=chat_message.user_id
        )
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/conversations")
async def get_conversations(limit: int = Query(20, description="Number of conversations to retrieve")):
    """Get recent conversations"""
    try:
        conversations = await db_manager.get_recent_conversations(limit=limit)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get messages for a specific conversation"""
    try:
        messages = await db_manager.get_conversation_messages(conversation_id)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search data endpoints
@app.get("/api/search-results")
async def get_search_results(limit: int = Query(50, description="Number of search results to retrieve")):
    """Get recent search results"""
    try:
        results = await db_manager.get_search_results(limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Investor data endpoints
@app.get("/api/investors")
async def get_investors(limit: int = Query(100, description="Number of investors to retrieve")):
    """Get angel investors data"""
    try:
        investors = await db_manager.get_investor_data(limit=limit)
        return investors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investors/search")
async def search_investors(q: str = Query(..., description="Search term"), limit: int = Query(100, description="Number of results")):
    """Search angel investors"""
    try:
        investors = await db_manager.get_investor_data(search_term=q, limit=limit)
        return investors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Fund data endpoints
@app.get("/api/funds")
async def get_funds(limit: int = Query(100, description="Number of funds to retrieve")):
    """Get investment funds data"""
    try:
        funds = await db_manager.get_fund_data(limit=limit)
        return funds
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/funds/search")
async def search_funds(q: str = Query(..., description="Search term"), limit: int = Query(100, description="Number of results")):
    """Search investment funds"""
    try:
        funds = await db_manager.get_fund_data(search_term=q, limit=limit)
        return funds
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API Info endpoint
@app.get("/api/info")
async def get_api_info():
    """Get API information and configuration"""
    return {
        "app_name": "0BullshitIntelligence Testing Interface",
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production",
        "supabase_url": settings.SUPABASE_URL,
        "gemini_model": settings.GEMINI_MODEL,
        "endpoints": {
            "dashboard": "/api/dashboard-stats",
            "chat_simulation": "/api/simulate-chat",
            "conversations": "/api/conversations",
            "search_results": "/api/search-results",
            "investors": "/api/investors",
            "funds": "/api/funds"
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Main entry point
if __name__ == "__main__":
    print("🔧 Starting 0BullshitIntelligence Testing Interface...")
    print(f"📍 Configuration:")
    print(f"   - Host: {settings.HOST}")
    print(f"   - Port: {settings.PORT}")
    print(f"   - Debug: {settings.DEBUG}")
    print(f"   - Supabase URL: {settings.SUPABASE_URL}")
    print(f"   - Gemini Model: {settings.GEMINI_MODEL}")
    
    # Use environment PORT for Render compatibility
    port = int(os.environ.get("PORT", settings.PORT))
    
    # Run with uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )