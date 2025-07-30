"""
Rate limiting middleware
"""

import time
import asyncio
from typing import Dict, Tuple
from collections import defaultdict, deque

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Rate limit storage: {client_id: deque of timestamps}
        self.request_times: Dict[str, deque] = defaultdict(deque)
        
        # Rate limits configuration
        self.rate_limits = {
            "per_minute": settings.rate_limit_per_minute,
            "per_hour": settings.rate_limit_per_hour
        }
        
        # Exempt paths from rate limiting
        self.exempt_paths = {
            "/health",
            "/health/live", 
            "/health/ready",
            "/",
            "/status"
        }
        
        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up old entries"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_entries())
    
    async def _cleanup_old_entries(self):
        """Cleanup old entries every 5 minutes"""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                current_time = time.time()
                
                # Remove entries older than 1 hour
                cleanup_cutoff = current_time - 3600
                
                for client_id in list(self.request_times.keys()):
                    timestamps = self.request_times[client_id]
                    
                    # Remove old timestamps
                    while timestamps and timestamps[0] < cleanup_cutoff:
                        timestamps.popleft()
                    
                    # Remove empty entries
                    if not timestamps:
                        del self.request_times[client_id]
                
                logger.debug(f"Rate limit cleanup completed. Active clients: {len(self.request_times)}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")
    
    async def dispatch(self, request: Request, call_next):
        """Check rate limits and process request"""
        
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Check rate limits
        try:
            self._check_rate_limits(client_id, current_time)
        except HTTPException as e:
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                path=request.url.path,
                method=request.method,
                limit_type=e.detail
            )
            raise
        
        # Record the request
        self.request_times[client_id].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, client_id, current_time)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        
        # Try to get user ID from JWT token (if authenticated)
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                import jwt
                token = auth_header.split(" ")[1]
                payload = jwt.decode(
                    token, 
                    settings.jwt_secret_key, 
                    algorithms=[settings.jwt_algorithm],
                    options={"verify_exp": False}  # Don't verify expiration for rate limiting
                )
                user_id = payload.get("user_id")
                if user_id:
                    return f"user:{user_id}"
            except:
                pass  # Fall back to IP-based rate limiting
        
        # Fall back to IP address
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_rate_limits(self, client_id: str, current_time: float):
        """Check if client has exceeded rate limits"""
        
        timestamps = self.request_times[client_id]
        
        # Check per-minute limit
        minute_cutoff = current_time - 60
        minute_requests = sum(1 for ts in timestamps if ts > minute_cutoff)
        
        if minute_requests >= self.rate_limits["per_minute"]:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: too many requests per minute"
            )
        
        # Check per-hour limit
        hour_cutoff = current_time - 3600
        hour_requests = sum(1 for ts in timestamps if ts > hour_cutoff)
        
        if hour_requests >= self.rate_limits["per_hour"]:
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded: too many requests per hour"
            )
    
    def _add_rate_limit_headers(self, response, client_id: str, current_time: float):
        """Add rate limit information to response headers"""
        
        timestamps = self.request_times[client_id]
        
        # Calculate remaining requests
        minute_cutoff = current_time - 60
        minute_requests = sum(1 for ts in timestamps if ts > minute_cutoff)
        minute_remaining = max(0, self.rate_limits["per_minute"] - minute_requests)
        
        hour_cutoff = current_time - 3600
        hour_requests = sum(1 for ts in timestamps if ts > hour_cutoff)
        hour_remaining = max(0, self.rate_limits["per_hour"] - hour_requests)
        
        # Add headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.rate_limits["per_minute"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(minute_remaining)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.rate_limits["per_hour"]) 
        response.headers["X-RateLimit-Remaining-Hour"] = str(hour_remaining)
        
        # Add reset time (next minute)
        reset_time = int(current_time) + 60
        response.headers["X-RateLimit-Reset"] = str(reset_time)
    
    def __del__(self):
        """Clean up background task"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()