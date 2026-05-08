"""Relevance engine test configuration.

No live DB or Supabase needed — all classification tests are pure functions
or use mocked AsyncSession.  Env vars set here so Settings initialises cleanly.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/buildloop_test")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
