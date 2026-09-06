"""
Base schemas for ERP03 Integration Contracts.

These schemas define the contract between ERP-BACKEND and AI-BACKEND.
AI systems must ONLY use these contracts - never import ERP ORM models directly.
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Standard response envelope for all API calls."""
    success: bool = Field(..., description="Whether the request succeeded")
    message: str = Field(default="", description="Human-readable status message")
    correlation_id: str = Field(..., description="Request correlation ID for tracing")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseResponse):
    """Error response schema."""
    success: bool = False
    error_code: str = Field(..., description="Machine-readable error code")
    error_details: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional error context"
    )


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether more pages exist")
    has_prev: bool = Field(..., description="Whether previous pages exist")


# ============================================================================
# User & Authentication Schemas
# ============================================================================

class UserSchema(BaseModel):
    """User entity schema."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    role_ids: List[int] = Field(default_factory=list)


class UserCreateSchema(BaseModel):
    """Schema for creating a user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)


class UserUpdateSchema(BaseModel):
    """Schema for updating a user."""
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


# ============================================================================
# Role & Permission Schemas
# ============================================================================

class RoleSchema(BaseModel):
    """Role entity schema."""
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime


class PermissionSchema(BaseModel):
    """Permission entity schema."""
    id: int
    name: str
    resource: str
    action: str
    description: Optional[str] = None


# ============================================================================
# Common Entity Schemas
# ============================================================================

class BaseEntitySchema(BaseModel):
    """Base schema for all entities with standard fields."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    modified_by: Optional[int] = None


# ============================================================================
# Event Envelope Schema
# ============================================================================

class EventEnvelope(BaseModel):
    """Standard event envelope for all ERP events."""
    event_id: str = Field(..., description="Unique event identifier (UUID)")
    event_type: str = Field(..., description="Event type in format 'resource.action'")
    event_version: str = Field(default="v1", description="Event schema version")
    source: str = Field(..., description="Source system identifier")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(..., description="Event payload data")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Health Check Schema
# ============================================================================

class HealthStatusSchema(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Overall health status (healthy/degraded/unhealthy)")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Component health details"
    )
