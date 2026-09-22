from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Table, Column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", PGUUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", PGUUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", PGUUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MMK")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Yangon")
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="my-MM")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    branches: Mapped[list["Branch"]] = relationship(back_populates="business", cascade="all, delete-orphan")


class Branch(Base):
    __tablename__ = "branches"
    __table_args__ = (Index("ix_branches_business_active", "business_id", "active"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    business: Mapped[Business] = relationship(back_populates="branches")

    __table_args__ = (
        Index("ix_branches_business_active", "business_id", "active"),
        Index("uq_branches_business_code", "business_id", "code", unique=True),
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(300))


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    permissions: Mapped[list[Permission]] = relationship(secondary=role_permissions)

    __table_args__ = (Index("uq_roles_business_name", "business_id", "name", unique=True),)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("uq_users_business_email", "business_id", "email", unique=True),
        Index("ix_users_business_active", "business_id", "active"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    roles: Mapped[list[Role]] = relationship(secondary=user_roles)
