"""
Database Configuration and Session Management

This module provides database engine configuration, session management,
and the base class for SQLAlchemy ORM models.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL


def _create_database_engine(database_url: str) -> Engine:
    """
    Create a database engine with appropriate configuration.

    Args:
        database_url: Database connection URL.

    Returns:
        Configured SQLAlchemy engine.
    """
    is_sqlite = database_url.startswith("sqlite")

    if is_sqlite:
        # SQLite doesn't support pool_size and max_overflow
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    else:
        # PostgreSQL/other databases with connection pooling
        return create_engine(
            database_url,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
        )


engine = _create_database_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Yields:
        SQLAlchemy database session.

    Ensures:
        Session is properly closed after use.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

