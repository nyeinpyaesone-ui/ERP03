"""
Standardized error handling middleware for ERP API.

This module provides:
- Centralized exception handling
- Standardized error response schema
- Correlation ID tracking
- Error code taxonomy
"""

import logging
import time
import uuid
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger("erp03.errors")


class ERPException(Exception):
    """Base exception for ERP system."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationException(ERPException):
    """Authentication failed."""
    
    def __init__(self, message: str = "Authentication required", code: str = "AUTH_REQUIRED"):
        super().__init__(message=message, code=code, status_code=401)


class AuthorizationException(ERPException):
    """Authorization failed."""
    
    def __init__(self, message: str = "Forbidden", code: str = "FORBIDDEN"):
        super().__init__(message=message, code=code, status_code=403)


class ValidationException(ERPException):
    """Validation failed."""
    
    def __init__(
        self,
        message: str = "Validation error",
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=400, details=details)


class NotFoundException(ERPException):
    """Resource not found."""
    
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(message=message, code=code, status_code=404)


class ConflictException(ERPException):
    """Resource conflict."""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=409, details=details)


class RateLimitException(ERPException):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", code: str = "RATE_LIMITED"):
        super().__init__(message=message, code=code, status_code=429)


class ServiceException(ERPException):
    """External service error."""
    
    def __init__(
        self,
        message: str = "Service unavailable",
        code: str = "SERVICE_UNAVAILABLE",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, code=code, status_code=503, details=details)


def create_error_response(
    code: str,
    message: str,
    request: Request,
    correlation_id: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
            "status_code": status_code
        }
    }


async def get_correlation_id(request: Request) -> str:
    """Extract or generate correlation ID from request."""
    return request.headers.get("X-Request-ID") or str(uuid.uuid4())


async def error_handler_middleware(request: Request, call_next):
    """
    Middleware to handle all exceptions and return standardized error responses.
    
    This middleware:
    - Catches all unhandled exceptions
    - Logs errors with correlation ID
    - Returns standardized error response
    - Masks sensitive information
    """
    correlation_id = await get_correlation_id(request)
    
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation_id
        return response
    except ERPException as e:
        logger.warning(
            f"ERP exception: {e.code} - {e.message}",
            extra={
                "correlation_id": correlation_id,
                "error_code": e.code,
                "path": request.url.path,
                "method": request.method
            }
        )
        error_response = create_error_response(
            code=e.code,
            message=e.message,
            request=request,
            correlation_id=correlation_id,
            details=e.details,
            status_code=e.status_code
        )
        return JSONResponse(
            status_code=e.status_code,
            content=error_response,
            headers={"X-Request-ID": correlation_id}
        )
    except RequestValidationError as e:
        # Format Pydantic validation errors
        field_errors = []
        for error in e.errors():
            field_errors.append({
                "field": ".".join(str(x) for x in error.get("loc", [])),
                "error": error.get("type", "invalid"),
                "message": error.get("msg", "Invalid value")
            })
        
        logger.warning(
            f"Validation error: {len(field_errors)} field(s)",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        error_response = create_error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            request=request,
            correlation_id=correlation_id,
            details={"fields": field_errors},
            status_code=400
        )
        return JSONResponse(
            status_code=400,
            content=error_response,
            headers={"X-Request-ID": correlation_id}
        )
    except HTTPException as e:
        # Map HTTPException to our error format
        code_map = {
            401: "AUTH_REQUIRED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            429: "RATE_LIMITED"
        }
        error_code = code_map.get(e.status_code, "INTERNAL_ERROR")
        
        logger.warning(
            f"HTTP exception: {e.status_code} - {e.detail}",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        error_response = create_error_response(
            code=error_code,
            message=e.detail if isinstance(e.detail, str) else "HTTP error",
            request=request,
            correlation_id=correlation_id,
            status_code=e.status_code
        )
        return JSONResponse(
            status_code=e.status_code,
            content=error_response,
            headers={"X-Request-ID": correlation_id}
        )
    except SQLAlchemyError as e:
        # Database errors - never expose raw SQL
        logger.error(
            f"Database error",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        # Check for specific DB errors
        if isinstance(e, IntegrityError):
            error_response = create_error_response(
                code="CONSTRAINT_VIOLATION",
                message="Database constraint violation",
                request=request,
                correlation_id=correlation_id,
                status_code=409
            )
            return JSONResponse(
                status_code=409,
                content=error_response,
                headers={"X-Request-ID": correlation_id}
            )
        
        error_response = create_error_response(
            code="DATABASE_ERROR",
            message="Database operation failed",
            request=request,
            correlation_id=correlation_id,
            status_code=500
        )
        return JSONResponse(
            status_code=500,
            content=error_response,
            headers={"X-Request-ID": correlation_id}
        )
    except Exception as e:
        # Catch-all for unhandled exceptions
        logger.exception(
            f"Unhandled exception",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        error_response = create_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            request=request,
            correlation_id=correlation_id,
            status_code=500
        )
        return JSONResponse(
            status_code=500,
            content=error_response,
            headers={"X-Request-ID": correlation_id}
        )


def register_exception_handlers(app: FastAPI):
    """Register exception handlers with FastAPI app."""
    
    @app.exception_handler(ERPException)
    async def erp_exception_handler(request: Request, exc: ERPException):
        correlation_id = await get_correlation_id(request)
        error_response = create_error_response(
            code=exc.code,
            message=exc.message,
            request=request,
            correlation_id=correlation_id,
            details=exc.details,
            status_code=exc.status_code
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers={"X-Request-ID": correlation_id}
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        correlation_id = await get_correlation_id(request)
        field_errors = []
        for error in exc.errors():
            field_errors.append({
                "field": ".".join(str(x) for x in error.get("loc", [])),
                "error": error.get("type", "invalid"),
                "message": error.get("msg", "Invalid value")
            })
        
        error_response = create_error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            request=request,
            correlation_id=correlation_id,
            details={"fields": field_errors},
            status_code=400
        )
        return JSONResponse(
            status_code=400,
            content=error_response,
            headers={"X-Request-ID": correlation_id}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        correlation_id = await get_correlation_id(request)
        code_map = {
            401: "AUTH_REQUIRED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            429: "RATE_LIMITED"
        }
        error_code = code_map.get(exc.status_code, "INTERNAL_ERROR")
        
        error_response = create_error_response(
            code=error_code,
            message=exc.detail if isinstance(exc.detail, str) else "HTTP error",
            request=request,
            correlation_id=correlation_id,
            status_code=exc.status_code
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers={"X-Request-ID": correlation_id}
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        correlation_id = await get_correlation_id(request)
        logger.error(f"Database error", exc_info=True)
        
        if isinstance(exc, IntegrityError):
            error_response = create_error_response(
                code="CONSTRAINT_VIOLATION",
                message="Database constraint violation",
                request=request,
                correlation_id=correlation_id,
                status_code=409
            )
            return JSONResponse(status_code=409, content=error_response)
        
        error_response = create_error_response(
            code="DATABASE_ERROR",
            message="Database operation failed",
            request=request,
            correlation_id=correlation_id,
            status_code=500
        )
        return JSONResponse(status_code=500, content=error_response)
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        correlation_id = await get_correlation_id(request)
        logger.exception(f"Unhandled exception")
        
        error_response = create_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            request=request,
            correlation_id=correlation_id,
            status_code=500
        )
        return JSONResponse(status_code=500, content=error_response)
