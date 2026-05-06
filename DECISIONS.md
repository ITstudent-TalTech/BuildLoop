# BUILDLoop — Project Decisions & Context

> **Purpose:** This file gives any team member full context on decisions made
> during development. Read this before starting any session with Claude Code,
> Codex, or any AI agent. It is the authoritative summary of the project's
> direction.

---

## What BUILDLoop Is

A two-sided platform for circular construction in Estonia:

1. **Digital Material Passports** — uses the Estonian construction register
   (EHR) + AI to auto-document what materials exist in a building, where,
   and in what condition.
2. **Marketplace** — where those materials can be bought/sold before a
   building is demolished or renovated.

**Mission:** Make material reuse the default, not the exception.
**Starting market:** Estonia → EU via franchise model.

---

## Repository Structure

```
BuildLoop/
├── app/                    # FastAPI backend (Track 2, in progress)
├── web/                    # Next.js 14 frontend (Track 1, complete)
├── alembic/                # DB migrations
├── tests/                  # Pytest
├── skills/                 # Workflow documentation (read-only)
├── design-references/      # Claude Design exports (read-only specs)
├── 00_*.md – 12_*.md       # Architecture pack (binding)
├── buildloop_passport_from_address.py        # Working extraction script
├── buildloop_passport_from_address_colab_v3.py  # Working extraction script
├── AGENTS.md               # Root agent instructions
├── PROGRESS.md             # Cross-cutting progress tracker
└── DECISIONS.md            # This file
```

---

## Architecture Decisions

### Frontend

| Decision           | Choice                             | Reason                                                            |
| ------------------ | ---------------------------------- | ----------------------------------------------------------------- |
| Framework          | Next.js 14 (App Router)            | SSR, file-based routing, RSC support                              |
| Styling            | Tailwind CSS utility classes       | No CSS modules, no styled-components                              |
| Language           | TypeScript strict mode             | No `any` types allowed                                            |
| Component model    | React Server Components by default | Client Components only where interactivity is needed              |
| State management   | Vanilla React state + Context      | No Zustand, no Redux — kept simple                                |
| API layer          | Typed client + mocks               | `web/lib/api/` — mocks first, real backend later                  |
| Routing convention | URL-driven state transitions       | Each step (intake → resolve → draft → published) is its own route |

### Backend

| Decision                   | Choice                               | Reason                                                         |
| -------------------------- | ------------------------------------ | -------------------------------------------------------------- |
| Framework                  | FastAPI                              | Async-first, Pydantic integration, auto-docs                   |
| ORM                        | SQLAlchemy 2.0 async (asyncpg)       | Async I/O, modern Mapped[] typing                              |
| Migrations                 | Alembic is source of truth           | Autogenerate from ORM models; doc 10 SQL is reference only     |
| Data plane                 | Supabase (Postgres + Storage + Auth) | Managed Postgres, built-in storage, EU region                  |
| Supabase connection method | Session pooler (port 5432, asyncpg)  |
| Config                     | Pydantic Settings                    | Secrets never committed; app fails to start if secrets missing |
| PDF parsing                | pypdf primary, pdfplumber fallback   | Pure Python, no system binary dependencies                     |
| PDF generation             | WeasyPrint + Jinja2                  | HTML → PDF, pure Python, works on Railway                      |
| Auth                       | Supabase Auth (magic link)           | JWT propagated to FastAPI; RLS on Postgres                     |

### Infrastructure

| Decision         | Choice                                      | Reason                                        |
| ---------------- | ------------------------------------------- | --------------------------------------------- |
| Frontend hosting | Vercel                                      | Tight Next.js integration, free tier          |
| Backend hosting  | Railway                                     | Always-on (no cold starts), free trial credit |
| Database         | Supabase free → Pro before contractor demos | Managed Postgres, EU region                   |
| Monorepo         | Yes — `web/` and `app/` in one repo         | Simpler for small team                        |

---

## The Five Tracks

```
Track 1 — Frontend screens (COMPLETE ✅)
Track 2 — Backend script-to-modules (IN PROGRESS 🔄)
Track 3 — Backend ↔ Frontend integration (PENDING)
Track 4 — Supabase Auth + RLS (PENDING)
Track 5 — Validation + deployment + tests (PENDING)
```

### Track 1 is complete. What was built:

- **Design system:** Brand tokens in `web/BRAND.md`, three screens designed
  in Claude Design (intake, candidate selection, passport draft)
- **Shared primitives:** `TopBar`, `StepIndicator`, `FieldRow`,
  `EvidenceBadge`, `SectionCard` — all in `web/components/shared/`
- **Typed API layer:** `web/lib/api/` — `types.ts`, `client.ts`, `mocks.ts`,
  `mock-config.ts`, fixtures for intake / resolution / passport drafts
- **Five real routes:**
  - `/` — landing page
  - `/intake` — address form with resolver dispatch
  - `/intake/resolve` — candidate selection (ambiguous / unresolved states)
  - `/passport/[id]` — read-only draft view (all 7 canonical sections)
  - `/passport/[id]/review` — per-field inline editing + audit trail + publish
  - `/passport/[id]/published` — publication confirmation
  - `/dev/components` — component playground (not user-facing)
- **Mock env vars** (in `web/.env.local`, gitignored):
  - `MOCK_RESOLUTION_MODE` = `resolved` | `ambiguous` | `unresolved`
  - `MOCK_DRAFT_VARIANT` = `complete` | `partial` | `sparse`
  - `MOCK_DELAY_MS` = artificial network delay (default 500)
  - `MOCK_FAIL_NEXT` = `status:code:message` (one-shot failure injection)

### Track 2 — Backend plan (in order):

| Session | Agent                  | What it does                                                                                    |
| ------- | ---------------------- | ----------------------------------------------------------------------------------------------- |
| **2.1** | Substrate              | Supabase schema applied, async SQLAlchemy, alembic baseline, Pydantic Settings, health endpoint |
| 2.2     | Resolver               | Address normalization, In-ADS queries, EHR code resolution, confidence scoring                  |
| 2.3     | Ingestion              | EHR PDF fetching, Supabase Storage, deduplication                                               |
| 2.4     | Parser                 | PDF text extraction, field extraction per doc 03 schema, observation generation                 |
| 2.5     | Relevance + Projection | Relevance classification, passport draft generation, quality scoring                            |
| 2.6     | API contracts          | FastAPI routes matching `web/lib/api/types.ts` exactly                                          |
| 2.7     | Review + Publication   | Manual edits, audit trail, immutable PassportVersion, PDF export                                |
| 2.8     | Product integration    | Listing-candidate stubs, export payloads, admin glue                                            |

**Integration rule:** after each backend session group, a Track 3 integration
session replaces the corresponding mock calls in `web/lib/api/client.ts` with
real `fetch` calls. Don't wait for the whole backend to be done.

---

## The Canonical Schema (binding)

The canonical schema in `03_PASSPORT_DOMAIN_MODEL_AND_CANONICAL_SCHEMA.md`
is the single source of truth for passport content. **Three rules that are
non-negotiable:**

1. **UI labels are always plain language.** Never expose raw schema keys
   (`heated_area_m2`, `load_bearing_material`) in the UI. The label is
   always human-readable ("Heated area", "Load-bearing material").
2. **Every field is a `FieldValue<T>`.** Each value carries confidence,
   source provenance (page number, document), and last-updated timestamp.
3. **Never invent fields outside the schema namespaces** (identity,
   building_profile, structural_systems, technical_systems, location,
   building_parts, quality). If the extraction scripts surface something
   not in doc 03, flag it — don't silently extend.

---

## The Two Reference Scripts

`buildloop_passport_from_address.py` (~35 KB) and the colab v3 variant
(~48 KB) contain **validated, working** extraction logic for real Estonian
buildings. They are the source of truth for what the backend should do.

**Track 2 is a structured refactoring of these scripts into the module
architecture described in doc 04.** The scripts are frozen — do not modify
them. Copy logic out, restructure into modules, write tests.

---

## API Contract Handshake

`web/lib/api/types.ts` and the FastAPI Pydantic models in `app/schemas/`
must stay in sync. This is the integration boundary. When doc 11 says a
field exists, it exists in both. When you change one, change the other.

Key type: `FieldValue<T>`:

```typescript
type FieldValue<T> = {
  value: T | null;
  unit?: string;
  confidence: "high" | "medium" | "low";
  source?: { document_id: string; page?: number; label: string };
  last_updated?: string; // ISO 8601
};
```

The `ResolutionResponse` is a discriminated union on `status`:
`'resolved' | 'ambiguous' | 'unresolved'` — do not flatten this.

---

## Agent Instructions Summary

Every AI agent session should start by reading:

**For frontend work (from `/web/`):**

- `/web/AGENTS.md`
- `/web/BRAND.md`
- `/PROGRESS.md`

**For backend work (from `/app/`):**

- `/app/AGENTS.md`
- `/03_PASSPORT_DOMAIN_MODEL_AND_CANONICAL_SCHEMA.md`
- `/11_FASTAPI_API_CONTRACTS.md`
- `/12_CODEX_AGENT_TASK_CARDS.md` (the specific agent card for the session)
- `/PROGRESS.md`

**Sessions in any track may always update `/PROGRESS.md`.**
Sessions must stay within their assigned directory scope otherwise.

---

## What the New Team Member Should Do First

1. Clone the repo: `git clone https://github.com/ITstudent-TalTech/BuildLoop.git`
2. Read this file top to bottom.
3. Read `PROGRESS.md` to see current status.
4. Read `12_CODEX_AGENT_TASK_CARDS.md` to understand agent boundaries.
5. Open `web/` in VS Code for frontend, `app/` for backend.
6. Run the frontend: `cd web && npm install && cp .env.example .env.local && npm run dev`
7. Visit `http://localhost:3000` — the full mocked frontend is running.
8. To run a backend agent session: install Claude Code (`npm install -g @anthropic-ai/claude-code`),
   run `claude` from the repo root, and paste the session prompt from the team.

---

## Open Items Before First Contractor Demo

- [ ] Session 2.1 — backend substrate (next session, ready to start)
- [ ] Deploy frontend to Vercel (mocks-only deploy, shareable URL)
- [ ] Schedule 5-10 contractor interviews in Tallinn (doc 01 validation step)
- [ ] Upgrade Supabase to Pro tier before demos
- [ ] Create Railway project for FastAPI hosting

## Resolved technical debt

**JSONB-blob FK in intake_requests (resolved in hotfix after 2.3).**
Initially `project_id` was stored as `{"project_id": str(uuid)}` inside
`intake_requests.normalized_input` JSONB to avoid creating a migration during
session 2.2. Replaced with a proper nullable FK column
(`intake_requests.project_id → projects.id ON DELETE SET NULL`) in migration
`734960e74be2`. The JSONB approach was rejected because it conflicted with that
column's intended purpose (storing the resolver's parsed address shape) and
forced `ResolverService` to carry cross-module knowledge of an internal storage
convention. The `normalized_input` column remains and is initialized to `{}`
by `IntakeService`; the resolver will populate it with the parsed address shape
in a later session.

---

## Algorithmic deviations from reference scripts

These are intentional changes from the validated extraction scripts at
repo root, made during Track 2 sessions. Documented here so they're
auditable rather than buried in code comments.

### Resolver (Session 2.2 — `app/services/resolver/`)

**Multi-variant confidence bonus.** `score_candidate()` adds +0.05 to
the confidence score when the same EHR code was found by more than one
query variant. The script's `score_candidate()` (line 214) doesn't do
this. Added to satisfy doc 12 Agent 2's "same EHR code reached via
multiple variants → confidence boosted" acceptance criterion. Effect:
candidates scoring 0.81–0.85 in the script can now auto-resolve at
0.86–0.90 if found by ≥2 variants. Resolver version bumped to
v1.1.0 to flag the deviation in `address_resolution_runs.resolver_version`.

**Corner-address alias extraction.** `_extract_corner_aliases()` in
candidate_grouper.py splits a `//`-composite address into individual
street-name aliases. The script doesn't emit clean alias lists — it
preserves the composite string ambient in `taisaadress`. This explicit
extraction was added to populate `address_aliases` in the API response
shape doc 11 specifies. Behavior matches the corner-address mental
model used throughout the architecture pack (doc 03 Rule 2).

**Known preserved bug.** `_walk_for_ehr_candidates` in candidate_grouper.py
double-adds EHR entries when an "ehr" list branch fires AND the
recursive walk also hits "ehr_kood" inside each item. The original
script's `seen` set masked this; here, CandidateGroup merging masks it
instead. Flagged with TODO(2.2 review). To revisit if duplicate-handling
performance matters at scale.

### Source Ingestion (Session 2.3 — `app/services/source_ingestion/`)

**Upload to Supabase Storage only — no local disk.** The script's
`fetch_pdf()` writes the PDF bytes to a local `out_path: Path` argument
(line 348). In `app/services/source_ingestion/`, there is no local disk
write; bytes go directly to Supabase Storage via `app.core.storage.upload_source_document`.
Track 2.4 (parser) will retrieve PDF bytes back from Storage. This is
a deliberate infrastructure decision — see the session 2.3 prompt heading
"INFRASTRUCTURE DECISION LOCKED".

**Checksum-based dedup scoped to (building_id, checksum).** The reference
script has no dedup concept — each run creates a new artifact file. The
service layer adds a dedup check keyed on `(building_id, checksum)` before
uploading, so the same EHR PDF is stored only once in Supabase Storage
regardless of how many user projects trigger a fetch. `project_id` is
still logged on the `source_documents` row for audit. This is a new
behavior not present in the script.

**URL path verified from script — differs from session prompt.** The
session 2.3 prompt described the URL as `{EHR_BASE_URL}/{ehr_code}/file`.
The script (line 341) uses `{EHR_BASE_URL}/pdf/document/file/{ehr_code}`.
The implementation follows the script as the source of truth.
`ehr_fetcher.py` has a comment documenting this discrepancy.

**Timeout deviation flagged.** The script uses `timeout=90` (line 346);
the `INGEST_EHR_TIMEOUT_SECONDS` setting defaults to 60 per the session
spec. Flagged with `TODO(2.3 review)` in `ehr_fetcher.py`. Verify with
EHR operator before production; bump the setting if long PDFs require 90s.
