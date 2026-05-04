# BUILDLoop Codex Architecture Pack v6

This pack is the working implementation package for BUILDLoop's passport-first product strategy.

It assumes the validated workflow is:

**user address -> address resolution -> EHR code -> public EHR PDF -> canonical observations -> relevance filtering -> passport draft -> professional review/edit -> published passport**

It also assumes the selected stack is:

- **Supabase** for Postgres, Auth, Storage, RLS, and product data plane
- **FastAPI** for resolver, source adapters, parsing, observation engine, relevance engine, and passport orchestration

## Reading order

1. `00_EXECUTIVE_REFRAME.md`
2. `01_UPDATED_PRODUCT_ROADMAP.md`
3. `02_VALIDATED_WORKFLOW_AND_SYSTEM_BOUNDARIES.md`
4. `03_PASSPORT_DOMAIN_MODEL_AND_CANONICAL_SCHEMA.md`
5. `04_PASSPORT_MVP_SYSTEM_ARCHITECTURE.md`
6. `05_DATA_RELEVANCE_POLICY.md`
7. `07_HYBRID_STACK_DECISION_AND_DEPLOYMENT_ARCHITECTURE.md`
8. `08_AGENTIC_AI_FIRST_DEVELOPMENT_MODEL.md`
9. `09_MATERIAL_PASSPORT_CONSTRUCT_AND_HYBRID_WORKFLOW.md`
10. `10_SUPABASE_SCHEMA_SQL.sql`
11. `11_FASTAPI_API_CONTRACTS.md`
12. `12_CODEX_AGENT_TASK_CARDS.md`
13. `06_IMPLEMENTATION_PLAN_BACKLOG_AND_AGENTS.md`

## What's new in v6

- full material passport construct defined
- hybrid passport-generation workflow defined explicitly
- concrete Supabase schema SQL added
- concrete FastAPI route contracts added
- Codex-native agent task cards added
- workflow scripts retained for execution continuity

## Product rule

The material passport is not a raw source dump.

It is a **reviewable, versioned, evidence-backed representation of a building's reuse-relevant characteristics**.

## Dev mode and UI skills

- Dev workflow recommendation: `DEV_MODE.md`
- Visual agent skills:
  - `skills/passport-ui-mvp`
  - `skills/passport-ui-scale`

---

## Backend (Track 2)

### Stack

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 async (asyncpg driver)
- Alembic for schema migrations
- Supabase (Postgres data plane, Storage for PDFs)
- Pydantic Settings for environment configuration
- pytest + pytest-asyncio + factory-boy for tests

### Quick start

All backend tooling lives in `app/`. Run commands from there.

```bash
# 1. Copy env template and fill in real Supabase credentials
cp app/.env.example app/.env.local

# 2. Install dependencies (from app/ — packages resolve to repo root)
cd app
pip install -e ".[dev]"

# 3. Apply database migrations (run from app/)
alembic upgrade head

# 4. Run the development server (run from repo root)
cd ..
uvicorn app.main:app --reload
```

The service starts at http://localhost:8000. The health endpoint is at
http://localhost:8000/v1/health.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Full async URL: `postgresql+asyncpg://...` |
| `DATABASE_URL_TEST` | Test only | Separate test DB; required to run pytest |
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service-role key (server use only) |
| `SUPABASE_STORAGE_SOURCE_BUCKET` | No | Default: `source-documents` |
| `SUPABASE_STORAGE_PASSPORT_BUCKET` | No | Default: `published-passports` |

### Running tests

```bash
cd app
DATABASE_URL_TEST=postgresql+asyncpg://postgres:postgres@localhost:5432/buildloop_test pytest
```

Tests never run against the real Supabase. If `DATABASE_URL_TEST` is
unset the suite fails immediately with a clear error.

### Key directories

```
app/                     ← backend root; run pip/alembic/pytest from here
  .env.example           ← copy to app/.env.local and fill in credentials
  pyproject.toml         ← backend deps + tool config
  alembic.ini            ← alembic config; prepend_sys_path=.. for imports
  alembic/versions/      ← 20260503_0001_init_full_schema.py — baseline migration
  tests/                 ← conftest.py, test_health.py, test_config.py
  core/                  ← config.py (Pydantic Settings), storage.py (Supabase)
  db/                    ← base.py (DeclarativeBase, TimestampMixin), session.py
  models/                ← 14 ORM model files, one per aggregate root
  api/routes/            ← health.py — GET /v1/health
web/                     ← frontend (Next.js); see web/.env.local for its env vars
```
