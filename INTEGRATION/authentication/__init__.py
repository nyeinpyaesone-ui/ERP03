"""
Authentication Package for ERP03 Integration.

This package provides JWT validation and API key management for secure
service-to-service communication.
"""

from .auth import (
    JWTValidator,
    APIKeyManager,
    TokenType,
    TokenPayload,
    extract_token_from_header,
    extract_api_key_from_header,
)

__all__ = [
    "JWTValidator",
    "APIKeyManager",
    "TokenType",
    "TokenPayload",
    "extract_token_from_header",
    "extract_api_key_from_header",
]
