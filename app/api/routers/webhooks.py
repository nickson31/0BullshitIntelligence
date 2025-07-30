"""
Webhooks router - Receive updates from main repository
"""

from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.models import ResponseModel
from app.services.sync_service import sync_service
from app.services.webhook_validator import webhook_validator

logger = get_logger(__name__)
router = APIRouter()


@router.post("/user_update", response_model=ResponseModel)
async def handle_user_update(
    payload: Dict[str, Any],
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle user data updates from main repository
    
    Receives user context updates, subscription changes, etc.
    """
    try:
        # Validate webhook signature
        await webhook_validator.validate_signature(
            payload=payload,
            signature=x_webhook_signature,
            request=request
        )
        
        logger.info("Processing user update webhook", 
                   user_id=payload.get("user_id"),
                   update_type=payload.get("type"))
        
        # Process the user update
        await sync_service.process_user_update(payload)
        
        return ResponseModel(
            success=True,
            message="User update processed successfully",
            data={"processed_at": datetime.utcnow().isoformat()}
        )
        
    except ValueError as e:
        logger.warning(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"User update webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/project_update", response_model=ResponseModel)
async def handle_project_update(
    payload: Dict[str, Any],
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle project data updates from main repository
    """
    try:
        # Validate webhook signature
        await webhook_validator.validate_signature(
            payload=payload,
            signature=x_webhook_signature,
            request=request
        )
        
        logger.info("Processing project update webhook",
                   project_id=payload.get("project_id"),
                   user_id=payload.get("user_id"),
                   update_type=payload.get("type"))
        
        # Process the project update
        await sync_service.process_project_update(payload)
        
        return ResponseModel(
            success=True,
            message="Project update processed successfully",
            data={"processed_at": datetime.utcnow().isoformat()}
        )
        
    except ValueError as e:
        logger.warning(f"Invalid project webhook payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Project update webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/subscription_update", response_model=ResponseModel)
async def handle_subscription_update(
    payload: Dict[str, Any],
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle subscription/plan updates from main repository
    
    Updates user plan info for upselling system
    """
    try:
        # Validate webhook signature
        await webhook_validator.validate_signature(
            payload=payload,
            signature=x_webhook_signature,
            request=request
        )
        
        logger.info("Processing subscription update webhook",
                   user_id=payload.get("user_id"),
                   plan=payload.get("plan"),
                   credits=payload.get("credits"))
        
        # Process the subscription update
        await sync_service.process_subscription_update(payload)
        
        return ResponseModel(
            success=True,
            message="Subscription update processed successfully",
            data={"processed_at": datetime.utcnow().isoformat()}
        )
        
    except ValueError as e:
        logger.warning(f"Invalid subscription webhook payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Subscription update webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/database_sync", response_model=ResponseModel)
async def handle_database_sync(
    payload: Dict[str, Any],
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle database synchronization updates
    
    Syncs shared tables between main repository and this microservice
    """
    try:
        # Validate webhook signature
        await webhook_validator.validate_signature(
            payload=payload,
            signature=x_webhook_signature,
            request=request
        )
        
        logger.info("Processing database sync webhook",
                   table=payload.get("table"),
                   operation=payload.get("operation"),
                   record_count=payload.get("record_count", 1))
        
        # Process the database sync
        await sync_service.process_database_sync(payload)
        
        return ResponseModel(
            success=True,
            message="Database sync processed successfully",
            data={"processed_at": datetime.utcnow().isoformat()}
        )
        
    except ValueError as e:
        logger.warning(f"Invalid database sync webhook payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Database sync webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/outreach_results", response_model=ResponseModel)
async def handle_outreach_results(
    payload: Dict[str, Any],
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle outreach campaign results from main repository
    
    Receives feedback on search results used in campaigns
    """
    try:
        # Validate webhook signature
        await webhook_validator.validate_signature(
            payload=payload,
            signature=x_webhook_signature,
            request=request
        )
        
        logger.info("Processing outreach results webhook",
                   campaign_id=payload.get("campaign_id"),
                   search_id=payload.get("search_id"),
                   results_count=payload.get("results_count"))
        
        # Process the outreach results
        await sync_service.process_outreach_results(payload)
        
        return ResponseModel(
            success=True,
            message="Outreach results processed successfully",
            data={"processed_at": datetime.utcnow().isoformat()}
        )
        
    except ValueError as e:
        logger.warning(f"Invalid outreach results webhook payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Outreach results webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.get("/health", response_model=ResponseModel)
async def webhook_health_check():
    """Health check for webhook processing"""
    try:
        # Check if sync service is healthy
        sync_healthy = await sync_service.health_check()
        
        return ResponseModel(
            success=sync_healthy,
            message="Webhook processing health check",
            data={
                "sync_service": "healthy" if sync_healthy else "unhealthy",
                "webhook_validator": "healthy",  # Simple service, always healthy
                "overall_status": "healthy" if sync_healthy else "degraded"
            }
        )
        
    except Exception as e:
        logger.error(f"Webhook health check failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook health check failed")


@router.post("/test", response_model=ResponseModel)
async def test_webhook():
    """Test webhook endpoint (only in debug mode)"""
    from app.core.config import features
    
    if not features.is_debug_mode():
        raise HTTPException(status_code=404, detail="Endpoint not available")
    
    return ResponseModel(
        success=True,
        message="Webhook test successful",
        data={
            "timestamp": datetime.utcnow().isoformat(),
            "service": "0BullshitIntelligence",
            "status": "webhook_received"
        }
    )