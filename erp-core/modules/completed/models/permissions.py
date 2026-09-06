"""Permission and RBAC (Role-Based Access Control) models."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Role(Base):
    """Role model for RBAC system."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System roles cannot be deleted

    # Relationships
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    users = relationship("User", secondary="user_roles", back_populates="roles")
    field_permissions = relationship("FieldPermission", back_populates="role", cascade="all, delete-orphan")
    data_policies = relationship("DataPolicy", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    """Permission model defining access rights."""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)  # e.g., 'contacts', 'invoices'
    action = Column(String(50), nullable=False)  # e.g., 'read', 'write', 'delete'
    description = Column(Text, nullable=True)

    # Relationships
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class RolePermission(Base):
    """Association table for role-permission many-to-many relationship."""
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class UserRole(Base):
    """Association table for user-role many-to-many relationship."""
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class FieldPermission(Base):
    """Field-level permission model for granular access control."""
    __tablename__ = "field_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)  # e.g., 'contacts', 'invoices'
    field_name = Column(String(100), nullable=False)  # e.g., 'email', 'phone'
    access_level = Column(String(20), nullable=False, default="read")  # read, write, hidden

    # Relationships
    role = relationship("Role", back_populates="field_permissions")


class DataPolicy(Base):
    """Data policy model for row-level security and data access rules."""
    __tablename__ = "data_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    resource = Column(String(100), nullable=False, index=True)  # e.g., 'contacts', 'invoices'
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    condition = Column(JSON, nullable=True)  # e.g., {"owner_id": "${user.id}"}
    effect = Column(String(10), nullable=False, default="allow")  # allow, deny
    priority = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    role = relationship("Role", back_populates="data_policies")
