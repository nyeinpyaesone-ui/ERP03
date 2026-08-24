"""
Rate limiting middleware using slowapi.
Provides configurable rate limits for API endpoints.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import time


class RateLimiter:
    """
    Configurable rate limiter for API endpoints.
    
    Usage:
        limiter = RateLimiter()
        app.state.limiter = limiter.limiter
        
        @router.post("/login")
        @limiter.limit("5/minute")
        async def login(...):
            ...
    """
    
    def __init__(self, default_limit: str = "100/minute"):
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[default_limit],
            storage_uri="memory://"
        )
        
    def setup_exception_handler(self, app):
        """Setup exception handler for rate limit exceeded errors."""
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce stricter rate limits on authentication endpoints.
    Prevents brute force attacks on login/register endpoints.
    """
    
    def __init__(self, app, max_attempts: int = 5, window_seconds: int = 60):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: dict[str, list[float]] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Only apply to auth endpoints
        if not request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old attempts
        if client_ip in self.attempts:
            self.attempts[client_ip] = [
                t for t in self.attempts[client_ip]
                if current_time - t < self.window_seconds
            ]
        else:
            self.attempts[client_ip] = []
        
        # Check if rate limit exceeded
        if len(self.attempts[client_ip]) >= self.max_attempts:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": self.window_seconds
                }
            )
        
        # Record this attempt
        self.attempts[client_ip].append(current_time)
        
        # Proceed with request
        response = await call_next(request)
        return response
