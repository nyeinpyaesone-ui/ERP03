"""
Base model class for all database models
Provides common fields and methods
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin for adding timestamp columns to models"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=True
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted = Column(Integer, nullable=False, server_default="0")
    deleted_at = Column(DateTime(timezone=True), nullable=True)
