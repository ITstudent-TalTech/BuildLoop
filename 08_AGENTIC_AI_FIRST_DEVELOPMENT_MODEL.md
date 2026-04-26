# 08. Agentic AI-First Development Model

## Objective

BUILDLoop is to be developed using an AI-first, strongly agentic workflow.
That only works if the agents have:
- clear system boundaries
- explicit ownership
- stable interfaces
- a shared source of truth

This document defines the operating model.

## Foundational rule

Agents are not allowed to infer the architecture from scattered code alone.

They must follow, in order:
1. validated workflow documents
2. canonical schema documents
3. stack decision document
4. task cards / backlog
5. then the existing codebase

## Core agent set

### Agent 1 — Product Architect
Owns:
- roadmap translation into system boundaries
- business capability decomposition
- relevance policy decisions
- architecture review
- acceptance of major schema changes

Outputs:
- architecture docs
- decision records
- scope clarifications

### Agent 2 — Platform Engineer
Owns:
- Supabase setup
- migrations
- auth / org / role model
- RLS policies
- storage buckets
- local/dev/prod environment setup

Outputs:
- schema migrations
- platform config
- deployment config

### Agent 3 — Workflow/API Engineer
Owns:
- FastAPI project structure
- endpoint contracts
- workflow orchestration
- job status models
- API tests

Outputs:
- FastAPI routes
- request/response models
- job orchestration logic

### Agent 4 — Resolver Engineer
Owns:
- address normalization
- multi-variant query generation
- public address-source adapter
- EHR code candidate grouping
- confidence scoring
- alias handling for corner buildings

Outputs:
- resolver service
- candidate/ranking tests
- resolver fixtures

### Agent 5 — Source Adapter Engineer
Owns:
- EHR PDF fetch adapter
- fetch retries / SSL fallback
- raw source metadata
- source versioning
- future additional source adapters

Outputs:
- source ingestion services
- fetch jobs
- source storage integrations

### Agent 6 — Parser Engineer
Owns:
- PDF text extraction
- deterministic parser
- section parsing
- observation generation
- parser regression fixtures

Outputs:
- parser modules
- parser tests
- observation builders

### Agent 7 — Relevance and Projection Engineer
Owns:
- relevance classification
- passport projection
- quality scoring
- listing_candidate derivation scaffolding

Outputs:
- relevance engine
- draft builder
- quality metrics

### Agent 8 — Review & Publication Engineer
Owns:
- manual edit model
- review workflow
- version publication
- export rendering
- audit trail

Outputs:
- review endpoints
- versioning logic
- PDF export

### Agent 9 — Frontend/Product Experience Engineer
Owns:
- intake UI
- candidate selection UI
- passport draft UI
- review/editor UI
- dashboard views

Outputs:
- web flows
- design tokens/components
- frontend tests

### Agent 10 — QA / Evaluation Engineer
Owns:
- workflow fixtures
- parser goldens
- resolver evaluation set
- regression suite
- output validation metrics

Outputs:
- test matrices
- evaluation datasets
- regression reports

## Shared artifacts all agents must use

### Required workflow artifacts
- `02_VALIDATED_WORKFLOW_AND_SYSTEM_BOUNDARIES.md`
- `03_PASSPORT_DOMAIN_MODEL_AND_CANONICAL_SCHEMA.md`
- `05_DATA_RELEVANCE_POLICY.md`
- `07_HYBRID_STACK_DECISION_AND_DEPLOYMENT_ARCHITECTURE.md`

### Required code artifact
- `scripts/buildloop_passport_from_address_colab_v3.py`

This script is not just a demo.
It is the current executable reference for the validated address -> resolver -> EHR code -> PDF -> passport flow.

## Agent task routing

### When the task is about:
- database or auth -> Platform Engineer
- endpoint or orchestration -> Workflow/API Engineer
- address matching -> Resolver Engineer
- EHR fetch logic -> Source Adapter Engineer
- PDF extraction or parsing -> Parser Engineer
- what belongs in the passport -> Relevance and Projection Engineer
- review/version/export -> Review & Publication Engineer
- UI workflow -> Frontend/Product Experience Engineer
- test datasets and quality -> QA / Evaluation Engineer

## Rules for autonomous work

### Rule 1 — No hidden architecture changes
Any change to:
- schema boundaries
- stack boundaries
- module boundaries
- passport schema
must be surfaced as an architecture decision, not silently committed.

### Rule 2 — No raw-source leakage
Agents must not build product logic directly around raw EHR field names outside the adapter/parser layer.

### Rule 3 — No silent resolver guessing
Agents must not make low-confidence auto-resolution decisions.

### Rule 4 — No field dumping
Agents must not dump all extracted source fields into user-facing passport views.

### Rule 5 — No marketplace-first distortion
Agents must not redesign the passport engine to optimize prematurely for marketplace behavior.

### Rule 6 — Every parser change needs fixture validation
Parser changes must be checked against stored sample PDFs and expected observations.

## Recommended Codex execution loop

For each work item:

1. Read the architecture and schema docs
2. Read the relevant existing module
3. Generate a small design note
4. Implement
5. Run/tests or produce a validation note
6. Summarize:
   - what changed
   - what assumptions were made
   - what remains uncertain

## Work packaging for agentic execution

### Good work items
- small vertical slice
- one owner
- clear inputs/outputs
- explicit acceptance criteria

### Bad work items
- “build the whole backend”
- “improve everything”
- “make it production-ready”

## Definition of success for AI-first development

The AI-first model succeeds when:
- architecture remains coherent across many generated changes
- agents do not drift into conflicting mental models
- the validated workflow remains runnable at all times
- generated code is traceable back to the documented product model
