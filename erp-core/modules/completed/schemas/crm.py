"""Pydantic schemas for CRM models."""
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, date


class CompanyBase(BaseModel):
    name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    company_id: Optional[int] = None
    status: str = "lead"
    source: Optional[str] = None
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    company_id: Optional[int] = None
    status: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assigned_to: Optional[int] = None
    lifetime_value: float = 0.0
    last_activity: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DealBase(BaseModel):
    title: str
    contact_id: Optional[int] = None
    company_id: Optional[int] = None
    value: float = 0
    stage: str = "prospect"
    probability: int = 0
    expected_close_date: Optional[date] = None
    description: Optional[str] = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    description: Optional[str] = None


class DealResponse(DealBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assigned_to: Optional[int] = None
    actual_close_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
