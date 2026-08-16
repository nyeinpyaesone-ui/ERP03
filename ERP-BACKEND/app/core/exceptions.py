"""
Custom Exception Hierarchy and Error Handling Models
Aligns with Issue #58: API Error Handling
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone

class ErrorResponse(BaseModel):
    """Standardized API Error Response"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    correlation_id: str
    timestamp: datetime

class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        self.correlation_id = str(uuid.uuid4())
        super().__init__(self.message)

class NotFoundException(AppException):
    """Resource not found (404)"""
    def __init__(self, resource: str, identifier: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, error_code="RESOURCE_NOT_FOUND", details=details)

class ValidationException(AppException):
    """Validation failed (400)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)

class ConflictException(AppException):
    """Resource conflict (409)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="RESOURCE_CONFLICT", details=details)

class UnauthorizedException(AppException):
    """Authentication required (401)"""
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="UNAUTHORIZED", details=details)

class ForbiddenException(AppException):
    """Access denied (403)"""
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="FORBIDDEN", details=details)

class DatabaseException(AppException):
    """Database operation failed (500)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="DATABASE_ERROR", details=details)

class TransactionRollbackException(AppException):
    """Transaction rolled back (500) - Specific for Issue #56"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code="TRANSACTION_ROLLBACK", details=details)
