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
        """
        Initialize the rate limiter with a default request limit.
        
        Parameters:
        	default_limit (str): The default rate limit applied to requests.
        """
        self.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[default_limit],
            storage_uri="memory://"
        )
        
    def setup_exception_handler(self, app):
        """
        Register the application's handler for rate-limit-exceeded errors.
        
        Parameters:
            app: The application to configure.
        """
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce stricter rate limits on authentication endpoints.
    Prevents brute force attacks on login/register endpoints.
    """
    
    def __init__(self, app, max_attempts: int = 5, window_seconds: int = 60):
        """Configure authentication request rate limiting for the middleware.
        
        Parameters:
        	max_attempts (int): Maximum number of authentication attempts allowed within the time window.
        	window_seconds (int): Duration of the rate-limiting window in seconds.
        """
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: dict[str, list[float]] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Only apply to auth endpoints
        """
        Apply an in-memory request limit to authentication endpoints.
        
        Parameters:
            request (Request): The incoming HTTP request.
            call_next: The handler that processes requests allowed through the middleware.
        
        Returns:
            The downstream response, or an HTTP 429 response when the client exceeds the configured limit.
        """
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
