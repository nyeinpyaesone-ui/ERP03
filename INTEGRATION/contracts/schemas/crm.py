"""
CRM schemas for ERP03 Integration Contracts.

These schemas define the contract for CRM operations between ERP-BACKEND and AI-BACKEND.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class CustomerSchema(BaseModel):
    """Customer entity schema."""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    status: str = Field(default="active", description="active/inactive/lead")
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    tags: List[str] = Field(default_factory=list)


class CustomerCreateSchema(BaseModel):
    """Schema for creating a customer."""
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    status: str = Field(default="active")
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class CustomerUpdateSchema(BaseModel):
    """Schema for updating a customer."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


# ============================================================================
# Contact Schemas
# ============================================================================

class ContactSchema(BaseModel):
    """Contact entity schema (person at a customer organization)."""
    id: int
    customer_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ContactCreateSchema(BaseModel):
    """Schema for creating a contact."""
    customer_id: int
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    is_primary: bool = False
    notes: Optional[str] = None


# ============================================================================
# Opportunity Schemas
# ============================================================================

class OpportunitySchema(BaseModel):
    """Sales opportunity schema."""
    id: int
    customer_id: int
    title: str
    description: Optional[str] = None
    stage: str = Field(..., description="prospecting/qualification/proposal/negotiation/closed_won/closed_lost")
    value: float = Field(..., ge=0)
    currency: str = Field(default="USD")
    probability: int = Field(default=0, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


class OpportunityCreateSchema(BaseModel):
    """Schema for creating an opportunity."""
    customer_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    stage: str = Field(default="prospecting")
    value: float = Field(..., ge=0)
    currency: str = Field(default="USD")
    probability: int = Field(default=0, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    owner_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)


class OpportunityUpdateSchema(BaseModel):
    """Schema for updating an opportunity."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    stage: Optional[str] = None
    value: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    owner_id: Optional[int] = None
    tags: Optional[List[str]] = None


# ============================================================================
# Interaction Schemas
# ============================================================================

class InteractionType(str):
    """Types of customer interactions."""
    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"


class InteractionSchema(BaseModel):
    """Customer interaction schema."""
    id: int
    customer_id: Optional[int] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    interaction_type: str
    subject: str
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = Field(default="pending", description="pending/completed/cancelled")
    owner_id: Optional[int] = None
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InteractionCreateSchema(BaseModel):
    """Schema for creating an interaction."""
    customer_id: Optional[int] = None
    contact_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    interaction_type: str
    subject: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: str = Field(default="pending")
    metadata: Dict[str, Any] = Field(default_factory=dict)
