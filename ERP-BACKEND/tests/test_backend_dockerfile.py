"""
Unit tests for `ERP-BACKEND/Dockerfile`.

This PR (see commit "fix: exec production backend process for correct
signal handling") makes three changes to this file:

1. Renames the stage-1 comment for clarity.
2. Consolidates the three separate `ENV` instructions in the production
   stage into a single instruction (fewer image layers).
3. Prefixes the `uvicorn` invocation in `CMD` with `exec` so that uvicorn
   replaces the shell process (PID 1's child) instead of running as a
   child of `sh`, allowing it to receive signals (e.g. SIGTERM) directly
   for graceful shutdown.

These tests validate the resulting file using lightweight text-based
assertions, consistent with this repo's existing conventions for testing
config files (see tests/test_env_file.py and tests/test_gitignore.py).
"""
import os
import re

import pytest


DOCKERFILE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
)


@pytest.fixture(scope="module")
def dockerfile_text():
    """Read and return the complete text content of the backend Dockerfile."""
    with open(DOCKERFILE_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def dockerfile_lines(dockerfile_text):
    """Split the Dockerfile text into individual lines for line-based assertions."""
    return dockerfile_text.splitlines()


class TestBackendDockerfileIntegrity:
    def test_dockerfile_exists(self):
        """Verify that the backend Dockerfile exists at the expected path."""
        assert os.path.isfile(DOCKERFILE_PATH)

    def test_dockerfile_is_not_empty(self, dockerfile_text):
        """Verify that the Dockerfile contains non-whitespace content."""
        assert len(dockerfile_text.strip()) > 0

    def test_still_has_two_named_stages(self, dockerfile_text):
        """Verify that both the builder and production stages are defined."""
        assert "FROM python:3.11-slim AS builder" in dockerfile_text
        assert "FROM python:3.11-slim AS production" in dockerfile_text


class TestBackendDockerfileStageComment:
    def test_stage_one_comment_updated(self, dockerfile_text):
        """Verify that the stage 1 comment was updated to the new wording."""
        assert "# Stage 1: deterministic dependency build" in dockerfile_text

    def test_old_stage_one_comment_removed(self, dockerfile_text):
        """Verify that the old stage 1 comment wording is no longer present."""
        assert "# Stage 1: Build Environment" not in dockerfile_text


class TestBackendDockerfileConsolidatedEnv:
    """The three previously-separate ENV instructions were merged into one
    multi-line instruction to reduce image layers, without changing which
    variables are set."""

    def test_exactly_one_env_instruction(self, dockerfile_lines):
        """Verify that all ENV variables were consolidated into a single instruction."""
        env_instruction_lines = [
            line for line in dockerfile_lines if line.startswith("ENV ")
        ]
        assert len(env_instruction_lines) == 1, (
            "Expected the PATH/PYTHONUNBUFFERED/PYTHONDONTWRITEBYTECODE "
            "settings to be consolidated into a single ENV instruction, "
            f"found {len(env_instruction_lines)} separate ENV lines"
        )

    def test_env_instruction_uses_line_continuation(self, dockerfile_text):
        """Verify that the consolidated ENV instruction uses backslash continuation."""
        match = re.search(r"^ENV .*\\\n", dockerfile_text, re.MULTILINE)
        assert match, "Expected the consolidated ENV instruction to use a backslash line continuation"

    @pytest.mark.parametrize(
        "expected_var",
        [
            "PATH=/home/appuser/.local/bin:$PATH",
            "PYTHONUNBUFFERED=1",
            "PYTHONDONTWRITEBYTECODE=1",
        ],
    )
    def test_env_variable_still_set(self, dockerfile_text, expected_var):
        """Verify that each required environment variable is still present."""
        assert expected_var in dockerfile_text

    def test_env_vars_appear_within_same_instruction_block(self, dockerfile_text):
        """All three variables must belong to the single consolidated ENV
        instruction (not scattered across the file)."""
        match = re.search(
            r"^ENV PATH=.*?PYTHONDONTWRITEBYTECODE=1\s*$",
            dockerfile_text,
            re.MULTILINE | re.DOTALL,
        )
        assert match, "PATH, PYTHONUNBUFFERED and PYTHONDONTWRITEBYTECODE are not part of one contiguous ENV instruction"


class TestBackendDockerfileCmd:
    """Regression tests for the `exec` fix that ensures uvicorn receives
    process signals directly for graceful shutdown."""

    @pytest.fixture(scope="class")
    def cmd_line(self, dockerfile_lines):
        """Extract and return the single CMD instruction line from the Dockerfile."""
        cmd_lines = [line for line in dockerfile_lines if line.startswith("CMD ")]
        assert len(cmd_lines) == 1, f"Expected exactly one CMD instruction, found {len(cmd_lines)}"
        return cmd_lines[0]

    def test_only_one_cmd_instruction(self, dockerfile_lines):
        """Verify that exactly one CMD instruction exists in the Dockerfile."""
        cmd_lines = [line for line in dockerfile_lines if line.startswith("CMD ")]
        assert len(cmd_lines) == 1

    def test_cmd_still_runs_migrations_first(self, cmd_line):
        """Verify that alembic migrations run before uvicorn starts."""
        assert "alembic upgrade head" in cmd_line
        assert cmd_line.index("alembic upgrade head") < cmd_line.index("uvicorn")

    def test_uvicorn_invoked_with_exec(self, cmd_line):
        """Verify that uvicorn is invoked with exec for proper signal handling."""
        assert "&& exec uvicorn" in cmd_line, (
            "uvicorn must be invoked with `exec` so it replaces the shell "
            "process and receives signals (e.g. SIGTERM) directly"
        )

    def test_bare_uvicorn_without_exec_not_present(self, cmd_line):
        """Negative/regression check: guards against the fix being
        accidentally reverted to `&& uvicorn ...` without `exec`."""
        assert "&& uvicorn" not in cmd_line

    def test_cmd_preserves_uvicorn_flags(self, cmd_line):
        """Verify that all required uvicorn command-line flags are present."""
        for expected_flag in (
            "--host 0.0.0.0",
            "--port 8000",
            "--workers 4",
            "--loop uvloop",
            "--http httptools",
            "--log-level info",
        ):
            assert expected_flag in cmd_line

    def test_cmd_uses_shell_form_array(self, cmd_line):
        """Verify that CMD uses the shell array form for execution."""
        assert cmd_line.startswith('CMD ["sh", "-c", "')


class TestBackendDockerfileUnrelatedInstructionsUnaffected:
    """Sanity checks that unrelated instructions untouched by this PR are
    still intact (guards against accidental collateral damage from the
    ENV consolidation refactor)."""

    def test_healthcheck_unchanged(self, dockerfile_text):
        """Verify that the HEALTHCHECK instruction remains unchanged."""
        assert (
            "HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3"
            in dockerfile_text
        )
        assert "CMD curl -f http://localhost:8000/api/v1/health || exit 1" in dockerfile_text

    def test_user_switches_to_appuser_after_env(self, dockerfile_text):
        """Verify that the USER instruction comes after ENV setup."""
        env_index = dockerfile_text.index("ENV PATH=")
        user_index = dockerfile_text.index("USER appuser")
        assert env_index < user_index

    def test_expose_8000_present(self, dockerfile_text):
        """Verify that port 8000 is exposed."""
        assert "EXPOSE 8000" in dockerfile_text
