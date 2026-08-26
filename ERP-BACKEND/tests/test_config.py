"""
Unit tests for the configuration module (app/config.py).
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import tempfile


class TestSettings:
    """Tests for Settings class."""

    def test_settings_default_values(self):
        """Test settings with default values."""
        with patch('app.config._read_secret', return_value=None):
            with patch.dict(os.environ, {
                'DATABASE_URL': 'postgresql://test:test@localhost/test',
                'SECRET_KEY': 'test_secret_key_for_testing_purposes_only_123456'
            }, clear=False):
                from app.config import Settings
                
                # Create a new settings instance to apply environment values and validation
                settings = Settings()
                
                assert settings.APP_NAME == "ERP SOLUTION System"
                assert settings.ALGORITHM == "HS256"
                assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24

    def test_settings_database_url_required(self):
        """Test that DATABASE_URL is required."""
        from app.config import Settings
        
        # Clear environment and cache to ensure fresh settings instance
        # Also need to prevent .env file from being loaded
        with patch.dict(os.environ, {}, clear=True):
            with patch('app.config._read_secret', return_value=None):
                # Need to clear the lru_cache to get a fresh Settings instance
                from app.config import get_settings
                get_settings.cache_clear()
                
                # Create settings without loading .env file
                with pytest.raises(ValueError) as exc_info:
                    Settings(_env_file=None)
                
                assert "DATABASE_URL" in str(exc_info.value)

    def test_settings_secret_key_minimum_length(self):
        """Test that SECRET_KEY must be at least 32 characters in production mode."""
        from pydantic import ValidationError
        
        # Need to test with a fresh module import since settings is created at module load
        import sys
        
        # Remove cached modules to get fresh import
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith('app.config')]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        # Set environment without TEST_MODE (which is set by conftest fixture)
        old_test_mode = os.environ.pop('TEST_MODE', None)
        old_db_url = os.environ.get('DATABASE_URL')
        old_secret_key = os.environ.get('SECRET_KEY')
        
        os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
        os.environ['SECRET_KEY'] = 'short'  # Too short
        
        try:
            # The exception will be raised during module import when Settings() is instantiated
            with pytest.raises((ValueError, ValidationError)) as exc_info:
                with patch('app.config._read_secret', return_value=None):
                    from app.config import Settings
                    Settings(_env_file=None)
            
            error_msg = str(exc_info.value)
            assert "SECRET_KEY" in error_msg or "32" in error_msg
        finally:
            # Restore environment
            if old_test_mode is not None:
                os.environ['TEST_MODE'] = old_test_mode
            if old_db_url is not None:
                os.environ['DATABASE_URL'] = old_db_url
            else:
                os.environ.pop('DATABASE_URL', None)
            if old_secret_key is not None:
                os.environ['SECRET_KEY'] = old_secret_key
            else:
                os.environ.pop('SECRET_KEY', None)

    def test_settings_from_env_file(self):
        """Test loading settings from .env file."""
        from app.config import Settings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("DATABASE_URL=postgresql://test:test@localhost/test\n")
            f.write("SECRET_KEY=test_secret_key_for_testing_purposes_only_123456\n")
            f.write("DEBUG=true\n")
            env_file = f.name
        
        try:
            settings = Settings(_env_file=env_file)
            assert settings.DATABASE_URL == "postgresql://test:test@localhost/test"
            assert settings.DEBUG is True
        finally:
            os.unlink(env_file)


class TestReadSecret:
    """Tests for _read_secret function."""

    def test_read_secret_from_file(self):
        """Test reading secret from file."""
        from app.config import _read_secret
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("secret_value")
            secret_file = f.name
        
        try:
            with patch.dict(os.environ, {'TEST_SECRET_FILE': secret_file}):
                result = _read_secret('TEST_SECRET')
                assert result == "secret_value"
                
            # Direct test
            os.environ['DIRECT_TEST_FILE'] = secret_file
            result = _read_secret('DIRECT_TEST')
            assert result == "secret_value"
        finally:
            os.unlink(secret_file)
            if 'DIRECT_TEST_FILE' in os.environ:
                del os.environ['DIRECT_TEST_FILE']
            if 'TEST_SECRET_FILE' in os.environ:
                del os.environ['TEST_SECRET_FILE']

    def test_read_secret_empty_file(self):
        """Test reading secret from empty file raises error."""
        from app.config import _read_secret
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("")  # Empty file
            secret_file = f.name
        
        try:
            os.environ['EMPTY_TEST_FILE'] = secret_file
            
            with pytest.raises(ValueError) as exc_info:
                _read_secret('EMPTY_TEST')
            
            assert "empty" in str(exc_info.value).lower()
        finally:
            os.unlink(secret_file)
            if 'EMPTY_TEST_FILE' in os.environ:
                del os.environ['EMPTY_TEST_FILE']

    def test_read_secret_no_file_path(self):
        """Test reading secret when no FILE env var is set."""
        from app.config import _read_secret
        
        # Ensure no such env var exists
        if 'NONEXISTENT_FILE' in os.environ:
            del os.environ['NONEXISTENT_FILE']
        
        result = _read_secret('NONEXISTENT')
        assert result is None


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_cached(self):
        """Test that get_settings uses LRU cache."""
        from app.config import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should return same cached instance
        assert settings1 is settings2
