"""
Database configuration and session management for the ERP system.

This module provides:
- SQLAlchemy engine configuration with connection pooling
- Session factory for database operations
- Base class for ORM models
- Database dependency for FastAPI routes
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings


SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL


def _create_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine with appropriate configuration.
    
    Args:
        database_url: Database connection URL.
        
    Returns:
        Configured SQLAlchemy engine instance.
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


engine = _create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for dependency injection.
    
    Yields:
        SQLAlchemy database session.
        
    Note:
        The session is automatically closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

