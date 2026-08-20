"""Base model class and common utilities."""
from sqlalchemy import Column, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


# Use JSON for SQLite compatibility in tests, JSONB for PostgreSQL in production
try:
    # Test if we're using PostgreSQL
    from sqlalchemy import create_engine
    test_engine = create_engine("sqlite:///:memory:")
    USE_JSONB = False
except:
    USE_JSONB = True

# Alias JSONB to JSON for SQLite compatibility
if not USE_JSONB:
    JSONB = JSON


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    is_deleted = Column(Boolean, nullable=False, server_default="false")
    deleted_at = Column(DateTime(timezone=True), nullable=True)
