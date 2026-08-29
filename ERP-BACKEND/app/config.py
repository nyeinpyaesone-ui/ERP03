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

    PROJECT_NAME: str = "ERP SOLUTION System"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "erp03_prod"

    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    INTEGRATION_SERVICE_ISSUER: str = "erp03"
    INTEGRATION_SERVICE_AUDIENCE: str = "erp-ai-integration"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@erp_solution.local"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_URL: str = "http://localhost:11434"

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    WS_HEARTBEAT_INTERVAL: int = 30
    TEST_MODE: bool = False
    API_V1_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if not self.POSTGRES_USER or not self.POSTGRES_PASSWORD:
            raise ValueError("POSTGRES_USER and POSTGRES_PASSWORD are required when DATABASE_URL is unset")
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@db:5432/{self.POSTGRES_DB}"

    def model_post_init(self, __context):
        # Docker/Kubernetes secrets are mounted as files and take precedence over env values.
        for name in ("POSTGRES_USER", "POSTGRES_PASSWORD", "DATABASE_URL", "SECRET_KEY"):
            value = _read_secret(name)
            if value:
                setattr(self, name, value)

        if self.TEST_MODE:
            if not self.DATABASE_URL:
                self.DATABASE_URL = "sqlite:///:memory:"
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must contain at least 32 characters even in test mode")
            return

        if not self.DATABASE_URL and (not self.POSTGRES_USER or not self.POSTGRES_PASSWORD):
            raise ValueError("DATABASE_URL or POSTGRES_USER/POSTGRES_PASSWORD is required")
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
