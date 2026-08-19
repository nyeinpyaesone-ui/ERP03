"""
Rate Limiting Middleware for API Security
Prevents brute force attacks and API abuse.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time

class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware specifically for authentication endpoints."""
    
    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Only rate limit auth endpoints
        if not request.url.path.startswith("/api/auth"):
            return await call_next(request)
        
        client_ip = request.client.host
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Clean old entries
        self.request_history[client_ip] = [
            timestamp for timestamp in self.request_history[client_ip]
            if timestamp > window_start
        ]
        
        # Check rate limit
        if len(self.request_history[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many authentication attempts. Please try again later."}
            )
        
        # Record this request
        self.request_history[client_ip].append(current_time)
        
        return await call_next(request)
