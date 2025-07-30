"""
Authentication middleware and dependency injection
"""

import jwt
from typing import Optional
from datetime import datetime, timedelta

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger
from app.models import UserContext

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for API requests
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.exempt_paths = {
            "/health",
            "/",
            "/status", 
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/test-interface"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle authentication"""
        
        # Skip authentication for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Skip authentication for webhook endpoints (they use signature validation)
        if request.url.path.startswith("/api/v1/webhooks"):
            return await call_next(request)
        
        # Process request normally (authentication will be handled by dependencies)
        response = await call_next(request)
        return response


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserContext:
    """
    Extract and validate user context from JWT token
    
    This dependency will be used in API endpoints to get current user info
    """
    
    # For development/testing, allow requests without authentication
    if settings.environment == "development" and not credentials:
        logger.warning("Development mode: Using mock user context")
        return UserContext(
            user_id="dev-user-001",
            email="dev@0bullshit.com",
            plan="pro",
            credits=10000,
            language="spanish",
            projects=["dev-project-001"]
        )
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Extract user information
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user_id")
        
        # Create user context
        user_context = UserContext(
            user_id=user_id,
            email=payload.get("email", ""),
            plan=payload.get("plan", "free"),
            credits=payload.get("credits", 0),
            language=payload.get("language", "spanish"),
            projects=payload.get("projects", []),
            subscription_expires=payload.get("subscription_expires"),
            features=payload.get("features", [])
        )
        
        return user_context
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


def create_jwt_token(user_context: UserContext) -> str:
    """
    Create JWT token for user context (for testing purposes)
    """
    payload = {
        "user_id": user_context.user_id,
        "email": user_context.email,
        "plan": user_context.plan,
        "credits": user_context.credits,
        "language": user_context.language,
        "projects": user_context.projects,
        "features": user_context.features,
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours),
        "iat": datetime.utcnow()
    }
    
    if user_context.subscription_expires:
        payload["subscription_expires"] = user_context.subscription_expires
    
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def validate_service_api_key(api_key: str) -> bool:
    """
    Validate service-to-service API key for webhook authentication
    """
    if not settings.service_api_key:
        logger.warning("Service API key not configured")
        return False
    
    return api_key == settings.service_api_key


class ServiceAuthDependency:
    """
    Dependency for service-to-service authentication
    """
    
    def __call__(self, request: Request) -> bool:
        api_key = request.headers.get("X-Service-API-Key")
        
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Service API key required"
            )
        
        # Validate API key
        if not settings.service_api_key or api_key != settings.service_api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid service API key"
            )
        
        return True


# Service authentication dependency instance
verify_service_auth = ServiceAuthDependency()