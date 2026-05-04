# BUILDLoop Backend — Agent Instructions

## What this is

The FastAPI service that powers BUILDLoop. Workflow engine for
passport generation: address resolution, source document ingestion,
parsing, observation extraction, relevance projection, passport
drafting, manual editing, and publication.

## Stack decisions (do not deviate without flagging)

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 with async session (asyncpg driver)
- Alembic as the source of truth for schema migrations.
  Doc 10 SQL is reference documentation; migrations are
  authored against SQLAlchemy models and applied via alembic.
- Supabase as data plane: Postgres for relational data,
  Storage for source PDFs and generated passport PDFs,
  Auth for user identity (Track 4).
- Pydantic Settings for env config; secrets never committed.
- pypdf primary, pdfplumber fallback for PDF parsing.
- WeasyPrint for passport PDF generation (Track 2 session 2.7).
- Hosting: Railway. Free tier through MVP, paid before contractor demos.

## Repo structure

- /app/ — Service code
  - main.py — FastAPI app instantiation
  - core/ — config, logging, exceptions
  - db/ — SQLAlchemy base, session factory
  - models/ — ORM models, one per aggregate root
  - services/ — Domain services per agent task card:
    - resolver/
    - source_ingestion/
    - source_parsing/
    - relevance_engine/
    - passport_engine/
    - review/
    - exporter/
  - api/routes/ — FastAPI route groups, one per resource
  - schemas/ — Pydantic request/response models
- /alembic/ — Migrations
- /tests/ — Pytest, async fixtures, factory_boy

## Architecture pack (binding)

Read these before any non-trivial change. Listed by file at repo root:

- 03_PASSPORT_DOMAIN_MODEL_AND_CANONICAL_SCHEMA.md — canonical
  observation/passport schema. Module field names match this.
- 04_PASSPORT_MVP_SYSTEM_ARCHITECTURE.md — module boundaries.
- 05_DATA_RELEVANCE_POLICY.md — relevance classification rules.
- 07_HYBRID_STACK_DECISION_AND_DEPLOYMENT_ARCHITECTURE.md — Supabase
  - FastAPI split rationale.
- 10_SUPABASE_SCHEMA_SQL.sql — reference for table shapes; alembic
  is the source of truth, but new tables match this shape.
- 11_FASTAPI_API_CONTRACTS.md — API endpoints (must match
  /web/lib/api/types.ts exactly, this is the integration handshake).
- 12_CODEX_AGENT_TASK_CARDS.md — agent boundaries. Stay within
  the agent's scope when running its session.

## Conventions

- Type hints required everywhere. mypy strict eventually; no
  bare `Any` except where strictly necessary (PDF parsing dicts).
- Pydantic models are the wire format; SQLAlchemy models are the
  storage format; mappers convert between them in services.
- Every route handler is < 30 lines and delegates to a service.
- Every service function has a docstring stating its contract:
  inputs, outputs, persistence side effects, raised exceptions.
- Tests live alongside the module: app/services/resolver/tests/
  test_normalizer.py, etc. Pytest with async fixtures.
- Alembic migrations: descriptive names, never edit a committed
  migration, always test up + down on a scratch DB.

## Working agreement

- Stay within the agent's scope per doc 12's task cards.
- Read doc 03 (canonical schema) and doc 11 (API contracts) before
  any service or route work.
- Never invent fields not in doc 03's schema.
- Never bypass the resolver's audit trail (every resolution has a
  resolver_run row; every observation has a source_document_id).
- Tests are not optional. Each session emits at least one
  fixture-driven test per module.
- If a doc conflicts with implementation reality (e.g., the
  scripts at repo root parse a field doc 03 doesn't list), flag
  it — don't silently extend the schema.
- Sessions may always update /PROGRESS.md.

## Two scripts at repo root, one warning

buildloop_passport_from_address.py and the colab v3 variant contain
the validated extraction logic. They are reference, not source. Track
2 sessions carve them into the modules above. Do NOT modify these
scripts in place — copy logic out, restructure, write tests. The
scripts stay frozen until Track 2.8 product-integration cleanup.
