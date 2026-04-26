---
name: passport-ui-mvp
description: Build and iterate a simple visual passport creation UI slice (identity/profile/review-ready fields) with minimal components, clear boundaries, and fast local preview. Use when asked to create or adjust the first visual workflow for passport creation.
---

# Passport UI MVP Skill

Use this skill when the user asks for visual/product UI work around **passport creation** in MVP scope.

## Scope guardrails

- Keep to MVP passport flow only (no marketplace features).
- Prefer 1-page flow with small reusable components.
- Optimize for reviewability and evidence visibility, not visual complexity.

## Default workflow

1. Build/update a `PassportCreate` page section-by-section:
   - identity
   - building profile
   - structural/technical summary
   - quality/review indicators
2. Use shared field components (`TextField`, `SelectField`, `EvidenceBadge`) instead of one-off controls.
3. Keep all form state in a single typed view-model.
4. Wire save actions to API contracts incrementally (start with mocked adapters if endpoints are not ready).
5. Add empty/loading/error states before styling polish.

## Done criteria

- User can input/edit MVP fields.
- Validation errors are visible per field.
- Review state is visible at section level.
- UI can be extended without rewrites.

## If implementation details are needed

Read: `references/ui-contract.md`.
