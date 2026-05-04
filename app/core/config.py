from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env.local.

    Secrets (database_url, supabase_*_key) have no defaults — the app
    will fail at startup with a clear ValidationError if any are missing.
    """

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    database_url: str  # full async URL: postgresql+asyncpg://user:pass@host:port/db

    # --- Supabase ---
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_storage_source_bucket: str = "source-documents"
    supabase_storage_passport_bucket: str = "published-passports"

    # --- Runtime ---
    env: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"

    # --- CORS ---
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
