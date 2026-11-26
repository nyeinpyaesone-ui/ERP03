import pytest

from app.core.config import Settings
from pydantic import ValidationError


def make_settings(**overrides):
    values = {
        "environment": "test",
        "supabase_url": "https://example.supabase.co",
        "supabase_publishable_key": "local-test-publishable-key",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_supabase_loopback_http_is_allowed_outside_production():
    settings = make_settings(supabase_url="http://127.0.0.1:54321")
    assert settings.supabase_url == "http://127.0.0.1:54321"


def test_supabase_https_is_allowed():
    settings = make_settings(supabase_url="https://example.supabase.co")
    assert settings.supabase_auth_enabled


@pytest.mark.parametrize(
    "url",
    [
        "http://example.supabase.co",
        "http://192.168.1.10:54321",
        "https://user:password@example.supabase.co",
        "https://example.supabase.co/path",
    ],
)
def test_unsafe_supabase_urls_are_rejected(url):
    with pytest.raises(ValidationError):
        make_settings(supabase_url=url)


def test_loopback_http_is_rejected_in_production():
    with pytest.raises(ValidationError):
        make_settings(
            environment="production",
            supabase_url="http://127.0.0.1:54321",
        )
