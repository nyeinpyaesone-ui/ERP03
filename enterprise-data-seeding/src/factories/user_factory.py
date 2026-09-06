"""
User factory for generating test user data.

Uses Factory Boy pattern with Faker for realistic test data.
"""

from datetime import datetime
from typing import Optional
import factory
from factory.faker import Faker
from factory.alchemy import SQLAlchemyModelFactory


class UserFactory(SQLAlchemyModelFactory):
    """
    Factory for creating test users.
    
    Usage:
        # Create single user
        user = UserFactory()
        
        # Create user with custom email
        user = UserFactory(email="custom@example.com")
        
        # Create batch of users
        users = UserFactory.create_batch(10)
        
        # Create async
        user = await UserFactory.create_async()
    """
    
    class Meta:
        model = None  # Will be set dynamically based on ERP-BACKEND models
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"
    
    # Core fields
    email = Faker("email")
    full_name = Faker("name")
    is_active = True
    is_superuser = False
    
    # Password (hashed by default)
    hashed_password = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3VsPGub8kAm"  # "password"
    
    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = None
    
    @classmethod
    def set_model(cls, model_class):
        """Set the model class used by the factory dynamically.
        
        Parameters:
        	model_class: The model class to associate with the factory.
        """
        cls.Meta.model = model_class
    
    @classmethod
    async def create_async(
        cls,
        _using=None,
        **kwargs
    ):
        """
        Create and persist a user in an asynchronous database session.
        
        Parameters:
            **kwargs: Attributes used to build the user.
        
        Returns:
            The persisted user.
        
        Raises:
            Exception: Re-raises any error encountered while creating or committing the user.
        """
        from ..database import db_manager
        
        async with db_manager.async_session() as session:
            cls.Meta.sqlalchemy_session = session
            
            try:
                user = cls.create(**kwargs)
                await session.commit()
                return user
            except Exception:
                await session.rollback()
                raise
            finally:
                cls.Meta.sqlalchemy_session = None
    
    @classmethod
    def simple_user(cls):
        """
        Build a standard active user without administrator privileges.
        
        Returns:
            A user configured as active and non-superuser.
        """
        return cls(
            is_active=True,
            is_superuser=False,
        )
    
    @classmethod
    def admin_user(cls):
        """Create an admin user."""
        return cls(
            is_superuser=True,
            is_active=True,
        )
    
    @classmethod
    def inactive_user(cls):
        """Create an inactive user."""
        return cls(
            is_active=False,
        )


def create_test_users(
    count: int = 10,
    include_admin: bool = True,
    include_inactive: bool = True,
) -> list:
    """
    Create a configurable collection of test users.
    
    Args:
        count: Number of regular users to create.
        include_admin: Whether to include one admin user.
        include_inactive: Whether to include three inactive users.
    
    Returns:
        List containing the requested admin, regular, and inactive users.
    """
    users = []
    
    # Create admin if requested
    if include_admin:
        users.append(UserFactory.admin_user())
    
    # Create regular users
    users.extend(UserFactory.create_batch(count))
    
    # Create inactive users if requested
    if include_inactive:
        users.extend(UserFactory.create_batch(3, is_active=False))
    
    return users
