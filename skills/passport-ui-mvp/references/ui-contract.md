# UI Contract (MVP)

## Required sections

- Identity
- Building profile
- Structural systems (summary)
- Technical systems (summary)
- Quality indicators

## Component conventions

- Keep field wrappers consistent (label, hint, error, evidence).
- Do not bind raw source field names to UI labels.
- Show confidence/evidence without blocking edits.

## API mapping preference

- Use workflow/resource endpoints as canonical.
- Keep UI actions idempotent and retry-safe.
