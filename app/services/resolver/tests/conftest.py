"""Resolver test suite configuration.

These tests do NOT require a live database or a real In-ADS endpoint.

Pure-function tests (normalizer, query_variants, candidate_grouper, confidence)
need no fixtures at all.

Service tests use AsyncMock for both the AsyncSession and the InAdsAdapter so
the suite runs without DATABASE_URL_TEST or network access.

Dummy env vars are set here so that Settings() instantiation (triggered lazily
by InAdsAdapter or get_settings() calls) does not raise a ValidationError on
missing required fields.
"""

import os

# Set dummy env vars before any app module is imported.
# The lru_cache on get_settings() picks these up on first call.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/buildloop_test")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
