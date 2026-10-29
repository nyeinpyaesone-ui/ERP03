"""Typed application settings with environment-based auto-tuning."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("erp03.config")


class Settings(BaseSettings):
    """Canonical settings with environment-driven auto-tuning.

    Database pool sizing scales with environment tier (development/staging/production)
    so operators only need to set ENVIRONMENT; pool parameters follow automatically.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", extra="forbid", case_sensitive=False
    )

    # --- Core ---
    secret_key: SecretStr = SecretStr("development-only-change-me")
    app_name: str = "ERP03 API"
    version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    database_url: str = Field(default="sqlite+aiosqlite:////app/.local/erp03.sqlite3")
    database_path: str = "./.local/erp03.sqlite3"

    # --- Database pool (auto-tuned by environment) ---
    db_pool_size: int = Field(default=10, ge=1, le=500)
    db_max_overflow: int = Field(default=20, ge=0, le=1000)
    db_pool_recycle: int = Field(default=1800, ge=60)
    db_echo: bool = False

    # --- TypeSafe System One ---
    typesafe_enabled: bool = Field(default=False)
    typesafe_api_key: SecretStr | None = Field(default=None)

    # --- JWT ---
    jwt_expiry_minutes: int = Field(default=480, ge=1, le=44640)

    # --- Redis (optional, for caching/sessions) ---
    redis_url: str | None = Field(default=None)
    redis_password: str | None = Field(default=None)
    redis_db: int = Field(default=0)

    # --- API metadata ---
    api_v1_prefix: str = Field(default="/api/v1")
    api_title: str = Field(default="ERP03 API")
    api_version: str = Field(default="1.0.0")
    api_docs_url: str = Field(default="/docs")
    api_redoc_url: str = Field(default="/redoc")

    # --- Auth ---
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=365)
    password_min_length: int = Field(default=12, ge=4, le=128)
    bcrypt_rounds: int = Field(default=12, ge=4, le=31)

    # --- Idempotency ---
    idempotency_ttl_hours: int = Field(default=24, ge=1, le=168)
    idempotency_cleanup_interval: int = Field(default=3600, ge=60)

    # --- Rate limiting ---
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)
    trusted_proxies: str = Field(default="")

    # --- Webhooks ---
    webhook_secret: SecretStr | None = Field(default=None)
    webhook_timeout: int = Field(default=30, ge=1, le=300)

    # --- Observability ---
    otel_enabled: bool = Field(default=False)
    otel_exporter_otlp_endpoint: str | None = Field(default=None)

    # --- Debug ---
    debug: bool = Field(default=False)

    @field_validator("typesafe_api_key", mode="before")
    @classmethod
    def _parse_typesafe_api_key(cls, value: Any) -> Any:
        if value is None or value == "":
            return None
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        upper = value.upper()
        if upper not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL")
        return upper

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [o.strip() for o in value.split(",") if o.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        for origin in origins:
            if "://" not in origin:
                raise ValueError(f"CORS origin '{origin}' must include scheme")
        return ",".join(origins)

    @model_validator(mode="after")
    def validate_production_security(self) -> Settings:
        env = self.environment.lower()
        if env in {"production", "prod"}:
            secret = self.secret_key.get_secret_value()
            if (
                secret in ("", "development-only-change-me", "change-me-in-production")
                or len(secret) < 32
            ):
                raise ValueError(
                    "SECRET_KEY must be explicitly configured with at least "
                    "32 characters in production"
                )
            if any(
                o.startswith(("http://localhost", "http://127.0.0.1"))
                for o in self.cors_origin_list
            ):
                raise ValueError("Production CORS_ORIGINS must not contain localhost/127.0.0.1")
            if any(o.startswith("http://") for o in self.cors_origin_list):
                raise ValueError("Production CORS_ORIGINS must use HTTPS")
            if "sqlite" in self.database_url.lower():
                raise ValueError("Production must use PostgreSQL DATABASE_URL, not SQLite")
        return self

    @model_validator(mode="after")
    def auto_tune_pool(self) -> Settings:
        """Auto-tune pool sizing based on environment tier."""
        env = self.environment.lower()
        if env in {"production", "prod"}:
            self.db_pool_size = max(self.db_pool_size, 20)
            self.db_max_overflow = max(self.db_max_overflow, 50)
            self.db_pool_recycle = max(self.db_pool_recycle, 3600)
        elif env in {"staging", "stage"}:
            self.db_pool_size = max(self.db_pool_size, 10)
            self.db_max_overflow = max(self.db_max_overflow, 30)
            self.db_pool_recycle = max(self.db_pool_recycle, 1800)
        else:
            self.db_pool_size = min(self.db_pool_size, 5)
            self.db_max_overflow = min(self.db_max_overflow, 10)
            self.db_pool_recycle = min(self.db_pool_recycle, 900)
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def redis_url_parsed(self) -> str | None:
        return self.redis_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Resolve settings once per process (cached)."""
    try:
        return Settings()
    except Exception as exc:
        logger.exception("Failed to load Settings: %s", exc)
        raise


settings: Settings = get_settings()
