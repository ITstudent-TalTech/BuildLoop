---
name: passport-ui-scale
description: Evolve the passport visual layer from MVP to scalable architecture by introducing design tokens, section modules, and stable extension points for future review/publication/listing-readiness features.
---

# Passport UI Scale Skill

Use this skill when the user asks to make the visual layer scalable without overbuilding.

## Scaling rules

- Preserve MVP behavior first.
- Extract primitives only after duplication appears twice.
- Keep domain modules explicit (`identity`, `profile`, `systems`, `review`).

## Architecture pattern

1. Introduce design tokens (spacing, typography, color).
2. Split page into section modules with typed props.
3. Add a section registry so new sections can be inserted without rewriting the page shell.
4. Centralize status badges (draft, in review, published).
5. Keep API adapters isolated from visual components.

## Anti-patterns

- Do not couple components directly to backend response quirks.
- Do not add marketplace-specific visuals into passport MVP pages.
- Do not create parallel component libraries.

## If implementation details are needed

Read: `references/scaling-checklist.md`.
