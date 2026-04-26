# 11. FastAPI API Contracts

## API philosophy

FastAPI is the domain engine and orchestration layer.
It should expose business operations, not raw registry quirks.

The API should center on:
- intake
- resolution
- source ingestion
- passport generation
- review
- publication
- export

## Base path

`/v1`

## 1. Intake and resolution

### POST `/v1/intakes`
Create a new intake request.

Request:
```json
{
  "address_input": "Lai 1, Nunne tn 4, 10133 Tallinn, Estonia",
  "project_title": "Pilot project"
}
```

Response:
```json
{
  "intake_request_id": "uuid",
  "project_id": "uuid",
  "status": "received"
}
```

### POST `/v1/resolutions`
Run address resolution.

Request:
```json
{
  "intake_request_id": "uuid"
}
```

Response (resolved):
```json
{
  "status": "resolved",
  "resolution_run_id": "uuid",
  "ehr_code": "101035685",
  "normalized_address": "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4",
  "address_aliases": ["Lai tn 1", "Nunne tn 4"],
  "confidence_score": 0.91
}
```

Response (ambiguous):
```json
{
  "status": "ambiguous",
  "resolution_run_id": "uuid",
  "candidates": [
    {
      "ehr_code": "101035685",
      "normalized_address": "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4",
      "confidence_score": 0.72
    }
  ]
}
```

### POST `/v1/resolutions/{resolution_run_id}/select`
User or operator selects a candidate manually.

Request:
```json
{
  "ehr_code": "101035685"
}
```

Response:
```json
{
  "status": "resolved",
  "ehr_code": "101035685"
}
```

## 2. Source ingestion

### POST `/v1/projects/{project_id}/sources/fetch`
Fetch source documents for the resolved building.

Request:
```json
{
  "ehr_code": "101035685"
}
```

Response:
```json
{
  "status": "ok",
  "source_document_id": "uuid",
  "source_type": "ehr_pdf",
  "fetch_status": "ok"
}
```

### GET `/v1/projects/{project_id}/sources`
List source documents.

## 3. Parsing and observations

### POST `/v1/source-documents/{source_document_id}/parse`
Run parser over a source document.

Response:
```json
{
  "status": "ok",
  "extraction_run_id": "uuid",
  "observation_count": 87
}
```

### GET `/v1/projects/{project_id}/observations`
List observations, optionally filtered by:
- section
- relevance_class
- namespace
- key

## 4. Passport draft generation

### POST `/v1/projects/{project_id}/passport-drafts`
Generate or regenerate the current passport draft.

Response:
```json
{
  "status": "ok",
  "passport_draft_id": "uuid",
  "schema_version": "buildloop.passport.mvp.v1",
  "schema_completeness_score": 82.5,
  "confidence_score": 86.0
}
```

### GET `/v1/projects/{project_id}/passport-draft`
Return the current draft payload.

### GET `/v1/passport-drafts/{passport_draft_id}`
Return one draft by ID.

## 5. Review and enrichment

### PATCH `/v1/passport-drafts/{passport_draft_id}/fields`
Manual edit of a field.

Request:
```json
{
  "target_field_path": "structural_systems.load_bearing_material",
  "new_value": "monoliitne raudbetoon",
  "reason": "Confirmed from site documents"
}
```

### POST `/v1/passport-drafts/{passport_draft_id}/photos`
Upload or register photos.

### POST `/v1/passport-drafts/{passport_draft_id}/condition-annotations`
Add condition / salvage annotations.

Request:
```json
{
  "target_path": "building_parts[0]",
  "condition_label": "good",
  "salvage_label": "reusable_as_is",
  "note": "Confirmed by professional reviewer"
}
```

### POST `/v1/passport-drafts/{passport_draft_id}/reproject`
Rebuild draft after edits/annotations.

## 6. Publication and export

### POST `/v1/passport-drafts/{passport_draft_id}/publish`
Publish an immutable passport version.

Response:
```json
{
  "status": "published",
  "passport_version_id": "uuid",
  "version_number": 1
}
```

### GET `/v1/passport-versions/{passport_version_id}`
Return version JSON.

### GET `/v1/passport-versions/{passport_version_id}/pdf`
Return rendered PDF.

## 7. Listing candidate derivation (future-facing)

### POST `/v1/passport-drafts/{passport_draft_id}/listing-candidates`
Derive marketplace-ready listing candidates from the passport.

This should exist only after the passport path is stable.

## Contract rules

### Rule 1
API clients should not need to know raw EHR field names.

### Rule 2
Address resolution must return explicit statuses:
- resolved
- ambiguous
- unresolved

### Rule 3
Parser and passport generation should be rerunnable and idempotent.

### Rule 4
Publication creates an immutable version.

### Rule 5
Manual edits and annotations are first-class API operations, not ad hoc database writes.
