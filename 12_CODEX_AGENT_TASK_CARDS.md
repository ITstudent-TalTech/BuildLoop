# 12. Codex Agent Task Cards

## How to use this file

Each card is designed as a bounded work package for a dedicated Codex agent.
Agents should:
- read the core architecture docs first
- only modify files within their boundary unless explicitly instructed
- emit tests and fixtures for their changes
- avoid redesigning adjacent modules without an explicit contract review

## Agent 1 — Platform/Substrate Agent
### Mission
Set up the Supabase-backed product substrate and shared backend scaffolding.

### Owns
- Supabase SQL schema
- migrations
- environment/config management
- storage abstraction
- auth / role integration points
- shared service clients

### Deliverables
- schema applied cleanly
- migration strategy
- dev/staging env docs
- typed config layer

### Do not do
- resolver logic
- parser logic
- passport projection logic

---

## Agent 2 — Resolver Agent
### Mission
Own the address-to-building identity capability.

### Owns
- address normalization
- query-variant generation
- In-ADS adapter
- candidate grouping by EHR code
- corner-address alias support
- resolution confidence logic

### Deliverables
- deterministic resolver service
- clear ambiguous/unresolved behavior
- stored raw resolver responses
- resolver regression fixtures from Tallinn test cases

### Acceptance criteria
- no silent weak auto-selection
- same EHR code across multiple variants boosts confidence
- corner buildings preserve address aliases

---

## Agent 3 — Ingestion Agent
### Mission
Own source document retrieval and storage.

### Owns
- EHR PDF fetch adapter
- source metadata persistence
- checksum generation
- SSL fallback policy
- object storage integration

### Deliverables
- fetch service
- fetch tests
- source document persistence
- retry behavior

### Acceptance criteria
- source document is stored with metadata
- failures are reproducible and diagnosable
- ingestion is idempotent for same source version

---

## Agent 4 — Parser Agent
### Mission
Interpret EHR PDFs into canonical observations.

### Owns
- PDF text extraction
- deterministic parser
- section splitters
- field extraction
- evidence/page mapping
- parser fixtures

### Deliverables
- parser module
- test PDFs / text fixtures
- observation generation
- parser versioning

### Acceptance criteria
- key sections parsed:
  - identity
  - building profile
  - structural systems
  - technical systems
  - geometry
  - building parts
- every observation carries provenance

---

## Agent 5 — Relevance/Projection Agent
### Mission
Turn observations into a product-grade passport.

### Owns
- relevance classification
- projection rules
- schema completeness scoring
- confidence rollups
- draft payload generation

### Deliverables
- relevance engine
- passport draft engine
- quality scoring
- JSON export schema

### Acceptance criteria
- passport is not a raw source dump
- only core/supporting observations reach the draft
- listing candidates remain separate

---

## Agent 6 — Review/Publication Agent
### Mission
Own the hybrid human-in-the-loop layer.

### Owns
- manual edits
- confirmations
- condition annotations
- photo evidence registration
- re-projection after review
- publication/versioning

### Deliverables
- review endpoints
- publication flow
- versioned passport persistence
- audit trail

### Acceptance criteria
- every manual change is recorded
- every publication is immutable
- reviewer-added evidence can be tied to passport fields/parts

---

## Agent 7 — API/Contract Agent
### Mission
Own the FastAPI service surface and Pydantic contracts.

### Owns
- route definitions
- request/response models
- OpenAPI coherence
- error model consistency

### Deliverables
- route handlers
- schema models
- API docs/tests
- status code conventions

### Acceptance criteria
- routes map to business operations
- status surfaces are consistent
- raw source quirks are hidden behind API contracts

---

## Agent 8 — Product Integration Agent
### Mission
Prepare the passport outputs for downstream product usage without building the whole marketplace.

### Owns
- listing candidate derivation design
- export payloads
- reporting-ready projections
- admin workflow glue

### Deliverables
- listing candidate model
- derivation stubs
- integration docs

### Acceptance criteria
- no marketplace coupling in core passport modules
- clear interfaces from passport to future marketplace

## Coordination rules

### Rule A
Agents cannot redefine the canonical passport schema independently.

### Rule B
Any change to observation namespaces/keys requires review against `03_PASSPORT_DOMAIN_MODEL_AND_CANONICAL_SCHEMA.md`.

### Rule C
Any new source-specific field must be mapped through the Estonia adapter and relevance engine.

### Rule D
All agents should emit tests or fixtures that make later Codex iterations safer.

## Recommended execution order

1. Agent 1
2. Agent 2
3. Agent 3
4. Agent 4
5. Agent 5
6. Agent 7
7. Agent 6
8. Agent 8
