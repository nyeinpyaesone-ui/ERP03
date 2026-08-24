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
        """
        Initialize an application exception with structured error information.
        
        Parameters:
            message (str): Human-readable error message.
            error_code (str): Application-specific error code.
            details (Optional[Dict[str, Any]]): Additional error details.
        """
        self.message = message
        self.error_code = error_code
        self.details = details
        self.correlation_id = str(uuid.uuid4())
        super().__init__(self.message)

class NotFoundException(AppException):
    """Resource not found (404)"""
    def __init__(self, resource: str, identifier: str, details: Optional[Dict[str, Any]] = None):
        """
        Create an exception describing a resource that could not be found.
        
        Parameters:
            resource (str): Name of the resource.
            identifier (str): Identifier of the missing resource.
            details (Optional[Dict[str, Any]]): Additional error details.
        """
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, error_code="RESOURCE_NOT_FOUND", details=details)

class ValidationException(AppException):
    """Validation failed (400)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize an exception for input validation failures.
        
        Parameters:
            message (str): Description of the validation failure.
            details (Optional[Dict[str, Any]]): Additional validation error details.
        """
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)

class ConflictException(AppException):
    """Resource conflict (409)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize an exception for a resource conflict.
        
        Parameters:
            message (str): Description of the conflict.
            details (Optional[Dict[str, Any]]): Additional context about the conflict.
        """
        super().__init__(message, error_code="RESOURCE_CONFLICT", details=details)

class UnauthorizedException(AppException):
    """Authentication required (401)"""
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        """Initialize an exception indicating that authentication is required.
        
        Parameters:
            message (str): Error message, defaulting to "Authentication required".
            details (Optional[Dict[str, Any]]): Additional error context.
        """
        super().__init__(message, error_code="UNAUTHORIZED", details=details)

class ForbiddenException(AppException):
    """Access denied (403)"""
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        """Initialize an exception for denied access.
        
        Parameters:
            message (str): The error message.
            details (Optional[Dict[str, Any]]): Additional error details.
        """
        super().__init__(message, error_code="FORBIDDEN", details=details)

class DatabaseException(AppException):
    """Database operation failed (500)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Create a database operation failure exception.
        
        Parameters:
            message (str): Description of the database failure.
            details (Optional[Dict[str, Any]]): Additional structured information about the failure.
        """
        super().__init__(message, error_code="DATABASE_ERROR", details=details)

class TransactionRollbackException(AppException):
    """Transaction rolled back (500) - Specific for Issue #56"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize an exception indicating that a transaction was rolled back.
        
        Parameters:
            message (str): Description of the rollback.
            details (Optional[Dict[str, Any]]): Additional error details.
        """
        super().__init__(message, error_code="TRANSACTION_ROLLBACK", details=details)
