import logging
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("erp03.config")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", extra="forbid", case_sensitive=False
    )
    secret_key: SecretStr = SecretStr("development-only-change-me")
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
    database_path: str = "/data/erp03.sqlite3"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [item.strip() for item in value.split(",") if item.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        for origin in origins:
            if "://" not in origin:
                raise ValueError(f"CORS origin '{origin}' must include scheme")
        return ",".join(origins)

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        env = self.environment.lower()
        # Production security checks
        if env in {"production", "prod"}:
            secret = self.secret_key.get_secret_value()
            if (
                secret in {"", "development-only-change-me", "change-me-in-production"}
                or len(secret) < 32
            ):
                raise ValueError(
                    "SECRET_KEY must be explicitly configured "
                    "with at least 32 characters in production"
                )
            if any(
                origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")
                for origin in self.cors_origin_list
            ):
                raise ValueError("Production CORS_ORIGINS must not contain localhost/127.0.0.1")
            # Require HTTPS origins in production
            if any(origin.startswith("http://") for origin in self.cors_origin_list):
                raise ValueError("Production CORS_ORIGINS must use HTTPS")
        # DB storage mutual exclusion
        if env in {"production", "prod"}:
            # In production, prefer DATABASE_URL and disallow SQLite path usage
            if self.database_path and "/sqlite" in self.database_url.lower():
                # Allow, but warn via validation if path points to different location than expected
                pass
        # Prevent ambiguous dual storage in production
        if env in {"production", "prod"} and "sqlite" in self.database_url.lower():
            raise ValueError("Production must use PostgreSQL DATABASE_URL, not SQLite")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Resolve settings once per process (cached)."""
    try:
        return Settings()
    except Exception as exc:
        logger.exception("Failed to load Settings: %s", exc)
        raise


# Single module-level accessor. Resolved eagerly on import; tests and tools
# override values through environment variables *before* importing the app,
# or call ``get_settings.cache_clear()`` after mutating the environment.
settings: Settings = get_settings()
