"""Typed application settings with environment-based auto-tuning."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("erp03.config")


class Settings(BaseSettings):
    """Canonical settings with environment-driven auto-tuning."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", extra="forbid", case_sensitive=False
    )

    secret_key: SecretStr = SecretStr("development-only-change-me")
    app_name: str = "ERP03 API"
    version: str = "1.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    database_url: str = Field(default="sqlite+aiosqlite:////app/.local/erp03.sqlite3")
    database_path: str = "./.local/erp03.sqlite3"

    db_pool_size: int = Field(default=10, ge=1, le=500)
    db_max_overflow: int = Field(default=20, ge=0, le=1000)
    db_pool_recycle: int = Field(default=1800, ge=60)
    db_pool_timeout: int = Field(default=30, ge=1, le=300)
    db_echo: bool = False

    typesafe_enabled: bool = Field(default=False)
    typesafe_api_key: SecretStr | None = Field(default=None)

    jwt_expiry_minutes: int = Field(default=480, ge=1, le=44640)
    redis_url: str | None = Field(default=None)
    redis_password: str | None = Field(default=None)
    redis_db: int = Field(default=0)
    redis_max_connections: int = Field(default=50, ge=1, le=1000)

    api_v1_prefix: str = Field(default="/api/v1")
    api_title: str = Field(default="ERP03 API")
    api_version: str = Field(default="1.1.0")
    api_docs_url: str = Field(default="/docs")
    api_redoc_url: str = Field(default="/redoc")

    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=365)
    password_min_length: int = Field(default=12, ge=4, le=128)
    bcrypt_rounds: int = Field(default=12, ge=4, le=31)

    idempotency_ttl_hours: int = Field(default=24, ge=1, le=168)
    idempotency_cleanup_interval: int = Field(default=3600, ge=60)
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)
    trusted_proxies: str = Field(default="")

    webhook_secret: SecretStr | None = Field(default=None)
    webhook_timeout: int = Field(default=30, ge=1, le=300)
    otel_enabled: bool = Field(default=False)
    otel_exporter_otlp_endpoint: str | None = Field(default=None)
    debug: bool = Field(default=False)

    # Optional Supabase Auth bridge. The publishable key is public; never add
    # service-role, secret API, or JWT signing keys to frontend configuration.
    supabase_url: str | None = Field(default=None)
    supabase_publishable_key: SecretStr | None = Field(default=None)

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
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        for origin in origins:
            if "://" not in origin:
                raise ValueError(f"CORS origin '{origin}' must include scheme")
        return ",".join(origins)

    @model_validator(mode="after")
    def validate_production_security(self) -> Settings:
        env = self.environment.lower()
        if bool(self.supabase_url) != bool(self.supabase_publishable_key):
            raise ValueError(
                "SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY must be configured together"
            )
        if self.supabase_url and not self.supabase_url.startswith("https://"):
            raise ValueError("SUPABASE_URL must use HTTPS")
        if env in {"production", "prod"}:
            secret = self.secret_key.get_secret_value()
            if (
                secret in ("", "development-only-change-me", "change-me-in-production")
                or len(secret) < 32
            ):
                raise ValueError(
                    "SECRET_KEY must be explicitly configured with at least 32 "
                    "characters in production"
                )
            if any(
                origin.startswith(("http://localhost", "http://127.0.0.1"))
                for origin in self.cors_origin_list
            ):
                raise ValueError("Production CORS_ORIGINS must not contain localhost/127.0.0.1")
            if any(origin.startswith("http://") for origin in self.cors_origin_list):
                raise ValueError("Production CORS_ORIGINS must use HTTPS")
            if "sqlite" in self.database_url.lower():
                raise ValueError("Production must use PostgreSQL DATABASE_URL, not SQLite")
        return self

    @model_validator(mode="after")
    def auto_tune_pool(self) -> Settings:
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
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def redis_url_parsed(self) -> str | None:
        return self.redis_url

    @property
    def supabase_auth_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_publishable_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as exc:
        logger.exception("Failed to load Settings: %s", exc)
        raise


settings: Settings = get_settings()
