"""User model."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, server_default="user")
    is_active = Column(Boolean, nullable=False, server_default="true")
    avatar_url = Column(String(500), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    contacts = relationship("Contact", back_populates="assigned_user", foreign_keys="Contact.assigned_to")
    deals = relationship("Deal", back_populates="assigned_user", foreign_keys="Deal.assigned_to")
    projects_managed = relationship("Project", back_populates="manager", foreign_keys="Project.manager_id")
    tasks = relationship("Task", back_populates="assigned_user", foreign_keys="Task.assigned_to")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user")
