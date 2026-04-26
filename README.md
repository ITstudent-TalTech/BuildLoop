# BUILDLoop Codex Architecture Pack v6

This pack is the working implementation package for BUILDLoop's passport-first product strategy.

It assumes the validated workflow is:

**user address -> address resolution -> EHR code -> public EHR PDF -> canonical observations -> relevance filtering -> passport draft -> professional review/edit -> published passport**

It also assumes the selected stack is:

- **Supabase** for Postgres, Auth, Storage, RLS, and product data plane
- **FastAPI** for resolver, source adapters, parsing, observation engine, relevance engine, and passport orchestration

## Reading order

1. `00_EXECUTIVE_REFRAME.md`
2. `01_UPDATED_PRODUCT_ROADMAP.md`
3. `02_VALIDATED_WORKFLOW_AND_SYSTEM_BOUNDARIES.md`
4. `03_PASSPORT_DOMAIN_MODEL_AND_CANONICAL_SCHEMA.md`
5. `04_PASSPORT_MVP_SYSTEM_ARCHITECTURE.md`
6. `05_DATA_RELEVANCE_POLICY.md`
7. `07_HYBRID_STACK_DECISION_AND_DEPLOYMENT_ARCHITECTURE.md`
8. `08_AGENTIC_AI_FIRST_DEVELOPMENT_MODEL.md`
9. `09_MATERIAL_PASSPORT_CONSTRUCT_AND_HYBRID_WORKFLOW.md`
10. `10_SUPABASE_SCHEMA_SQL.sql`
11. `11_FASTAPI_API_CONTRACTS.md`
12. `12_CODEX_AGENT_TASK_CARDS.md`
13. `06_IMPLEMENTATION_PLAN_BACKLOG_AND_AGENTS.md`

## What's new in v6

- full material passport construct defined
- hybrid passport-generation workflow defined explicitly
- concrete Supabase schema SQL added
- concrete FastAPI route contracts added
- Codex-native agent task cards added
- workflow scripts retained for execution continuity

## Product rule

The material passport is not a raw source dump.

It is a **reviewable, versioned, evidence-backed representation of a building's reuse-relevant characteristics**.

## Dev mode and UI skills

- Dev workflow recommendation: `DEV_MODE.md`
- Visual agent skills:
  - `skills/passport-ui-mvp`
  - `skills/passport-ui-scale`
