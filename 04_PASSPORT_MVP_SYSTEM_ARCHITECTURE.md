# 04. Passport MVP System Architecture

## Architecture style

Use a **modular monolith** for the MVP.

Reasons:
- faster iteration
- easier refactoring
- lower operational overhead
- simpler data migrations
- simpler coordination with Codex

The modular boundaries matter more than process boundaries.

## Suggested stack

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy / SQLModel
- PostgreSQL
- Redis
- background jobs (RQ / Dramatiq / Celery)

### Storage
- PostgreSQL for core data and observations
- S3/MinIO for raw PDFs, exported PDFs, uploaded photos

### Rendering / parsing
- pypdf or pdftotext fallback for extraction
- HTML -> PDF renderer for BUILDLoop-branded passport output

## Module boundaries

### 1. intake
Responsibilities:
- accept raw address / project creation request
- validate request shape
- persist intake request

### 2. resolver
Responsibilities:
- address normalization
- multiple query variant generation
- public address lookup
- candidate grouping by EHR code
- confidence scoring
- alias extraction
- resolver result persistence

### 3. source_ingestion
Responsibilities:
- fetch EHR PDF by EHR code
- persist raw source and fetch metadata
- version source documents
- retry and SSL fallback behavior

### 4. source_parsing
Responsibilities:
- extract text from source document
- parse sections
- create canonical observations
- attach evidence and page references

### 5. relevance_engine
Responsibilities:
- classify observations by relevance
- filter source noise
- flag low-signal sections
- prepare listing_candidate observations for later

### 6. passport_engine
Responsibilities:
- build current draft from passport_core + supporting observations
- compute quality metrics
- generate JSON and PDF views
- version published passports

### 7. review
Responsibilities:
- manual overrides
- confirmations
- image uploads
- notes
- re-run projection after edits

### 8. exporter
Responsibilities:
- PDF export
- JSON export
- regulator/export payloads later

## Execution flow

### API request
`POST /v1/passports/from-address`

### Internal flow
1. intake request persisted
2. resolver runs
3. if ambiguous -> return candidates
4. if resolved -> source ingestion runs
5. source parsing produces observations
6. relevance engine filters observations
7. passport engine produces draft
8. review flow optionally edits/approves
9. export layer renders final PDF

## Data flow layers

### Layer A — raw source
Immutable source-of-trace.
Examples:
- source PDF
- resolver raw responses
- fetch metadata

### Layer B — observations
Canonical atomic facts.
Examples:
- building status
- load-bearing material
- building part area
- geometry coordinates

### Layer C — product views
Projections built from observations.
Examples:
- passport draft
- published passport
- future listing candidates

## Feature flags

Use feature flags from the beginning:

- `enable_address_resolution_v2`
- `enable_resolver_multi_variant`
- `enable_corner_address_alias_merge`
- `enable_pdf_ssl_fallback`
- `enable_listing_candidate_classification`
- `enable_photo_enrichment`
- `enable_condition_annotation`

## Quality model

Split quality into at least two top-level scores:

### Schema completeness
How much of the defined passport schema is populated.

### Evidence confidence
How trustworthy the populated fields are.

Later add:
### Reuse readiness completeness
How much of the data needed for a marketplace-grade listing is available.

## Error handling model

### Resolution errors
Return:
- unresolved
- ambiguous
- resolved

Do not silently auto-pick weak matches.

### Source errors
Return:
- fetch_failed
- fetch_blocked
- source_unavailable

### Parsing errors
Return:
- parse_failed
- parse_partial
- parse_ok

## Why this architecture fits the validated workflow

Because it matches the observed reality:

- address resolution is a separate capability
- EHR PDF is the canonical validated source
- PDF fields need interpretation and filtering
- not every source field belongs in the product output
- marketplace concerns should not distort the passport engine
