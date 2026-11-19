"""Connection-pool limits must remain safe across the configured HPA range."""

from app.core.config import Settings


def _settings(environment: str, **overrides: object) -> Settings:
    return Settings(
        _env_file=None,
        environment=environment,
        secret_key="test-secret-key-with-at-least-32-characters",
        database_url="postgresql+asyncpg://erp03:test@localhost:5432/erp03",
        cors_origins="https://erp.example.com",
        **overrides,
    )


def test_production_pool_is_bounded_for_ten_hpa_replicas() -> None:
    settings = _settings("production", db_pool_size=20, db_max_overflow=50)

    assert settings.db_pool_size == 4
    assert settings.db_max_overflow == 2
    assert settings.db_pool_size + settings.db_max_overflow == 6
    assert (settings.db_pool_size + settings.db_max_overflow) * 10 == 60


def test_staging_pool_uses_the_same_safe_connection_cap() -> None:
    settings = _settings("staging", db_pool_size=10, db_max_overflow=30)

    assert settings.db_pool_size == 4
    assert settings.db_max_overflow == 2


def test_development_pool_defaults_are_conservative() -> None:
    settings = _settings("development")

    assert settings.db_pool_size == 4
    assert settings.db_max_overflow == 2
