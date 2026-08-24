"""
Settings model for application configuration
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class Setting(Base):
    """Application settings and configuration"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, server_default="general")
    is_encrypted = Column(Boolean, nullable=False, server_default="false")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Setting(id={self.id}, key='{self.key}', category='{self.category}')>"
