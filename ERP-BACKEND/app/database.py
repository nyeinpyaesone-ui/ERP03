from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Check if using SQLite (for testing)
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
is_async = "async" in SQLALCHEMY_DATABASE_URL.lower()

if is_async:
    # Async engine for PostgreSQL/SQLite with async support
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )
    AsyncSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
elif is_sqlite:
    # SQLite doesn't support pool_size and max_overflow
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # PostgreSQL/other databases with connection pooling
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    if is_async:
        raise NotImplementedError("Async DB session not implemented in sync getter")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

