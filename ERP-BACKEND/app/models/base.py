"""Base model class and common utilities."""
from sqlalchemy import Column, Integer, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


# Use JSON universally for compatibility across SQLite (tests) and PostgreSQL (production)
# SQLAlchemy handles JSON type appropriately for each database dialect
JSONB = JSON


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    is_deleted = Column(Boolean, nullable=False, server_default="false")
    deleted_at = Column(DateTime(timezone=True), nullable=True)
