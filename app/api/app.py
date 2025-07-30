"""
Main FastAPI application for 0BullshitIntelligence.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.core.logging import get_logger, performance_logger
from app.models import ResponseModel, ErrorResponse
from .routers import chat_router, health_router
from .middleware import LoggingMiddleware, RateLimitMiddleware
from .websockets import websocket_manager

logger = get_logger(__name__)
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="0BullshitIntelligence",
    description="AI-powered chat application with modern UI and Gemini integration",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# ==========================================
# MIDDLEWARE CONFIGURATION
# ==========================================

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# ==========================================
# EXCEPTION HANDLERS
# ==========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with structured responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            success=False,
            message=str(exc),
            error_code="VALIDATION_ERROR"
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            message="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )

# ==========================================
# ROUTE SETUP
# ==========================================

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Health and status endpoints
app.include_router(health_router, prefix="/health", tags=["Health"])

# Core API endpoints
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])

# ==========================================
# UI ROUTES
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main chat interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Chat interface page"""
    return templates.TemplateResponse("chat.html", {"request": request})

# ==========================================
# WEBSOCKET ENDPOINTS
# ==========================================

@app.websocket("/ws/chat/{conversation_id}")
async def chat_websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat communication"""
    try:
        await websocket_manager.connect(websocket, conversation_id)
        logger.info(f"WebSocket connected for conversation {conversation_id}")
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message and broadcast to connected clients
            await websocket_manager.handle_message(conversation_id, data)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
        await websocket_manager.disconnect(websocket, conversation_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket, conversation_id)

# ==========================================
# APPLICATION LIFECYCLE
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 Application starting up...")
    
    # Initialize services
    try:
        # Add any startup logic here
        logger.info("✅ Startup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("🛑 Application shutting down...")
    
    # Cleanup services
    try:
        # Add any cleanup logic here
        logger.info("✅ Shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# ==========================================
# HEALTH CHECK ENDPOINT
# ==========================================

@app.get("/api/status")
async def status_check():
    """Application status check"""
    return ResponseModel(
        success=True,
        message="0BullshitIntelligence is running",
        data={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "environment": settings.environment
        }
    )