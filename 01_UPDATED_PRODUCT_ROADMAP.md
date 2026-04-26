# 01. Updated Product Roadmap

## Reference point

The old roadmap positioned the product as:
- Phase 1: Passport First, Marketplace Lite
- Phase 2: Full Marketplace & Monetisation
- Phase 3: European expansion

That high-level structure is still useful, but the actual execution plan should be updated based on validated workflow and current data quality.

## Updated roadmap

---

## Phase 0 — Data Reality & Source Validation
### 0–2 months

### Goal
Prove that BUILDLoop can reliably create a reviewable passport draft from public sources for real buildings in Estonia.

### Core deliverables
- address resolution service v1
- EHR PDF fetch adapter
- raw source storage
- deterministic PDF parser
- canonical observation model
- passport draft generator
- quality / provenance scoring
- manual review UI or admin workflow

### Success criteria
- at least 20 real buildings processed end-to-end
- at least 80% of runs produce a structurally valid passport draft
- manual review time under 10 minutes for a typical building
- parser precision judged acceptable on key fields:
  - identity
  - area/volume
  - structural system labels
  - technical system labels
  - building parts

### Main output
A passport draft JSON + PDF with provenance.

---

## Phase 1 — Passport MVP
### 2–6 months

### Goal
Ship a production-quality passport workflow that is useful even if marketplace functionality is minimal.

### Core features
- address input with candidate selection
- source fetch and versioned storage
- passport draft creation
- manual correction and confirmation
- photo upload and annotation
- condition and confidence fields
- publishable passport PDF
- audit trail and version history
- exportable JSON for later integrations

### Deliberately excluded
- payments
- messaging
- logistics booking
- escrow
- advanced inventory search

### Business outcome
Validate that demolition / renovation actors will create and review passports if the workflow is fast and useful.

### Success criteria
- 50+ passports created
- 10+ organizations using the flow
- repeat usage by early partners
- evidence that users trust the draft enough to correct and publish it

---

## Phase 2 — Marketplace-Ready Enrichment
### 6–12 months

### Goal
Transform passports from building-level documentation into listing-ready supply.

### Core features
- relevance classifier for listing candidates
- condition / salvage / reuse tags
- item families and listing derivation rules
- grouping of building parts into offer lots
- demand-side taxonomy for buyers
- inquiry workflow
- project-level listing pages generated from passport sections

### Why this is separate
A passport is not automatically a marketplace inventory.
The system must first decide:
- which fields are relevant to reuse
- which building parts are sellable
- what level of granularity is useful
- whether evidence is strong enough for listing

### Success criteria
- listing derivation works for multiple project types
- users can turn a passport into a marketplace-ready supply set with minimal extra effort
- inquiry-to-conversation conversion is measurable

---

## Phase 3 — Verified Passports & Marketplace Execution
### 12–24 months

### Goal
Add trust, transactions, and operational scale.

### Core features
- verified passports
- surveyor / engineer review workflows
- in-app inquiries and messaging
- pricing and transaction support
- logistics integrations
- buyer-side search and saved alerts
- regulatory reporting exports

### Success criteria
- paid verified passports
- recurring usage
- measurable GMV and conversion rates
- repeat activity from both supply and demand sides

---

## Phase 4 — Country Adapter Platform
### 18–36 months

### Goal
Generalize the passport engine beyond Estonia.

### Core features
- country-specific resolver adapters
- country-specific source adapters
- canonical schema shared across countries
- localized taxonomies
- white-label and franchise support
- cross-border analytics and reporting

### Critical rule
The platform should never depend on raw EHR field names outside the Estonia adapter.

## Roadmap summary

### Immediate truth
The MVP is not "marketplace lite".
The MVP is **passport infrastructure with marketplace potential**.

### Product principle
Everything that reaches the marketplace later must first pass through:
- source ingestion
- canonical observation mapping
- relevance filtering
- human review where required
