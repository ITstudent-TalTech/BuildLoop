from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the app/ directory at import time so the .env.local path is
# absolute and independent of the caller's working directory.
_APP_DIR = Path(__file__).parent.parent  # …/BuildLoop/app/


class Settings(BaseSettings):
    """Application settings loaded from app/.env.local.

    Secrets (database_url, supabase_*_key) have no defaults — the app
    will fail at startup with a clear ValidationError if any are missing.
    """

    model_config = SettingsConfigDict(
        env_file=str(_APP_DIR / ".env.local"),
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

    # --- Resolver ---
    # In-ADS gazetteer base URL (Estonian address register public API)
    resolver_inads_base_url: str = "https://inaadress.maaamet.ee/inaadress"
    # Feature layers to request from In-ADS (matches the script default)
    resolver_inads_features: str = "EHAK,VAIKEKOHT,TANAV,KATASTRIYKSUS,EHITISHOONE"
    # Retry without SSL certificate verification on TLS error.
    # Known workaround for Estonian network paths with incomplete cert chains.
    # Set to false in environments with correct PKI.
    resolver_inads_ssl_fallback: bool = True
    # Confidence threshold above which the resolver auto-picks the top candidate.
    resolver_auto_resolve_threshold: float = 0.85
    # Confidence threshold above which the result is ambiguous (not unresolved).
    resolver_ambiguous_threshold: float = 0.50
    # Semver string stamped on every ResolverRun row for regression tracking.
    resolver_version: str = "v1.0.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
