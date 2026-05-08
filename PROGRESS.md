# BUILDLoop — Progress

Last updated: 2026-05-04
Current phase: Track 2 (backend, script-to-modules)
Current session: 2.3 (Ingestion) — next up

## Done

### Pre-implementation

- ✅ Architecture pack written (docs 00–12 at repo root: canonical schema,
  validated workflow, hybrid stack decision, Supabase schema SQL,
  FastAPI route contracts, agent task cards).
- ✅ Two working extraction scripts at repo root
  (`buildloop_passport_from_address.py`,
  `buildloop_passport_from_address_colab_v3.py`) — reference, not yet
  integrated into the modular FastAPI app.
- ✅ FastAPI scaffold: `/v1/health` endpoint, `Building` and `Project`
  SQLAlchemy models, alembic init migration. (To be replaced in 2.1.)

### Track 1 — Frontend ✅

- ✅ `/web/` Next.js 14 App Router scaffold (TypeScript strict, Tailwind).
- ✅ `/web/BRAND.md` brand block.
- ✅ `/web/AGENTS.md`, `/AGENTS.md` (root), `/web/CLAUDE.md` for agent-driven
  development.
- ✅ `/web/design_references/` with three Claude Design exports
  (intake, candidate selection, passport draft) — read-only specs.
- ✅ Tailwind tokens (forest, forest-light, surface, ink, ink-soft).
- ✅ Shared primitives in `/web/components/shared/`: TopBar, StepIndicator,
  FieldRow, EvidenceBadge, SectionCard.
- ✅ Demo route at `/dev/components` showing all primitives in isolation.
- ✅ Typed API client + mocks layer at `/web/lib/api/` matching doc 11
  contracts: types.ts, client.ts, mocks.ts, mock-config.ts, fixtures
  (intake, resolution, passport-drafts).
- ✅ Session 1.1 — Intake screen at `/intake`, four form states,
  resolver dispatch.
- ✅ Session 1.2 — Resolution screen at `/intake/resolve`, ambiguous +
  unresolved + error states.
- ✅ Session 1.3 — Passport draft view at `/passport/[id]` composing all
  primitives across seven canonical sections.
- ✅ Session 1.4 — Review/edit screen at `/passport/[id]/review` with
  per-field inline editing, audit trail, publish flow.
- ✅ Session 1.5 — Publication confirmation, landing page, EHR direct
  entry, visual polish, responsive behavior, deploy prep.

### Closeout fixes (after Track 1)

- ✅ `/web/eslint.config.mjs` ignores `design_references/**`.
- ✅ `/web/AGENTS.md` permits PROGRESS.md updates from any session.
- ✅ `/AGENTS.md` (root) needs the same PROGRESS.md exception line.
- ✅ `/PROGRESS.md` created (this file).
- ✅ `/app/AGENTS.md` and `/app/CLAUDE.md` drafted for Track 2.

## In progress

- 🔄 Pre-2.1 prep: dropping `/PROGRESS.md`, `/app/AGENTS.md`,
  `/app/CLAUDE.md`, updating `/AGENTS.md` with PROGRESS exception.

## Next sessions

### Track 2 — Backend script-to-modules

- ✅ 2.1 — Substrate (Agent 1): async SQLAlchemy + asyncpg, alembic
  baseline matching doc 10, Pydantic Settings, Supabase storage client,
  health endpoint reporting DB + storage status.
- ✅ 2.2 — Resolver (Agent 2): carve from
  `buildloop_passport_from_address.py` into
  `app/services/resolver/` (normalizer, query_variants, inads_adapter,
  candidate_grouper, confidence). Persist resolver runs + candidates.
  Fixture-based tests with real Tallinn cases.
- ✅ 2.3 — Ingestion (Agent 3): EHR PDF fetch into
  `app/services/source_ingestion/` with Supabase Storage and
  checksum-based deduplication.
- 📋 2.4 — Parser (Agent 4): PDF extraction into
  `app/services/source_parsing/` producing canonical observations
  with provenance. Highest-risk session.
- 📋 2.5 — Relevance + projection (Agent 5):
  `app/services/relevance_engine/` and `app/services/passport_engine/`
  producing draft JSON matching doc 03.
- 📋 2.6 — API contracts (Agent 7): `app/api/routes/` filled per doc 11.
  Pydantic models matching `web/lib/api/types.ts` exactly.
- 📋 2.7 — Review + publication (Agent 6): manual edits, audit trail,
  immutable PassportVersion, WeasyPrint PDF export.
- 📋 2.8 — Product integration stubs (Agent 8): listing-candidate stubs,
  export payloads, admin glue.

### Track 3 — Backend ↔ Frontend integration (interleaved)

- 📋 3.1 — Wire intake + resolution endpoints (after 2.2).
- 📋 3.2 — Wire source ingestion + parsing + draft (after 2.5).
- 📋 3.3 — Wire review + publication (after 2.7).

### Track 4 — Supabase substrate

- 📋 4.1 — Auth flow (Supabase magic link, parallel with early Track 2).
- 📋 4.2 — RLS policies (after 2.1).
- 📋 4.3 — Storage bucket policies.

### Track 5 — Validation + deploy

- 📋 5.1 — Vercel deploy (frontend, mocks-only).
- 📋 5.2 — Railway deploy (FastAPI, after 2.6).
- 📋 5.3 — Integration tests (after 3.3).
- 📋 5.4 — Contractor interviews (5-10 in Tallinn).
- 📋 5.5 — Renovator survey (50+ respondents).

## Decisions

| Decision              | Value                                           |
| --------------------- | ----------------------------------------------- |
| Frontend hosting      | Vercel                                          |
| FastAPI hosting (MVP) | Railway $5 trial credit → Hobby $5/mo           |
| PDF parsing           | pypdf primary, pdfplumber fallback              |
| PDF generation        | WeasyPrint with Jinja2 templates                |
| Auth strategy         | Supabase Auth (magic link)                      |
| Supabase project tier | Free → Pro before contractor demos              |
| Repo structure        | Monorepo                                        |
| SQLAlchemy mode       | 2.0 async (asyncpg driver)                      |
| Alembic vs doc 10 SQL | Alembic is source of truth; doc 10 is reference |

## Reference

- Architecture pack: `/00_*.md` through `/12_*.md`
- Canonical schema (binding): `/03_PASSPORT_DOMAIN_MODEL_AND_CANONICAL_SCHEMA.md`
- API contracts (binding): `/11_FASTAPI_API_CONTRACTS.md`
- Agent boundaries: `/12_CODEX_AGENT_TASK_CARDS.md`
- Frontend conventions: `/web/AGENTS.md`
- Backend conventions: `/app/AGENTS.md`
- Brand tokens: `/web/BRAND.md`
- Decision summary: `/DECISIONS.md`

## Update protocol

At the end of each Cowork/Claude Code session, append a one-line entry to
the session log below and move the corresponding ⏳/📋 item to ✅ in the
sections above.

## Session log

- 2026-04-26 — Established frontend scaffold, primitives, API mocks layer.
- 2026-04-26 — Session 1.1 complete: intake screen at `/intake`.
- 2026-04-26 — Session 1.2 complete: resolution screen with ambiguous +
  unresolved + error states.
- 2026-04-26 — Session 1.3 complete: passport draft view, all seven
  sections composed.
- 2026-04-26 — Session 1.4 complete: review/edit screen with per-field
  inline editing, audit trail, publish flow.
- 2026-04-26 — Session 1.5 complete: Track 1 frontend MVP feature-complete.
- 2026-05-03 — Pre-2.1 prep: PROGRESS.md, /app/AGENTS.md, /app/CLAUDE.md
  staged; /AGENTS.md updated with PROGRESS exception.
- 2026-05-03 — Session 2.1 complete: backend substrate. Async SQLAlchemy
  - asyncpg, full ORM model coverage (14 tables), alembic baseline migration
    matching doc 10, Pydantic Settings, Supabase storage client, health
    endpoint reporting DB and storage status. Foundation for Track 2 work.
- 2026-05-03 — Session 2.1 complete: backend substrate. 14 tables migrated to Supabase via Session pooler. Health endpoint reports DB + storage. Foundation ready for Track 2 service work.
- 2026-05-04 — Session 2.2 complete: resolver carved into modules
  (normalizer, query_variants, inads_adapter, candidate_grouper,
  confidence, service). /v1/intakes and /v1/resolutions endpoints
  match doc 11. Fixture-based tests pass for resolved/corner/
  ambiguous/unresolved cases. SSL fallback preserved behind
  RESOLVER_INADS_SSL_FALLBACK setting. Two algorithmic deviations
  from script flagged in DECISIONS.md: +0.05 multi-variant bonus,
  explicit corner-alias extraction. resolver_version='v1.1.0'.
- 2026-05-06 — Session 2.3 complete: source ingestion module carved, EHR PDF fetch uploads to Supabase Storage with checksum dedup. /v1/projects/{id}/sources/fetch and GET endpoints match doc 11. Fixture-based tests pass for clean / failure / dedup cases.
- 2026-05-06 — Hotfix on 2.1/2.2: declared 6 missing indexes on models (no migration needed); replaced JSONB project_id workaround in IntakeService with proper FK column on intake_requests. Migration 734960e74be2 applied to Supabase. alembic check clean. 60 resolver tests pass, mypy clean.
- 2026-05-07 — Resolver hotfix: candidate walker rewritten to handle real In-ADS response shape (addresses[].ehr[] with address fields on outer node). Synthetic fixtures replaced with real captured API response for Lai 1, 10133 Tallinn. End-to-end smoke test against live In-ADS now produces expected resolved status with corner aliases.
- 2026-05-08 — Resolver hotfix: added in_ads_primary scoring signal (+0.10 when In-ADS marks entry primary='true'). CandidateGroup.in_ads_primary field added; captured in _structured_walk, propagated in group_candidates, scored in score_candidate. 3 new tests. resolver_version bumped to v1.2.0. 64 resolver tests pass.
- 2026-05-08 — Track 2 hotfix: /v1/health now strictly verifies both Supabase Storage buckets exist; reports missing_buckets status when not. Startup warning added. storage='unavailable' now triggers 503. 5 health tests pass.
