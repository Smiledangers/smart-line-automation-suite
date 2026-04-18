"""
Security middleware for rate limiting and security headers.
"""
import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    For production, use Redis-based rate limiting.
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self._requests: Dict[str, list] = defaultdict(list)
    
    def _cleanup_old_requests(self, key: str) -> None:
        """Remove requests older than 1 minute."""
        cutoff = time.time() - 60
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
    
    def check(self, key: str) -> bool:
        """Check if request is allowed."""
        self._cleanup_old_requests(key)
        
        if len(self._requests[key]) >= self.requests_per_minute:
            return False
        
        self._requests[key].append(time.time())
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for this minute."""
        self._cleanup_old_requests(key)
        return max(0, self.requests_per_minute - len(self._requests[key]))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting based on IP address.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute)
        # Endpoints to exclude from rate limiting
        self.exclude_paths = ["/health", "/ready", "/startup", "/metrics"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self.rate_limiter.check(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )
        
        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining(client_ip)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding security headers to responses.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


def create_rate_limiter(requests_per_minute: int = 60) -> RateLimitMiddleware:
    """Factory function to create rate limiter middleware."""
    return lambda app: RateLimitMiddleware(app, requests_per_minute)