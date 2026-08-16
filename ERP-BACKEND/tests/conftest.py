"""
Test fixtures and configuration for pytest.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def test_settings():
    """Create test settings with mocked values."""
    settings = MagicMock()
    settings.SECRET_KEY = "test_secret_key_for_testing_purposes_only_123456"
    settings.ALGORITHM = "HS256"
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60
    settings.DATABASE_URL = "sqlite:///:memory:"
    return settings


@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )


@pytest.fixture
def db_session(engine):
    """Create a fresh database session for each test."""
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.query = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.delete = MagicMock()
    db.close = MagicMock()
    return db


@pytest.fixture
def sample_user():
    """Create a sample user object."""
    from app.models import User
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G.2f2f2f2f2f2f",
        full_name="Test User",
        role="user",
        is_active=True
    )
    return user


@pytest.fixture
def sample_admin():
    """Create a sample admin user object."""
    from app.models import User
    admin = User(
        id=2,
        email="admin@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G.2f2f2f2f2f2f",
        full_name="Admin User",
        role="admin",
        is_active=True
    )
    return admin


@pytest.fixture
def sample_superadmin():
    """Create a sample superadmin user object."""
    from app.models import User
    superadmin = User(
        id=3,
        email="superadmin@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G.2f2f2f2f2f2f",
        full_name="Super Admin",
        role="superadmin",
        is_active=True
    )
    return superadmin


@pytest.fixture
def sample_company():
    """Create a sample company object."""
    from app.models import Company
    return Company(
        id=1,
        name="Test Company",
        industry="Technology",
        size="50-200",
        website="https://testcompany.com",
        address="123 Test St",
        phone="+1234567890"
    )


@pytest.fixture
def sample_contact():
    """Create a sample contact object."""
    from app.models import Contact
    return Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+1234567890",
        title="Manager",
        status="lead"
    )


@pytest.fixture
def mock_oauth2_scheme():
    """Mock OAuth2 scheme for testing authentication."""
    with patch('app.auth.oauth2_scheme') as mock:
        mock.return_value = "test_token"
        yield mock


@pytest.fixture
def mock_jwt_encode():
    """Mock JWT encode function."""
    with patch('app.auth.jwt.encode') as mock:
        mock.return_value = "encoded_test_token"
        yield mock


@pytest.fixture
def mock_jwt_decode():
    """Mock JWT decode function."""
    with patch('app.auth.jwt.decode') as mock:
        mock.return_value = {"sub": "1", "exp": datetime.utcnow() + timedelta(minutes=60)}
        yield mock


@pytest.fixture
def mock_pwd_context():
    """Mock password context."""
    with patch('app.auth.pwd_context') as mock:
        mock.verify.return_value = True
        mock.hash.return_value = "hashed_password"
        yield mock
