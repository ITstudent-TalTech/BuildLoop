"""Source parsing test suite configuration.

These tests do NOT require a live database or Supabase Storage.
All I/O is mocked at the boundary (AsyncSession, storage download).

Dummy env vars must be set before any app module is imported —
lru_cache picks them up on first import.
"""

import os
from pathlib import Path

# Set before any app module is imported.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/buildloop_test")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")

FIXTURE_PDF_PATH = Path(__file__).parent / "fixtures" / "pdfs" / "lai_1_101035685.pdf"
GOLDEN_FILE_PATH = Path(__file__).parent / "fixtures" / "expected" / "lai_1_observations.json"
