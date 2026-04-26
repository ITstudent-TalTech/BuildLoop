# 07. Hybrid Stack Decision and Deployment Architecture

## Decision

The product should adopt a **hybrid stack**:

- **Supabase** as the product data plane
- **FastAPI** as the passport engine and workflow API

This is not a compromise between two tools. It is a deliberate fit to the validated workflow and the product's likely evolution.

## Why Supabase fits

Supabase is a strong fit for the product platform layer because BUILDLoop needs:

- managed Postgres
- Auth
- Row Level Security
- file storage for source PDFs, generated passports, and uploaded photos
- product-friendly admin/dashboard development
- a clean operational foundation for an AI-first team

### Supabase responsibilities
- user accounts and organizations
- projects
- passports and versions
- manual edits and review state
- storage buckets for source and export artifacts
- notifications and light server-side glue
- access control through RLS

## Why FastAPI fits

FastAPI is a strong fit for the domain engine because the validated workflow is Python-heavy and document-centric:

- resolver orchestration
- EHR source adapters
- PDF ingestion
- PDF interpretation
- canonical observation generation
- relevance filtering
- passport projection
- future listing derivation

### FastAPI responsibilities
- intake API
- resolver API
- source ingestion API
- parser/orchestration jobs
- relevance engine
- passport draft generation
- review re-projection
- export endpoints

## Why not "Supabase only"

A Supabase-only architecture would push the core passport engine into places where it does not fit naturally.
The current core problem is not CRUD. It is deterministic document interpretation and domain projection.
That should remain a Python application concern.

## Why not "FastAPI only"

A FastAPI-only stack would force the team to rebuild product infrastructure that Supabase already provides well:
- Auth
- RLS-backed access control
- storage workflows
- a fast path to internal/admin product surfaces

## Deployment topology

### Web client
- Next.js / React app
- uses Supabase Auth for sign-in
- calls FastAPI for workflow actions

### Supabase
- Postgres
- Auth
- Storage
- optional Realtime
- optional Edge Functions for lightweight jobs / webhooks

### FastAPI service
- passport engine
- resolver/source adapters
- background workers
- integration layer to Supabase DB and Storage

### Background workers
- source fetch jobs
- PDF extraction jobs
- parser jobs
- re-projection jobs
- export jobs

## Data access pattern

### Writes
FastAPI should own workflow-critical writes:
- source documents
- observations
- extraction runs
- draft generation
- passport versions

### Reads
Frontend can read some product views directly from Supabase when safe through RLS:
- projects
- published passports
- user project dashboards

For workflow-critical reads, the frontend should use FastAPI endpoints that understand workflow state.

## Storage model

### Supabase Postgres
Canonical application data:
- buildings
- projects
- source documents metadata
- extraction runs
- observations
- relevance classifications
- passport drafts
- passport versions
- manual edits
- resolver requests and candidates

### Supabase Storage
Binary artifacts:
- raw resolver response snapshots if needed
- source PDFs
- generated passport PDFs
- user-uploaded photos
- future surveyor attachments

## API model

### FastAPI public workflow endpoints
- `POST /v1/passports/from-address`
- `POST /v1/passports/from-ehr-code`
- `GET /v1/passports/{id}`
- `POST /v1/passports/{id}/recompute`
- `POST /v1/passports/{id}/publish`

### FastAPI admin / review endpoints
- `GET /v1/buildings/{id}/observations`
- `PATCH /v1/passports/{id}/draft`
- `GET /v1/resolution-requests/{id}`
- `GET /v1/source-documents/{id}`

## Job model

Use a queue-backed worker model for:
- resolver retries
- source fetching
- PDF extraction
- parsing
- draft generation
- exports

The web request should enqueue work and return job status when appropriate.
Only trivial operations should be synchronous.

## Product growth path

This hybrid stack scales well into later phases:

### Phase A — passport engine
Supabase + FastAPI are already enough.

### Phase B — marketplace-ready derivation
FastAPI adds listing-candidate derivation and relevance logic.
Supabase stores derived supply objects and user interactions.

### Phase C — marketplace and verification
Supabase handles users, roles, assets, and messaging-adjacent data.
FastAPI handles heavy workflow logic, rule execution, and document processing.

### Phase D — multi-country expansion
Country-specific resolver/source adapters stay in FastAPI.
Core product tables and auth remain in Supabase.

## Rule for Codex

Codex must treat:
- **Supabase** as the platform substrate
- **FastAPI** as the workflow and intelligence layer

It must not collapse the whole system into only one of them.
