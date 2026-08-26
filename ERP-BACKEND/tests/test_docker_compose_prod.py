"""
Unit tests for `docker-compose.prod.yml`.

This PR makes the following changes to this file:

1. Fixes the postgres healthcheck to use `$${POSTGRES_USER}`/`$${POSTGRES_DB}`
   instead of `$${DB_USER}`/`$${DB_NAME}` -- the latter are never set as
   environment variables inside the postgres container itself (only
   `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` are), so the previous
   healthcheck would have always failed to resolve those variables.
2. Adds a `start_period` grace period to the postgres and redis
   healthchecks.
3. Switches the `erp-backend` service's `DATABASE_URL` scheme from
   `postgresql://` to `postgresql+asyncpg://` to match the asyncpg driver
   used by the application.
4. Adds healthchecks to the `erp-backend` and `frontend` services.
5. Changes `frontend`'s and `nginx`'s `depends_on` conditions from
   `service_started` to `service_healthy` so dependents wait for their
   upstreams to actually be ready, not just started.

These tests validate the resulting file using lightweight text-based
assertions, consistent with this repo's existing conventions for testing
config files (see tests/test_env_file.py and tests/test_gitignore.py),
without introducing a new PyYAML dependency.
"""
import os

import pytest


COMPOSE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.prod.yml")
)

SERVICE_ORDER = ["postgres", "redis", "erp-backend", "frontend", "ollama", "nginx"]


@pytest.fixture(scope="module")
def compose_text():
    """Read and return the complete text content of docker-compose.prod.yml."""
    with open(COMPOSE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _service_section(text, service_name):
    """
    Extracts a top-level service block from compose file text.
    
    Parameters:
        text (str): Complete compose file content.
        service_name (str): Name of the service whose block to extract.
    
    Returns:
        str: The service block from its header through the line before the next top-level service, volumes, or networks section.
    """
    header = f"\n  {service_name}:\n"
    start = text.index(header)
    other_markers = [f"\n  {s}:\n" for s in SERVICE_ORDER if s != service_name]
    other_markers += ["\nvolumes:\n", "\nnetworks:\n"]
    search_from = start + len(header)
    ends = [text.index(m, search_from) for m in other_markers if m in text[search_from:]]
    end = min(ends) if ends else len(text)
    return text[start:end]


class TestComposeFileIntegrity:
    def test_compose_file_exists(self):
        """Verify that docker-compose.prod.yml exists at the expected path."""
        assert os.path.isfile(COMPOSE_PATH)

    def test_compose_file_is_not_empty(self, compose_text):
        """Verify that the compose file contains non-whitespace content."""
        assert len(compose_text.strip()) > 0

    def test_starts_with_services_key(self, compose_text):
        """Verify that the compose file starts with the services key."""
        assert compose_text.startswith("services:\n")

    @pytest.mark.parametrize("service_name", SERVICE_ORDER)
    def test_all_expected_services_present(self, compose_text, service_name):
        """Verify that all expected services are defined in the compose file."""
        assert f"\n  {service_name}:\n" in compose_text


class TestPostgresHealthcheckFix:
    @pytest.fixture(scope="class")
    def postgres_section(self, compose_text):
        """Extract and return the postgres service section from the compose file."""
        return _service_section(compose_text, "postgres")

    def test_uses_postgres_user_and_db_env_vars(self, postgres_section):
        """Verify that the healthcheck uses POSTGRES_USER and POSTGRES_DB variables."""
        assert (
            'test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]'
            in postgres_section
        )

    def test_no_longer_references_undefined_db_user_var(self, postgres_section):
        """Regression guard: `$${DB_USER}`/`$${DB_NAME}` are not set inside
        the postgres container's own environment, so the healthcheck must
        not reference them."""
        assert "$${DB_USER}" not in postgres_section
        assert "$${DB_NAME}" not in postgres_section

    def test_has_start_period_grace(self, postgres_section):
        """Verify that the postgres healthcheck includes a start_period grace period."""
        assert "start_period: 10s" in postgres_section

    def test_environment_still_sets_postgres_vars_from_db_vars(self, postgres_section):
        """The container's POSTGRES_USER/POSTGRES_DB env vars are populated
        from the compose-level DB_USER/DB_NAME variables; this mapping is
        what makes the healthcheck fix correct."""
        assert "POSTGRES_USER: ${DB_USER:?DB_USER must be set}" in postgres_section
        assert "POSTGRES_DB: ${DB_NAME:?DB_NAME must be set}" in postgres_section


class TestRedisHealthcheckStartPeriod:
    @pytest.fixture(scope="class")
    def redis_section(self, compose_text):
        """Extract and return the redis service section from the compose file."""
        return _service_section(compose_text, "redis")

    def test_has_start_period_grace(self, redis_section):
        """Verify that the redis healthcheck includes a start_period grace period."""
        assert "start_period: 10s" in redis_section

    def test_existing_ping_check_still_present(self, redis_section):
        """Sanity check that the addition of start_period did not disturb
        the pre-existing healthcheck test command."""
        assert 'redis-cli -a \\"$${REDIS_PASSWORD}\\" ping | grep -q PONG' in redis_section


class TestErpBackendDatabaseUrlScheme:
    @pytest.fixture(scope="class")
    def backend_section(self, compose_text):
        """Extract and return the erp-backend service section from the compose file."""
        return _service_section(compose_text, "erp-backend")

    def test_database_url_uses_asyncpg_scheme(self, backend_section):
        """Verify that DATABASE_URL uses the postgresql+asyncpg scheme."""
        assert (
            "DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}"
            in backend_section
        )

    def test_no_bare_postgresql_scheme_remains(self, backend_section):
        """Regression guard: ensures the scheme wasn't left as the
        non-async `postgresql://`, which is incompatible with the
        asyncpg-based SQLAlchemy engine used by the app."""
        assert "DATABASE_URL: postgresql://" not in backend_section


class TestErpBackendHealthcheck:
    @pytest.fixture(scope="class")
    def backend_section(self, compose_text):
        """Extract and return the erp-backend service section from the compose file."""
        return _service_section(compose_text, "erp-backend")

    def test_healthcheck_present(self, backend_section):
        """Verify that a healthcheck is defined for the erp-backend service."""
        assert "healthcheck:" in backend_section

    def test_healthcheck_hits_health_endpoint(self, backend_section):
        """Verify that the healthcheck targets the health endpoint."""
        assert "http://127.0.0.1:8000/api/v1/health" in backend_section

    def test_healthcheck_uses_python_urllib(self, backend_section):
        """Verify that the healthcheck uses Python with urllib for the HTTP check."""
        assert '"CMD", "python", "-c"' in backend_section

    def test_healthcheck_timing_values(self, backend_section):
        """Verify that the healthcheck has the correct timing parameters."""
        assert "interval: 30s" in backend_section
        assert "timeout: 10s" in backend_section
        assert "retries: 5" in backend_section
        assert "start_period: 45s" in backend_section


class TestFrontendHealthcheckAndDependsOn:
    @pytest.fixture(scope="class")
    def frontend_section(self, compose_text):
        """Extract and return the frontend service section from the compose file."""
        return _service_section(compose_text, "frontend")

    def test_depends_on_backend_waits_for_healthy(self, frontend_section):
        """Verify that frontend depends on erp-backend being healthy."""
        assert "erp-backend:\n        condition: service_healthy" in frontend_section

    def test_healthcheck_present(self, frontend_section):
        """Verify that a healthcheck is defined for the frontend service."""
        assert "healthcheck:" in frontend_section

    def test_healthcheck_uses_wget_spider(self, frontend_section):
        """Verify that the healthcheck uses wget in spider mode."""
        assert (
            '["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://127.0.0.1/"]'
            in frontend_section
        )

    def test_healthcheck_timing_values(self, frontend_section):
        """Verify that the healthcheck has the correct timing parameters."""
        assert "interval: 30s" in frontend_section
        assert "timeout: 10s" in frontend_section
        assert "retries: 5" in frontend_section
        assert "start_period: 15s" in frontend_section


class TestNginxDependsOnHealthy:
    @pytest.fixture(scope="class")
    def nginx_section(self, compose_text):
        """Extract and return the nginx service section from the compose file."""
        return _service_section(compose_text, "nginx")

    def test_depends_on_backend_waits_for_healthy(self, nginx_section):
        """Verify that nginx depends on erp-backend being healthy."""
        assert "erp-backend:\n        condition: service_healthy" in nginx_section

    def test_depends_on_frontend_waits_for_healthy(self, nginx_section):
        """Verify that nginx depends on frontend being healthy."""
        assert "frontend:\n        condition: service_healthy" in nginx_section


class TestServiceStartedConditionFullyMigrated:
    """Regression guard: this PR replaces every `service_started` condition
    with `service_healthy`. No occurrence of the old condition should
    remain anywhere in the file."""

    def test_no_service_started_condition_remains(self, compose_text):
        """Verify that no service_started conditions remain in the compose file."""
        assert "condition: service_started" not in compose_text

    def test_service_healthy_condition_used_at_least_three_times(self, compose_text):
        """
        Verify that the production Compose configuration uses healthy-service dependency conditions at least three times.
        
        Parameters:
        	compose_text (str): Complete contents of the Docker Compose file.
        """
        assert compose_text.count("condition: service_healthy") >= 3


class TestHealthyDependenciesHaveHealthchecks:
    """Cross-service integration check: any service that other services
    depend on with `condition: service_healthy` must itself define a
    `healthcheck`, otherwise docker compose will never consider it
    healthy and dependents will hang indefinitely."""

    @pytest.mark.parametrize("service_name", ["erp-backend", "frontend", "postgres", "redis"])
    def test_service_referenced_as_healthy_dependency_has_healthcheck(self, compose_text, service_name):
        """Verify that services referenced as healthy dependencies define healthchecks."""
        section = _service_section(compose_text, service_name)
        assert "healthcheck:" in section, (
            f"Service '{service_name}' is depended on with "
            "condition: service_healthy elsewhere in the file but does not "
            "define its own healthcheck"
        )
