# 03. Passport Domain Model and Canonical Schema

## Core principle

Never map raw source data directly into the final passport as product truth.

Always go through:

1. raw source artifact
2. canonical observations
3. relevance classification
4. passport projection

## Core entities

### Building
Represents the canonical building identity.

Suggested fields:
- building_id
- country_code
- primary_ehr_code
- normalized_address
- address_aliases
- municipality
- county
- source_identity_confidence
- created_at
- updated_at

### SourceDocument
Represents a raw source artifact.

Suggested fields:
- source_document_id
- building_id
- source_type
- source_uri
- mime_type
- checksum
- fetched_at
- parser_status
- storage_key

### ExtractionRun
Represents one interpretation pass over a source document.

Suggested fields:
- extraction_run_id
- source_document_id
- parser_name
- parser_version
- status
- started_at
- completed_at
- error_summary

### Observation
Represents one canonical fact with provenance.

Suggested fields:
- observation_id
- building_id
- namespace
- key
- value_json
- unit
- section
- relevance_class
- confidence_score
- confidence_label
- source_document_id
- extraction_run_id
- evidence_text
- page_number
- source_locator
- created_at

### PassportDraft
Represents the current assembled passport.

Suggested fields:
- passport_draft_id
- building_id
- schema_version
- status
- payload_json
- schema_completeness_score
- confidence_score
- generated_at

### PassportVersion
Immutable published version.

Suggested fields:
- passport_version_id
- passport_draft_id
- version_number
- payload_json
- pdf_storage_key
- published_at
- published_by

### ManualEdit
Represents a human override or confirmation.

Suggested fields:
- manual_edit_id
- building_id
- target_field_path
- old_value_json
- new_value_json
- edit_type
- reason
- actor
- created_at

## Canonical observation namespaces

### identity
Examples:
- identity.ehr_code
- identity.normalized_address
- identity.address_aliases
- identity.country

### building_profile
Examples:
- building_profile.building_type
- building_profile.building_status
- building_profile.building_name
- building_profile.use_categories
- building_profile.floors.above_ground
- building_profile.floors.below_ground
- building_profile.footprint_area_m2
- building_profile.heated_area_m2
- building_profile.net_area_m2
- building_profile.public_use_area_m2
- building_profile.technical_area_m2
- building_profile.height_m
- building_profile.length_m
- building_profile.width_m
- building_profile.depth_m
- building_profile.volume_m3

### structural_systems
Examples:
- structural_systems.foundation_type
- structural_systems.load_bearing_material
- structural_systems.wall_type
- structural_systems.facade_finish_material
- structural_systems.floor_structure_material
- structural_systems.roof_structure_material
- structural_systems.roof_covering_material

### technical_systems
Examples:
- technical_systems.electricity
- technical_systems.water
- technical_systems.sewer
- technical_systems.heat_source
- technical_systems.gas
- technical_systems.ventilation
- technical_systems.lift_count

### location
Examples:
- location.geometry_method
- location.shape_type
- location.coordinates

### building_parts
Examples:
- building_parts
- building_parts[].part_identifier
- building_parts[].part_type
- building_parts[].part_name
- building_parts[].part_use
- building_parts[].part_area_m2

## Relevance classes

Every observation should get one relevance class:

### passport_core
Required or strongly useful for the passport MVP.

### passport_supporting
Useful context but not always required.

### listing_candidate
Not core to the passport draft, but potentially useful later for marketplace derivation.

### low_signal
Present in the source but currently low-value.

### excluded
Not shown in the passport MVP.

## Passport MVP schema

### identity
- ehr_code
- normalized_address
- address_aliases
- country
- input_address

### building_profile
- building_type
- building_status
- building_name
- use_categories
- floors
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

### structural_systems
- foundation_type
- load_bearing_material
- wall_type
- facade_finish_material
- floor_structure_material
- roof_structure_material
- roof_covering_material

### technical_systems
- electricity
- water
- sewer
- heat_source
- gas
- ventilation
- lift_count

### location
- geometry_method
- shape_type
- coordinates

### building_parts
- part identifier
- part type
- part name
- part use
- part area

### quality
- schema_completeness_score
- confidence_score
- provenance_by_section
- missing_fields

### meta
- schema_version
- generated_at_utc
- source_strategy

## Critical semantic rules

### Rule 1
Do not call `footprint_area_m2` by the name `gross_area_m2`.

### Rule 2
If the resolver yields multiple official addresses for one EHR code, store them as `address_aliases`, not as competing buildings.

### Rule 3
Do not invent material quantities unless they are explicitly sourced or clearly marked as derived estimates.

### Rule 4
A parser output is not a final passport. It is an input to passport projection.

### Rule 5
Confidence belongs to observations first, then rolls up into passport sections.
