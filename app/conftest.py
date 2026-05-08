"""Root conftest for the app package.

Provides a fallback DATABASE_URL_TEST so that unit/integration tests that mock
the database layer (e.g. health endpoint tests) can run without a live Postgres
instance. Tests that genuinely need a real DB (test_db fixture) will fail to
connect at the dummy URL — set DATABASE_URL_TEST to a real test-DB URL in those
environments.
"""

import os

os.environ.setdefault(
    "DATABASE_URL_TEST",
    "postgresql+asyncpg://test:test@localhost:5432/buildloop_test_fake",
)
