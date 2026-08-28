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
        # Clear environment to ensure we test defaults, not .env file values
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'SECRET_KEY': 'test_secret_key_for_testing_purposes_only_123456'
        }, clear=True):
            with patch('app.config._read_secret', return_value=None):
                from app.config import Settings

                # Create a new settings instance with no env file loading
                settings = Settings(_env_file=None)

                assert settings.APP_NAME == "ERP SOLUTION System"
                assert settings.ALGORITHM == "HS256"
                # Note: ACCESS_TOKEN_EXPIRE_MINUTES is now 15 minutes for security (changed from 24 hours)
                assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
                assert settings.OLLAMA_URL == "http://localhost:11434"
                assert settings.OLLAMA_MODEL == "llama3.1"

    def test_ollama_url_can_be_overridden_via_env(self):
        """Test that OLLAMA_URL can be overridden via environment variable."""
        with patch('app.config._read_secret', return_value=None):
            with patch.dict(os.environ, {
                'DATABASE_URL': 'postgresql://test:test@localhost/test',
                'SECRET_KEY': 'test_secret_key_for_testing_purposes_only_123456',
                'OLLAMA_URL': 'http://ollama:11434',
            }, clear=False):
                from app.config import Settings

                settings = Settings()

                assert settings.OLLAMA_URL == "http://ollama:11434"

    def test_settings_ollama_url_default_value(self):
        """Test that OLLAMA_URL defaults to the local Ollama endpoint."""
        with patch('app.config._read_secret', return_value=None):
            with patch.dict(os.environ, {
                'DATABASE_URL': 'postgresql://test:test@localhost/test',
                'SECRET_KEY': 'test_secret_key_for_testing_purposes_only_123456'
            }, clear=False):
                from app.config import Settings

                settings = Settings(_env_file=None)

                assert settings.OLLAMA_URL == "http://localhost:11434"

    def test_settings_ollama_url_overridable_via_env(self):
        """Test that OLLAMA_URL can be overridden via environment variables."""
        with patch('app.config._read_secret', return_value=None):
            with patch.dict(os.environ, {
                'DATABASE_URL': 'postgresql://test:test@localhost/test',
                'SECRET_KEY': 'test_secret_key_for_testing_purposes_only_123456',
                'OLLAMA_URL': 'http://ollama:11434',
            }, clear=False):
                from app.config import Settings

                settings = Settings(_env_file=None)

                assert settings.OLLAMA_URL == "http://ollama:11434"

    @pytest.mark.parametrize("missing_credential", ["POSTGRES_USER", "POSTGRES_PASSWORD"])
    def test_settings_database_credentials_required_without_database_url(self, missing_credential):
        """Test that both Postgres credentials are required without DATABASE_URL."""
        from app.config import Settings
        environment = {
            "SECRET_KEY": "test_secret_key_for_testing_purposes_only_123456",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_password",
        }
        environment[missing_credential] = ""

        with patch.dict(os.environ, environment, clear=True):
            with patch('app.config._read_secret', return_value=None):
                with pytest.raises(ValueError) as exc_info:
                    Settings(_env_file=None)

                assert missing_credential in str(exc_info.value)

    def test_settings_postgres_credentials_allow_database_url_fallback(self):
        """Test that Postgres credentials are accepted when DATABASE_URL is absent."""
        from app.config import Settings

        with patch.dict(os.environ, {
            "SECRET_KEY": "test_secret_key_for_testing_purposes_only_123456",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_password",
        }, clear=True):
            with patch('app.config._read_secret', return_value=None):
                settings = Settings(_env_file=None)

                assert settings.get_database_url == "postgresql+asyncpg://test_user:test_password@db:5432/erp03_prod"

    def test_settings_secret_key_minimum_length(self):
        """Test that SECRET_KEY must be at least 32 characters."""
        from app.config import Settings
        
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'SECRET_KEY': 'short'  # Too short
        }, clear=False):
            with patch('app.config._read_secret', return_value=None):
                with pytest.raises(ValueError) as exc_info:
                    Settings()
                
                assert "SECRET_KEY" in str(exc_info.value) or "32" in str(exc_info.value)

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
