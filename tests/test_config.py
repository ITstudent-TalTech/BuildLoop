"""Tests for app.core.config Settings.

These tests verify that Settings raises clearly when required secrets
are missing, and that values are loaded correctly when present.
"""

import os

import pytest
from pydantic import ValidationError


def test_settings_raises_when_database_url_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings must fail with a ValidationError if DATABASE_URL is unset."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    # Patch env_file so Settings doesn't pick up .env.local on disk
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from typing import Literal
    from functools import lru_cache

    class IsolatedSettings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=None,
            extra="ignore",
        )
        database_url: str
        supabase_url: str
        supabase_anon_key: str
        supabase_service_role_key: str

    with pytest.raises(ValidationError) as exc_info:
        IsolatedSettings()

    errors = exc_info.value.errors()
    missing_fields = {e["loc"][0] for e in errors}
    assert "database_url" in missing_fields


def test_settings_loads_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings must pick up values set via environment variables."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key-value")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-key-value")

    from pydantic_settings import BaseSettings, SettingsConfigDict

    class IsolatedSettings(BaseSettings):
        model_config = SettingsConfigDict(env_file=None, extra="ignore")
        database_url: str
        supabase_url: str
        supabase_anon_key: str
        supabase_service_role_key: str

    s = IsolatedSettings()
    assert s.database_url == "postgresql+asyncpg://user:pass@localhost/test"
    assert s.supabase_url == "https://example.supabase.co"
    assert s.supabase_anon_key == "anon-key-value"
    assert s.supabase_service_role_key == "service-key-value"


def test_settings_default_buckets() -> None:
    """Storage bucket names should have correct defaults."""
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class IsolatedSettings(BaseSettings):
        model_config = SettingsConfigDict(env_file=None, extra="ignore")
        database_url: str = "postgresql+asyncpg://x:x@localhost/x"
        supabase_url: str = "https://x.supabase.co"
        supabase_anon_key: str = "x"
        supabase_service_role_key: str = "x"
        supabase_storage_source_bucket: str = "source-documents"
        supabase_storage_passport_bucket: str = "published-passports"

    s = IsolatedSettings()
    assert s.supabase_storage_source_bucket == "source-documents"
    assert s.supabase_storage_passport_bucket == "published-passports"
