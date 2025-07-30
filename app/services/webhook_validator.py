"""
Webhook Validator - Validates webhook signatures and authenticity
"""

import hmac
import hashlib
from typing import Dict, Any, Optional

from fastapi import Request, HTTPException
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebhookValidator:
    """
    Validates webhook signatures to ensure they come from authorized sources
    """
    
    def __init__(self):
        pass
    
    async def validate_signature(
        self,
        payload: Dict[str, Any],
        signature: Optional[str],
        request: Request
    ) -> bool:
        """Validate webhook signature"""
        
        try:
            # For development, skip signature validation if no service key configured
            if not settings.service_api_key:
                logger.warning("Service API key not configured - skipping webhook validation")
                return True
            
            if not signature:
                logger.warning("No webhook signature provided")
                raise HTTPException(status_code=401, detail="Webhook signature required")
            
            # Get raw body for signature verification
            body = await request.body()
            
            # Calculate expected signature
            expected_signature = self._calculate_signature(body, settings.service_api_key)
            
            # Compare signatures
            if not self._secure_compare(signature, expected_signature):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
            
            logger.debug("Webhook signature validated successfully")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Webhook signature validation failed: {e}")
            raise HTTPException(status_code=500, detail="Signature validation error")
    
    def _calculate_signature(self, body: bytes, secret: str) -> str:
        """Calculate HMAC signature for webhook payload"""
        
        # Create HMAC signature using SHA256
        signature = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    def _secure_compare(self, signature1: str, signature2: str) -> bool:
        """Securely compare two signatures to prevent timing attacks"""
        
        if len(signature1) != len(signature2):
            return False
        
        return hmac.compare_digest(signature1, signature2)


# Create singleton instance
webhook_validator = WebhookValidator()