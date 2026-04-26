# BUILDLoop — Root Agent Instructions

This is a multi-track project. The track you're working on determines
which directory to operate from and which instructions to read.

## Frontend track
- Working directory: /web/
- Stack: Next.js 14 (App Router), TypeScript strict, Tailwind
- Read: /web/AGENTS.md
- Do not modify anything outside /web/ from a frontend session

## Backend track
- Working directory: /app/
- Stack: FastAPI, SQLAlchemy, Alembic, Supabase
- Read: /app/AGENTS.md (when it exists)
- Architecture pack at repo root, files 00 through 12, must be
  read before any non-trivial backend change
- The two scripts buildloop_passport_from_address.py and
  buildloop_passport_from_address_colab_v3.py contain the working
  extraction logic. They are reference, not source. Carving them
  into modules per doc 04 is a deliberate, scoped task — do not
  touch them opportunistically.

## Cross-cutting rules
- Architecture docs at repo root (00_*.md through 12_*.md) are
  the source of truth for system design. UI labels, schema keys,
  API contracts, and module boundaries all derive from them.
- The canonical schema (doc 03) is binding. UI never displays raw
  schema keys. Backend never invents fields outside the namespaces
  defined there.
- Never edit /skills/ — those are skill packs that document
  workflows, not code to modify.