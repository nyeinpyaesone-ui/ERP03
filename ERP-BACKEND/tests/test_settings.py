"""Unit tests for the typed Settings model (app.core.config).

These cover validation rules and environment auto-tuning without touching
the database or network, complementing the API/integration suites.
"""

from __future__ import annotations

import pytest
from app.core.config import Settings
from pydantic import ValidationError


def _base(**overrides) -> Settings:
    """Build Settings isolated from .env files and process environment."""
    params = dict(_env_file=None, _secrets_dir=None)
    params.update(overrides)
    return Settings(**params)


class TestLogLevel:
    def test_normalizes_to_uppercase(self) -> None:
        assert _base(log_level="debug").log_level == "DEBUG"

    @pytest.mark.parametrize("value", ["verbose", "", "trace"])
    def test_rejects_invalid_levels(self, value: str) -> None:
        with pytest.raises(ValidationError):
            _base(log_level=value)


class TestCorsOrigins:
    def test_trims_whitespace_and_keeps_valid_origins(self) -> None:
        s = _base(cors_origins=" http://localhost:3000 , http://localhost:5173 ")
        assert s.cors_origin_list == ["http://localhost:3000", "http://localhost:5173"]

    def test_rejects_empty_origins(self) -> None:
        with pytest.raises(ValidationError):
            _base(cors_origins=" , ")

    def test_rejects_origin_without_scheme(self) -> None:
        with pytest.raises(ValidationError):
            _base(cors_origins="localhost:3000")


class TestProductionSecurity:
    PROD_SECRET = "x" * 48

    def test_production_requires_strong_secret(self) -> None:
        with pytest.raises(ValidationError):
            _base(environment="production")  # default dev secret must fail

    def test_production_rejects_short_secret(self) -> None:
        with pytest.raises(ValidationError):
            _base(environment="production", secret_key="short-secret")

    def test_production_rejects_sqlite_database(self) -> None:
        with pytest.raises(ValidationError):
            _base(
                environment="production",
                secret_key=self.PROD_SECRET,
                cors_origins="https://erp.example.com",
                database_url="sqlite+aiosqlite:///./prod.sqlite3",
            )

    def test_production_rejects_localhost_or_http_cors(self) -> None:
        common = dict(
            environment="production",
            secret_key=self.PROD_SECRET,
            database_url="postgresql+asyncpg://u:p@db:5432/erp",
        )
        with pytest.raises(ValidationError):
            _base(cors_origins="http://localhost:3000", **common)
        with pytest.raises(ValidationError):
            _base(cors_origins="http://erp.example.com", **common)

    def test_production_accepts_hardened_configuration(self) -> None:
        s = _base(
            environment="production",
            secret_key=self.PROD_SECRET,
            cors_origins="https://erp.example.com",
            database_url="postgresql+asyncpg://u:p@db:5432/erp",
        )
        assert s.environment == "production"


class TestPoolAutoTuning:
    def test_development_caps_pool_sizes(self) -> None:
        s = _base(environment="development", db_pool_size=100, db_max_overflow=100)
        assert s.db_pool_size == 5
        assert s.db_max_overflow == 10

    def test_production_floors_pool_sizes(self) -> None:
        s = _base(
            environment="production",
            secret_key="y" * 48,
            cors_origins="https://erp.example.com",
            database_url="postgresql+asyncpg://u:p@db:5432/erp",
            db_pool_size=1,
            db_max_overflow=0,
        )
        assert s.db_pool_size == 20
        assert s.db_max_overflow == 50

    def test_staging_floors_pool_sizes(self) -> None:
        s = _base(environment="staging", db_pool_size=2, db_max_overflow=1)
        assert s.db_pool_size == 10
        assert s.db_max_overflow == 30


class TestOptionalFeatures:
    def test_empty_typesafe_api_key_becomes_none(self) -> None:
        assert _base(typesafe_api_key="").typesafe_api_key is None

    def test_redis_defaults(self) -> None:
        s = _base()
        assert s.redis_url is None
        assert s.redis_db == 0
        assert s.redis_url_parsed is None
