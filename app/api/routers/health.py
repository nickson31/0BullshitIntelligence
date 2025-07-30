"""
Health check endpoints for monitoring system status
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import asyncio

from app.core.logging import get_logger
from app.models import ResponseModel

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=ResponseModel)
async def health_check():
    """Basic health check endpoint"""
    return ResponseModel(
        success=True,
        message="Service is healthy",
        data={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "0BullshitIntelligence"
        }
    )


@router.get("/detailed", response_model=ResponseModel)
async def detailed_health_check():
    """Detailed health check with component status"""
    try:
        health_checks = []
        
        # Check database connectivity
        try:
            from app.database import database_manager
            db_healthy = await database_manager.health_check()
            health_checks.append({"component": "database", "healthy": db_healthy})
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_checks.append({"component": "database", "healthy": False, "error": str(e)})
        
        # Check AI systems
        try:
            from app.ai_systems import ai_coordinator
            ai_healthy = await ai_coordinator.health_check()
            health_checks.append({"component": "ai_systems", "healthy": ai_healthy})
        except Exception as e:
            logger.error(f"AI systems health check failed: {e}")
            health_checks.append({"component": "ai_systems", "healthy": False, "error": str(e)})
        
        # Check search engines
        try:
            from app.search import search_coordinator
            search_healthy = await search_coordinator.health_check()
            health_checks.append({"component": "search_engines", "healthy": search_healthy})
        except Exception as e:
            logger.error(f"Search engines health check failed: {e}")
            health_checks.append({"component": "search_engines", "healthy": False, "error": str(e)})
        
        overall_healthy = all(check["healthy"] for check in health_checks)
        
        return ResponseModel(
            success=overall_healthy,
            message="Detailed health check completed",
            data={
                "overall_status": "healthy" if overall_healthy else "degraded",
                "components": health_checks,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/ready", response_model=ResponseModel)
async def readiness_check():
    """Readiness check for container orchestration"""
    try:
        # Check if all critical services are ready
        from app.database import database_manager
        from app.ai_systems import ai_coordinator
        
        await database_manager.health_check()
        await ai_coordinator.health_check()
        
        return ResponseModel(
            success=True,
            message="Service is ready",
            data={"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        )
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live", response_model=ResponseModel)
async def liveness_check():
    """Liveness check for container orchestration"""
    return ResponseModel(
        success=True,
        message="Service is alive",
        data={"status": "alive", "timestamp": datetime.utcnow().isoformat()}
    )