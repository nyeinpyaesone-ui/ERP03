from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "ERP03 API"
    version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    database_url: str = Field(default="postgresql+asyncpg://erp03:erp03@postgres:5432/erp03")
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=200)
    db_pool_recycle: int = Field(default=1800, ge=60)
    db_echo: bool = False
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:1.5b"
    ollama_timeout_seconds: float = Field(default=120.0, gt=0, le=600)
    secret_key: SecretStr = SecretStr("development-only-change-me")
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore", case_sensitive=False)

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment.lower() in {"production", "prod"} and self.secret_key.get_secret_value() in {"", "development-only-change-me", "change-me-in-production"}:
            raise ValueError("SECRET_KEY must be explicitly configured in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def effective_celery_broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def effective_celery_result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()