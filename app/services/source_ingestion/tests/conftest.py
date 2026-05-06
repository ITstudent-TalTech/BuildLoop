"""Source ingestion test suite configuration.

These tests do NOT require a live database, Supabase Storage, or the real
EHR endpoint. All I/O is mocked at the boundary:
  - httpx: patched via pytest-httpx or unittest.mock
  - AsyncSession: AsyncMock with explicit side_effect chains
  - Supabase Storage: a FakeStorage class that records uploads in memory

Dummy env vars are set here so that Settings() instantiation does not
raise a ValidationError on missing required fields.
"""

import os

# Must be set before any app module is imported — lru_cache picks them up.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/buildloop_test")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("INGEST_EHR_BASE_URL", "https://test-ehr.example.com/api/document/v1")
os.environ.setdefault("INGEST_EHR_SSL_FALLBACK", "true")
os.environ.setdefault("INGEST_EHR_TIMEOUT_SECONDS", "60")
