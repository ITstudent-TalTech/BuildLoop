# 02. Validated Workflow and System Boundaries

## Validated workflow

The workflow that has been validated enough to treat as real is:

**address input -> address resolver -> EHR code -> EHR PDF fetch -> PDF text extraction -> canonical observations -> passport draft**

Important: the resolver is still probabilistic; the rest of the flow becomes deterministic once the EHR code is known.

## System boundary definition

### Outside the passport engine
These concerns should not leak into the core passport model:

- Google Maps / autocomplete UX
- raw In-ADS quirks
- raw EHR PDF structure
- marketplace listing UI
- logistics
- payment processing
- franchise / country-specific operational procedures

### Inside the passport engine
These are core concerns:

- building identity
- source artifact ingestion
- canonical observations
- relevance classification
- passport projection
- quality scoring
- review and versioning

## Workflow stages

### Stage 1 — Intake
Input:
- raw user address
- optional project metadata
- optional direct EHR code (debug/admin only)

Output:
- normalized intake record

### Stage 2 — Resolution
Input:
- normalized intake record

Output:
- resolved EHR code
- candidate set if ambiguous
- alias addresses if available
- confidence and match reasoning

### Stage 3 — Source ingestion
Input:
- EHR code

Output:
- raw source artifact(s)
- fetch metadata
- source version / timestamp

### Stage 4 — Source interpretation
Input:
- raw source artifact(s)

Output:
- canonical observations with evidence and provenance

### Stage 5 — Relevance filtering
Input:
- canonical observations

Output:
- passport-relevant observations
- useful-but-non-passport observations
- excluded/noise observations

### Stage 6 — Passport projection
Input:
- passport-relevant observations

Output:
- current passport draft
- quality / confidence scores
- missing sections
- PDF render

### Stage 7 — Review and publication
Input:
- draft passport
- human edits / confirmations
- optional photos and condition data

Output:
- published passport version
- audit trail
- export JSON / PDF

## Resolver boundary

The resolver must answer only one question:

**Which building does this user mean?**

It should not:
- infer materials
- generate passport fields
- fetch marketplace data
- generate PDFs

## Source adapter boundary

The EHR adapter must answer only two questions:

- How do I fetch the source artifact?
- How do I interpret it into canonical observations?

It should not:
- decide product relevance
- decide listing relevance
- apply business pricing logic

## Relevance boundary

This is the key new boundary that did not exist clearly in the older roadmap.

The system needs a dedicated decision layer between:
- "field exists in source"
and
- "field belongs in passport MVP"

Examples of source data that exist but may not be passport-core:
- cultural value flags depending on use case
- legal metadata not useful for reuse decisions
- fine-grained room stats with no current reuse value
- empty or low-signal technical placeholders

The MVP should not dump all available source data into the passport just because it can.

## Why this matters

If the core engine is built around:
- raw address search,
- raw EHR fields,
- and direct PDF-to-passport mapping

then every source change and every future country integration will become expensive.

If instead the engine is built around:
- identity resolution
- source adapters
- canonical observations
- relevance filtering
- passport projection

then:
- Estonia becomes one adapter, not the whole product
- marketplace becomes one consumer, not the whole MVP
- Europe expansion becomes realistic
