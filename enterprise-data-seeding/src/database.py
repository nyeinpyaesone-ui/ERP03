"""
Database connection management for seeding operations.

Provides async and sync database session factories with proper
connection pooling, transaction management, and error handling.
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import text

from .config import config


class DatabaseManager:
    """
    Manages database connections for seeding operations.
    
    Features:
    - Connection pooling
    - Transaction management
    - Health checks
    - Graceful shutdown
    """
    
    def __init__(self, database_url: str | None = None):
        """Initialize a database manager with the specified or configured database URL."""
        self.database_url = database_url or config.database.url
        self._async_engine: AsyncEngine | None = None
        self._sync_engine = None
        
    @property
    def async_engine(self) -> AsyncEngine:
        """Get or create the cached asynchronous database engine.
        
        Returns:
        	AsyncEngine: The asynchronous database engine.
        """
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self.database_url,
                pool_size=config.database.pool_size,
                max_overflow=config.database.max_overflow,
                echo=config.database.echo,
                pool_pre_ping=True,
            )
        return self._async_engine
    
    @property
    def sync_engine(self):
        """Provide the configured synchronous database engine, creating it on first access.
        
        Returns:
            The synchronous SQLAlchemy engine.
        """
        if self._sync_engine is None:
            from sqlalchemy import create_engine
            # Convert async URL to sync URL if needed
            sync_url = self.database_url.replace("+asyncpg", "")
            self._sync_engine = create_engine(
                sync_url,
                pool_size=config.database.pool_size,
                max_overflow=config.database.max_overflow,
                echo=config.database.echo,
                pool_pre_ping=True,
            )
        return self._sync_engine
    
    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provide an asynchronous database session with transactional handling.
        
        Yields:
            AsyncSession: Session for asynchronous database operations.
        
        The transaction is committed when the context exits successfully, rolled
        back when an exception occurs, and the session is always closed.
        """
        async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        session = async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @contextmanager
    def sync_session(self) -> Generator[Session, None, None]:
        """
        Provide a synchronous database session.
        
        Yields:
            Session: Database session for sync operations
            
        Example:
            with db_manager.sync_session() as session:
                result = session.query(Model).all()
        """
        sync_session_factory = sessionmaker(
            self.sync_engine,
            class_=Session,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        session = sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def check_health(self) -> bool:
        """
        Check whether the database is accessible.
        
        Returns:
            bool: `True` if the connectivity check succeeds, `False` otherwise.
        """
        try:
            async with self.async_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
    
    async def close(self):
        """Close all database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
            self._async_engine = None
        
        if self._sync_engine:
            self._sync_engine.dispose()
            self._sync_engine = None


# Global database manager instance
db_manager = DatabaseManager()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session for dependency injection.
    
    Yields:
        AsyncSession: An active asynchronous database session.
    """
    async with db_manager.async_session() as session:
        yield session


def get_sync_session() -> Generator[Session, None, None]:
    """Provide a synchronous database session for dependency injection."""
    with db_manager.sync_session() as session:
        yield session
