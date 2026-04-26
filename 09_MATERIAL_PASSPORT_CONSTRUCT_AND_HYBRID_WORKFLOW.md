# 09. Material Passport Construct and Hybrid Workflow

## Why this document exists

The roadmap described a hybrid flow:
- details are looked up,
- data is extracted,
- a professional user confirms and possibly edits,
- additional evidence can be added,
- a material passport is generated.

This document defines exactly what that means in product and engineering terms.

## Definition

A BUILDLoop material passport is a **versioned, evidence-backed digital representation of a building or project that captures reuse-relevant building identity, systems, parts, and material signals, together with confidence, provenance, and review status**.

It is not:
- a full BIM model
- a demolition report
- a raw EHR export
- a final marketplace inventory
- a legal guarantee of reuse suitability

It is:
- a structured project artifact
- a decision support layer
- a reviewable basis for deconstruction planning
- a future input to listing generation and reporting

## Passport object model

### 1. Identity section
Purpose:
- identify exactly which building/project is being documented

Fields:
- passport_id
- building_id
- project_id
- country_code
- primary_ehr_code
- normalized_address
- address_aliases
- source_identity_confidence
- generated_at
- passport_version
- status

### 2. Building profile section
Purpose:
- characterize the building at a level useful for downstream reuse analysis

Fields:
- building_type
- building_status
- building_name
- use_categories
- floors_above_ground
- floors_below_ground
- footprint_area_m2
- heated_area_m2
- net_area_m2
- public_use_area_m2
- technical_area_m2
- height_m
- length_m
- width_m
- depth_m
- volume_m3

### 3. Structural systems section
Purpose:
- capture reuse-relevant structure and envelope signals

Fields:
- foundation_type
- load_bearing_material
- wall_type
- facade_finish_material
- floor_structure_material
- roof_structure_material
- roof_covering_material

### 4. Technical systems section
Purpose:
- capture services and systems that affect reuse, deconstruction, and building characterization

Fields:
- electricity
- water
- sewer
- heat_source
- gas
- ventilation
- lift_count

### 5. Spatial / geometry section
Purpose:
- locate the building accurately and support future mapping/logistics

Fields:
- geometry_method
- shape_type
- coordinates

### 6. Building parts section
Purpose:
- break the building into meaningful parts or occupancies that can later support listing derivation

Fields:
- part_identifier
- part_type
- part_name
- part_use
- part_area_m2
- shape_no

### 7. Evidence and provenance section
Purpose:
- show why the passport says what it says

Fields:
- source_documents
- extraction_runs
- observations
- evidence_text
- page_number
- parser_version
- confidence scores
- resolver match rationale

### 8. Quality section
Purpose:
- communicate how usable the passport is right now

Fields:
- schema_completeness_score
- confidence_score
- missing_fields
- unresolved_sections
- review_status
- publication_status

### 9. Review/enrichment section
Purpose:
- record what the professional user confirmed, edited, or added

Fields:
- manual confirmations
- manual edits
- uploaded photos
- notes
- condition annotations
- salvage annotations
- reviewer identity
- review timestamp

## Hybrid workflow definition

This is the full BUILDLoop passport workflow for the MVP and near-term product.

### Stage A — System-sourced baseline
System does:
1. accept address
2. resolve building identity
3. fetch stable public source(s)
4. parse source(s)
5. create observations
6. classify relevance
7. assemble draft passport

At this stage the system produces a **baseline draft**, not a final truth.

### Stage B — Professional review and enrichment
Professional user does:
1. confirm the building is correct
2. confirm or edit key profile fields
3. confirm or edit structure/system fields
4. attach photos
5. annotate condition
6. annotate salvage suitability
7. add missing high-value elements not present in source
8. approve for publication or keep in draft

This is where the product becomes trustworthy.

### Stage C — Published passport
System does:
1. freeze a version
2. render export PDF
3. store structured JSON
4. make it available for listing derivation and reporting

## Review statuses

Recommended statuses:
- `draft_system_generated`
- `draft_needs_review`
- `review_in_progress`
- `review_completed`
- `published`
- `superseded`

## Confidence model

### Observation-level confidence
Each extracted fact gets:
- numeric confidence
- label:
  - `confirmed_from_source`
  - `derived`
  - `confirmed_by_reviewer`

### Section-level confidence
Each passport section gets a rollup.

### Passport-level confidence
Overall rollup, but never at the expense of section-level visibility.

## Condition / salvage extensions

These are not mandatory for the very first system-generated draft, but they are part of the hybrid workflow and should be modeled now.

### Condition fields
- good
- fair
- poor
- salvage_only
- unknown

### Salvage / reuse suitability
- reusable_as_is
- reusable_with_refurbishment
- recyclable_only
- unsuitable
- unknown

### Evidence types
- source-only
- source + reviewer confirmation
- reviewer-added
- photo-supported

## What should not be in the passport MVP by default

Do not include by default:
- raw API/debug payloads
- every source field just because it exists
- speculative quantities without clear labeling
- marketplace-specific pricing
- transaction state
- buyer communications

## Downstream products of the passport

The passport should later feed:
- listing candidate derivation
- municipal/regulatory reporting
- surveyor verification products
- analytics dashboards
- cross-country adapters

## Product rule

The hybrid workflow is not optional polish.
It is the trust mechanism of the product.
