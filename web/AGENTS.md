# BUILDLoop — Agent Instructions

## What this project is
BUILDLoop is a passport-first platform for circular construction in
Estonia, expanding to the EU. It generates digital material passports
for buildings using public registry data (Estonian EHR) plus AI, then
provides a marketplace for reusable materials.

## Repo structure
- `/web/` — Next.js 14 (App Router) + Tailwind frontend (in progress)
- `/web/design-references/` — Exported HTML from Claude Design, read-only,
  use as visual specs only. Do not import into the build.
- `/web/BRAND.md` — Brand tokens (palette, tone, typography rules)
- `/app/` — FastAPI backend (minimal scaffold, expanding)
- `/00_*.md` through `/12_*.md` — Architecture pack. Read these before
  any non-trivial change. Especially:
  - `03_PASSPORT_DOMAIN_MODEL_AND_CANONICAL_SCHEMA.md` — the canonical
    schema. UI labels are plain language, never raw schema keys.
  - `11_FASTAPI_API_CONTRACTS.md` — API endpoints and shapes.
  - `12_CODEX_AGENT_TASK_CARDS.md` — agent boundaries (you).
- `buildloop_passport_from_address.py` and the colab v3 variant — the
  actual extraction logic that needs to be carved into the modular
  backend later. Don't touch these yet.

## Conventions
- TypeScript strict mode in `/web/`. No `any`. Pydantic models in `/app/`.
- Frontend: React Server Components by default; Client Components only
  where interactivity is needed.
- Styling: Tailwind utility classes. No CSS modules, no styled-components.
- Component primitives live in `/web/components/shared/`. Build these
  before assembling screens.
- Mock the FastAPI calls in `/web/lib/api/mocks.ts` until backend routes
  exist. Frontend must work end-to-end with mocks first.
- Never bind raw schema keys (e.g. `heated_area_m2`) to UI labels.

## Working agreement
- Stay within the directory you're assigned in a given task.
- Read the relevant architecture doc before non-trivial changes.
- Emit a short test or fixture with each component or route.
- If a design decision conflicts with a doc, flag it — don't silently override.

- Sessions may always update /PROGRESS.md (the cross-cutting progress 
  log at repo root). This is the only file outside /web/ that frontend 
  sessions are permitted to modify.