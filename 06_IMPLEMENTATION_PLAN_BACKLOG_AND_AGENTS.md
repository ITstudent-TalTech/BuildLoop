# 06. Implementation Plan, Backlog, and Codex Agents

## Delivery strategy

Build the system in vertical slices around the validated workflow.

Do not start with the marketplace.
Do not start with full multi-country support.
Do not start with AI-heavy quantity estimation.

Start with the passport engine.

## Sprint structure

### Sprint 0 — Project foundation
#### Goal
Create the implementation skeleton.

#### Deliverables
- FastAPI app scaffold
- PostgreSQL setup
- migrations
- object storage abstraction
- job queue abstraction
- settings / feature flags
- structured logging

#### Tickets
- BL-001 backend scaffold
- BL-002 config and secrets model
- BL-003 database bootstrap
- BL-004 migration framework
- BL-005 object storage abstraction
- BL-006 background job abstraction

---

### Sprint 1 — Building identity and source ingestion
#### Goal
Make address -> EHR -> source document reproducible.

#### Deliverables
- intake endpoint
- resolver module v1/v2/v3 abstraction
- source document persistence
- fetch metadata persistence
- raw resolver response persistence

#### Tickets
- BL-010 intake API
- BL-011 resolver service interface
- BL-012 In-ADS adapter
- BL-013 resolver candidate grouping by EHR code
- BL-014 corner-address alias handling
- BL-015 source ingestion service
- BL-016 fetch retries / SSL fallback policy
- BL-017 source document model

---

### Sprint 2 — PDF parser and observations
#### Goal
Produce canonical observations from the validated EHR PDF.

#### Deliverables
- PDF text extraction service
- deterministic parser
- observation model
- parser test fixtures
- evidence/page extraction

#### Tickets
- BL-020 PDF extraction service
- BL-021 parser section splitter
- BL-022 identity/profile parser
- BL-023 structural systems parser
- BL-024 technical systems parser
- BL-025 geometry parser
- BL-026 building parts parser
- BL-027 observation persistence
- BL-028 parser regression tests

---

### Sprint 3 — Relevance engine and passport draft
#### Goal
Turn observations into a product-quality passport draft.

#### Deliverables
- relevance classifier
- passport draft builder
- quality scoring
- draft API
- draft JSON export

#### Tickets
- BL-030 relevance class model
- BL-031 relevance rules for EHR observations
- BL-032 passport projection engine
- BL-033 schema completeness scoring
- BL-034 confidence rollup scoring
- BL-035 passport draft endpoint
- BL-036 export JSON endpoint

---

### Sprint 4 — Review and publication
#### Goal
Support manual correction and publishable passport versions.

#### Deliverables
- manual edit model
- review API
- published passport versions
- branded PDF render

#### Tickets
- BL-040 manual edit model
- BL-041 review endpoint
- BL-042 re-projection after edits
- BL-043 passport versioning
- BL-044 PDF rendering
- BL-045 export audit trail

---

### Sprint 5 — Marketplace-ready enrichment
#### Goal
Prepare the passport for downstream marketplace usage without fully building the marketplace.

#### Deliverables
- listing_candidate classification
- part grouping heuristics
- item-family taxonomy
- derived listing payload

#### Tickets
- BL-050 listing candidate relevance rules
- BL-051 material family grouping
- BL-052 project-to-listing derivation
- BL-053 listing-ready export schema

## Codex workstreams / agents

### Agent A — Resolver and Intake
Owns:
- intake API
- address normalization
- In-ADS adapter
- candidate grouping
- alias handling
- resolver persistence

Primary files:
- `services/resolver/*`
- `api/intake.py`
- `models/resolution.py`

### Agent B — Source Ingestion
Owns:
- fetch service
- source storage
- source metadata
- retries / SSL fallback

Primary files:
- `services/ingestion/*`
- `models/source_document.py`

### Agent C — Parser and Observations
Owns:
- PDF extraction
- deterministic parser
- parser tests
- observation persistence

Primary files:
- `services/parser/*`
- `models/observation.py`
- `tests/parser/*`

### Agent D — Relevance and Projection
Owns:
- relevance classes
- passport projection
- quality scoring
- export JSON

Primary files:
- `services/relevance/*`
- `services/passport/*`

### Agent E — Review and Publication
Owns:
- manual edits
- published versions
- PDF output
- audit trail

Primary files:
- `services/review/*`
- `services/export/*`

## Codex guardrails

### Guardrail 1
Never let raw EHR field names leak outside the Estonia adapter layer.

### Guardrail 2
Never write directly from raw source into final passport views.

### Guardrail 3
Never silently auto-select low-confidence resolver matches.

### Guardrail 4
Never classify all extracted data as passport-relevant.

### Guardrail 5
Do not build marketplace-specific runtime dependencies into the core passport engine.

### Guardrail 6
Maintain parser fixtures from real sample PDFs and treat them as regression contracts.

## Definition of done for the passport MVP

The passport MVP is done when:

- a user can input an Estonian address
- the system can resolve or present candidates
- the system can fetch the EHR PDF when resolved
- the parser produces canonical observations
- the relevance engine filters output for the passport view
- the passport draft is reviewable
- the published passport is versioned and exportable
- the whole run is reproducible via source artifact + parser version + observation trail

## What Codex should not optimize for yet

- full chat/messaging
- payments
- logistics APIs
- advanced pricing logic
- franchise/admin tooling
- complex AI models for estimation
- multi-country adapters beyond interface definitions
