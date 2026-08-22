import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_secret(name: str) -> str | None:
    path = os.getenv(f"{name}_FILE")
    if not path:
        return None
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError(f"{name}_FILE is empty")
    return value


class Settings(BaseSettings):
    APP_NAME: str = "ERP SOLUTION System"
    APP_VERSION: str = "1.8.0"
    DEBUG: bool = False

    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Reduced from 24 hours to 15 minutes for security

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@erp_solution.local"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    WS_HEARTBEAT_INTERVAL: int = 30

    # Test mode flag (set by conftest.py during testing)
    TEST_MODE: bool = False
    
    # Integration service settings (with test defaults)
    INTEGRATION_SERVICE_ISSUER: str = "test-issuer"
    INTEGRATION_SERVICE_AUDIENCE: str = "test-audience"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    def model_post_init(self, __context):
        # Skip validation in test mode
        """
        Initialize settings with test-mode defaults or validated configuration.
        
        In test mode, an empty database URL is replaced with an in-memory SQLite
        URL. Otherwise, database and secret-key values may be loaded from file-based
        secrets before validation.
        
        Raises:
            ValueError: If the secret key is missing or shorter than 32 characters,
                or if the database URL is missing outside test mode.
        """
        if self.TEST_MODE:
            if not self.DATABASE_URL:
                self.DATABASE_URL = "sqlite:///:memory:"
            # SECURITY FIX: Require valid SECRET_KEY even in test mode
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must contain at least 32 characters even in test mode")
            return
        
        database_url = _read_secret("DATABASE_URL")
        secret_key = _read_secret("SECRET_KEY")
        if database_url:
            self.DATABASE_URL = database_url
        if secret_key:
            self.SECRET_KEY = secret_key
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL or DATABASE_URL_FILE is required")
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
