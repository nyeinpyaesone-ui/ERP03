"""Canonical declarative base, naming conventions, and shared helpers."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's native ``UUID`` when the dialect supports it and falls
    back to a 32-hex-character ``CHAR(32)`` elsewhere (e.g. SQLite), so one
    model codebase runs unchanged on both production (PostgreSQL) and
    development/embedded (SQLite) backends.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return str(value) if not isinstance(value, UUID) else value
        if isinstance(value, UUID):
            return value.hex
        return UUID(str(value)).hex

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        text_value = str(value)
        # Legacy databases (created before GUID adoption) store canonical
        # hyphenated strings; freshly created CHAR(32) columns store bare hex.
        # Accept both transparently on every dialect.
        return UUID(text_value.replace("-", ""))


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
    return mapped_column(GUID(), primary_key=True, default=uuid4)
