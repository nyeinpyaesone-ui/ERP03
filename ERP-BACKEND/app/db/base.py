"""Canonical declarative base, naming conventions, and shared helpers."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def utcnow() -> datetime:
    """Single source of truth for timezone-aware creation/update timestamps."""
    return datetime.now(UTC)


def uuid_pk() -> Mapped[UUID]:
    """Return the standard UUID primary-key column definition.

    Models apply it explicitly (``id: Mapped[UUID] = uuid_pk()``) instead of
    inheriting from a mixin so that column order stays deterministic for
    Alembic autogenerate.
    """
    return mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
