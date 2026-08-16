"""
ERP Client Package for AI-BACKEND.

This package provides HTTP clients for safe communication with ERP-BACKEND.
"""

from .client import (
    ERPClient,
    ERPSyncClient,
    ERPClientError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    CircuitBreakerOpen,
    CircuitBreaker,
)

__all__ = [
    "ERPClient",
    "ERPSyncClient",
    "ERPClientError",
    "AuthenticationError",
    "ValidationError",
    "RateLimitError",
    "CircuitBreakerOpen",
    "CircuitBreaker",
]
