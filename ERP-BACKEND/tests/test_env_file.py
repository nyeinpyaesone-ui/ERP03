"""
Unit tests for the `ERP-BACKEND/.env` file.

This PR appended two new keys (`OLLAMA_URL`, `OLLAMA_MODEL`) to the existing
`.env` file to support the new AI assistant feature (see app/ai/assistant.py
and app/config.py). These tests validate the structure of the resulting file
and that the new keys are present with the expected values, without asserting
anything about pre-existing keys that were not touched by this PR.
"""
import os

import pytest


ENV_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", ".env")
)


@pytest.fixture(scope="module")
def env_lines():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        return f.read().splitlines()


@pytest.fixture(scope="module")
def env_dict(env_lines):
    """Parse simple KEY=VALUE lines into a dict, ignoring blanks/comments."""
    parsed = {}
    for line in env_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        assert "=" in stripped, f"Malformed .env line (no '='): {stripped!r}"
        key, _, value = stripped.partition("=")
        parsed[key] = value
    return parsed


class TestEnvFileIntegrity:
    """Structural sanity checks on the .env file itself."""

    def test_env_file_exists(self):
        assert os.path.isfile(ENV_PATH)

    def test_env_file_is_not_empty(self, env_lines):
        assert len(env_lines) > 0

    def test_no_duplicate_keys(self, env_lines):
        keys = [
            line.split("=", 1)[0]
            for line in env_lines
            if line.strip() and not line.strip().startswith("#")
        ]
        assert len(keys) == len(set(keys)), f"Duplicate keys found in .env: {keys}"

    def test_every_non_comment_line_has_key_value_format(self, env_lines):
        for line in env_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            key, _, _ = stripped.partition("=")
            assert key, f"Line is missing a key before '=': {stripped!r}"


class TestEnvFileOllamaSettings:
    """Tests for the new Ollama-related keys added by this PR."""

    def test_ollama_url_key_present(self, env_dict):
        assert "OLLAMA_URL" in env_dict

    def test_ollama_url_value_matches_expected_service_address(self, env_dict):
        assert env_dict["OLLAMA_URL"] == "http://ollama:11434"

    def test_ollama_model_key_present(self, env_dict):
        assert "OLLAMA_MODEL" in env_dict

    def test_ollama_model_value_matches_expected_default(self, env_dict):
        assert env_dict["OLLAMA_MODEL"] == "llama3.1"

    def test_ollama_url_uses_http_scheme(self, env_dict):
        assert env_dict["OLLAMA_URL"].startswith("http://")


class TestEnvFilePreExistingKeysUnaffected:
    """Regression checks that pre-existing keys were not touched by this PR."""

    @pytest.mark.parametrize("key", ["DATABASE_URL", "SECRET_KEY", "ACCESS_TOKEN_EXPIRE_MINUTES"])
    def test_pre_existing_key_still_present(self, env_dict, key):
        assert key in env_dict

    def test_access_token_expire_minutes_unchanged(self, env_dict):
        assert env_dict["ACCESS_TOKEN_EXPIRE_MINUTES"] == "1440"