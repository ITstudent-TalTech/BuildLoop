# 00. Executive Reframe

## Why the roadmap must be updated

The original roadmap is directionally correct, but it assumed a cleaner and richer data path than what has actually been validated. The product vision remains sound:

- BUILDLoop automates digital material passports
- BUILDLoop operates a marketplace for reuse-ready materials
- Estonia is the wedge market because of EHR and public digital infrastructure
- Europe is the long-term expansion target

However, the implementation reality is now clearer:

1. The stable public source currently validated is **EHR PDF by EHR code**
2. Address resolution exists as a separate problem and cannot be treated as solved plumbing
3. The raw source contains many fields, but not all are relevant to the passport MVP
4. The MVP needs a **data relevance layer** and a **canonical observation model**
5. The marketplace should consume passport outputs later; it should not drive the first architecture

## Updated product thesis

### Previous thesis
Passport first, then marketplace lite.

### Updated thesis
**Passport engine first, marketplace-ready data second.**

That means the MVP should not be framed as:
- address search
- fetch some EHR
- generate a PDF
- list items

It should be framed as:

1. identify the building
2. ingest source documents
3. convert source documents into canonical observations
4. filter for passport-relevant data
5. generate a reviewable passport draft
6. enrich manually where needed
7. publish a versioned passport
8. only then derive marketplace-ready outputs

## What the MVP really is

The MVP is a **passport operating system** for existing buildings.

That operating system needs four core capabilities:

- **resolution**: convert user-facing address input into building identity
- **ingestion**: fetch and store the stable source artifacts
- **interpretation**: transform source artifacts into canonical observations
- **projection**: build passport views, PDFs, and later marketplace inventory views

## What is proven today

### Proven enough to build around
- EHR code -> PDF fetch
- PDF -> deterministic extraction of many building fields
- building parts extraction
- geometry extraction
- structural / technical fields extraction

### Not yet robust enough to be considered solved
- address -> EHR resolution
- automatic material quantity estimation
- condition grading
- removability / reuse-readiness inference
- marketplace-grade itemization

## Strategic decision

The engineering program should now be organized around:

**Phase A — Passport foundation**
- source adapters
- canonical schema
- deterministic parser
- passport review workflow

**Phase B — Marketplace readiness**
- translate passport sections into reusable listing candidates
- add condition, photos, and salvage signals
- prepare listing derivation rules

**Phase C — Marketplace execution**
- actual buyer/seller interactions
- listing lifecycle
- logistics and transactions

That is the architecture that matches both the long-term vision and the current data reality.
