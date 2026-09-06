"""
ERP03 Integration Contracts - Schemas Package

This package contains all Pydantic schemas used for API contracts between
ERP-BACKEND and AI-BACKEND systems.

IMPORTANT: AI systems must ONLY use these schemas. Never import ERP ORM models directly.
"""

from .base import (
    BaseResponse,
    ErrorResponse,
    PaginatedResponse,
    UserSchema,
    UserCreateSchema,
    UserUpdateSchema,
    RoleSchema,
    PermissionSchema,
    BaseEntitySchema,
    EventEnvelope,
    HealthStatusSchema,
)

from .crm import (
    CustomerSchema,
    CustomerCreateSchema,
    CustomerUpdateSchema,
    ContactSchema,
    ContactCreateSchema,
    OpportunitySchema,
    OpportunityCreateSchema,
    OpportunityUpdateSchema,
    InteractionSchema,
    InteractionCreateSchema,
)

from .inventory import (
    ProductSchema,
    ProductCreateSchema,
    ProductUpdateSchema,
    CategorySchema,
    CategoryCreateSchema,
    StockMovementSchema,
    StockMovementCreateSchema,
    LocationSchema,
    LocationCreateSchema,
    StockLevelSchema,
    StockAdjustmentSchema,
    StockAdjustmentCreateSchema,
)

__all__ = [
    # Base
    "BaseResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "UserSchema",
    "UserCreateSchema",
    "UserUpdateSchema",
    "RoleSchema",
    "PermissionSchema",
    "BaseEntitySchema",
    "EventEnvelope",
    "HealthStatusSchema",
    # CRM
    "CustomerSchema",
    "CustomerCreateSchema",
    "CustomerUpdateSchema",
    "ContactSchema",
    "ContactCreateSchema",
    "OpportunitySchema",
    "OpportunityCreateSchema",
    "OpportunityUpdateSchema",
    "InteractionSchema",
    "InteractionCreateSchema",
    # Inventory
    "ProductSchema",
    "ProductCreateSchema",
    "ProductUpdateSchema",
    "CategorySchema",
    "CategoryCreateSchema",
    "StockMovementSchema",
    "StockMovementCreateSchema",
    "LocationSchema",
    "LocationCreateSchema",
    "StockLevelSchema",
    "StockAdjustmentSchema",
    "StockAdjustmentCreateSchema",
]
