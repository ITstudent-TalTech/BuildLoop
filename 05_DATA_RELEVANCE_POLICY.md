# 05. Data Relevance Policy

## Why this document exists

The simplified workflow now produces enough data that the real problem is no longer "can we extract fields?" but:

**Which extracted fields belong in the passport MVP, which belong later, and which should be ignored?**

The system must not equate "available in EHR PDF" with "product-relevant now."

## Relevance framework

Every extracted field must be classified into one of these buckets.

### Bucket A — Passport Core
Must appear in the MVP passport if present.

Examples:
- EHR code
- normalized address
- address aliases
- building type
- building status
- use categories
- floors
- footprint
- heated/net area
- height
- volume
- structural system labels
- technical system labels
- building parts
- geometry
- provenance metadata

### Bucket B — Passport Supporting
Useful context, but optional in the user-facing MVP draft.

Examples:
- building name
- public-use area
- technical area
- length / width / depth
- object type details from resolver
- primary-candidate marker from resolver

### Bucket C — Listing Candidate
Not needed in the first passport view, but useful later when turning passports into supply listings.

Examples:
- building parts with areas
- categories that can be grouped into sellable lots
- address aliases useful for pickup / access context
- future condition annotations
- future photo-derived candidate material items

### Bucket D — Low Signal
Present in the source, but not useful enough right now.

Examples:
- empty technical placeholders
- repeated labels with no value
- ambiguous room-level counters with no reuse implication
- registry noise without product meaning

### Bucket E — Excluded
Should not appear in the MVP passport unless the use case changes.

Examples:
- raw resolver payloads
- fetch internals
- UI/debug-only values
- temporary parser scaffolding

## Practical field policy

### Identity
Keep:
- ehr_code
- normalized_address
- address_aliases
- country
- input_address

### Building profile
Keep:
- building_type
- building_status
- use_categories
- floors
- footprint_area_m2
- heated_area_m2
- net_area_m2
- height_m
- volume_m3

Optional supporting:
- building_name
- public_use_area_m2
- technical_area_m2
- length_m
- width_m
- depth_m

### Structural systems
Keep all non-empty fields.
These are high-value for the passport MVP because they support later material-family inference.

### Technical systems
Keep all non-empty fields.
They matter for reuse context, disassembly context, and building characterization.

### Building parts
Keep.
Even if the marketplace is later, building parts are already valuable for understanding usable sections and future listing granularity.

### Geometry
Keep.
Useful for identity, location, future logistics, and map views.

## Specific examples from the current EHR PDF workflow

### Highly relevant
- `Ehitise aadress`
- `Ehitisregistri kood`
- `Ehitise liik`
- `Ehitise seisund`
- `Kasutamise otstarve`
- `Ehitisealune pind`
- `Köetav pind`
- `Suletud netopind`
- `Kõrgus`
- `Maht`
- structural materials
- technical systems
- building parts
- coordinates

### Relevant but secondary
- `Ehitise nimetus`
- `Üldkasutatav pind`
- `Tehnopind`
- length / width / depth

### Low signal or excluded for MVP
- empty cooling system line items
- placeholder fields with no value
- raw administrative/debug source details

## Relevance governance

This policy should be implemented in code, not only in documents.

Recommended implementation:
- each observation gets a `relevance_class`
- the relevance engine maps observations into:
  - passport_core
  - passport_supporting
  - listing_candidate
  - low_signal
  - excluded

The passport engine should only project:
- passport_core
- selected passport_supporting

## Design rule

The relevance policy is where product strategy enters the data pipeline.

Without it, the passport becomes a raw registry dump.
With it, the passport becomes a product.
