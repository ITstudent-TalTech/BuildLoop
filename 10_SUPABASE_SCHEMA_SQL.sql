-- BUILDLoop v6 Supabase / Postgres schema
-- Purpose: product data plane for passport-first architecture

create extension if not exists pgcrypto;

-- ==========================================
-- Core identity tables
-- ==========================================

create table if not exists public.buildings (
  id uuid primary key default gen_random_uuid(),
  country_code text not null default 'EE',
  primary_ehr_code text,
  normalized_address text,
  address_aliases jsonb not null default '[]'::jsonb,
  municipality text,
  county text,
  source_identity_confidence numeric(5,2),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_buildings_primary_ehr_code on public.buildings(primary_ehr_code);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  building_id uuid references public.buildings(id) on delete set null,
  owner_user_id uuid,
  title text,
  raw_input_address text,
  status text not null default 'draft',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ==========================================
-- Resolver / intake
-- ==========================================

create table if not exists public.intake_requests (
  id uuid primary key default gen_random_uuid(),
  raw_address_input text not null,
  normalized_input jsonb,
  country_code text not null default 'EE',
  status text not null default 'received',
  created_at timestamptz not null default now()
);

create table if not exists public.address_resolution_runs (
  id uuid primary key default gen_random_uuid(),
  intake_request_id uuid references public.intake_requests(id) on delete cascade,
  project_id uuid references public.projects(id) on delete set null,
  resolver_version text not null,
  status text not null,
  resolved_ehr_code text,
  normalized_address text,
  address_aliases jsonb not null default '[]'::jsonb,
  confidence_score numeric(5,2),
  reason text,
  query_variants jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.address_resolution_candidates (
  id uuid primary key default gen_random_uuid(),
  resolution_run_id uuid references public.address_resolution_runs(id) on delete cascade,
  ehr_code text,
  normalized_address text,
  address_aliases jsonb not null default '[]'::jsonb,
  confidence_score numeric(5,2),
  object_types jsonb not null default '[]'::jsonb,
  matched_query_variants jsonb not null default '[]'::jsonb,
  match_reasons jsonb not null default '[]'::jsonb,
  primary_candidate boolean not null default false,
  raw_candidate jsonb,
  created_at timestamptz not null default now()
);

-- ==========================================
-- Source ingestion
-- ==========================================

create table if not exists public.source_documents (
  id uuid primary key default gen_random_uuid(),
  building_id uuid references public.buildings(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  source_type text not null,
  source_uri text,
  mime_type text,
  checksum text,
  fetched_at timestamptz,
  parser_status text,
  storage_bucket text,
  storage_path text,
  fetch_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_source_documents_building_id on public.source_documents(building_id);

create table if not exists public.extraction_runs (
  id uuid primary key default gen_random_uuid(),
  source_document_id uuid references public.source_documents(id) on delete cascade,
  parser_name text not null,
  parser_version text not null,
  status text not null,
  error_summary text,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

-- ==========================================
-- Canonical observations
-- ==========================================

create table if not exists public.observations (
  id uuid primary key default gen_random_uuid(),
  building_id uuid references public.buildings(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  source_document_id uuid references public.source_documents(id) on delete cascade,
  extraction_run_id uuid references public.extraction_runs(id) on delete cascade,
  namespace text not null,
  key text not null,
  section text not null,
  value_json jsonb not null,
  unit text,
  relevance_class text not null,
  confidence_score numeric(5,2),
  confidence_label text,
  evidence_text text,
  page_number integer,
  source_locator text,
  created_at timestamptz not null default now()
);

create index if not exists idx_observations_building_id on public.observations(building_id);
create index if not exists idx_observations_project_id on public.observations(project_id);
create index if not exists idx_observations_namespace_key on public.observations(namespace, key);
create index if not exists idx_observations_relevance_class on public.observations(relevance_class);

-- ==========================================
-- Passport drafts and versions
-- ==========================================

create table if not exists public.passport_drafts (
  id uuid primary key default gen_random_uuid(),
  building_id uuid references public.buildings(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  schema_version text not null,
  status text not null default 'draft_system_generated',
  payload_json jsonb not null,
  schema_completeness_score numeric(5,2),
  confidence_score numeric(5,2),
  generated_at timestamptz not null default now()
);

create table if not exists public.passport_versions (
  id uuid primary key default gen_random_uuid(),
  passport_draft_id uuid references public.passport_drafts(id) on delete cascade,
  version_number integer not null,
  payload_json jsonb not null,
  pdf_storage_bucket text,
  pdf_storage_path text,
  published_at timestamptz not null default now(),
  published_by uuid
);

create unique index if not exists idx_passport_versions_unique on public.passport_versions(passport_draft_id, version_number);

-- ==========================================
-- Review / enrichment
-- ==========================================

create table if not exists public.manual_edits (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade,
  building_id uuid references public.buildings(id) on delete cascade,
  passport_draft_id uuid references public.passport_drafts(id) on delete cascade,
  target_field_path text not null,
  old_value_json jsonb,
  new_value_json jsonb,
  edit_type text not null,
  reason text,
  actor_user_id uuid,
  created_at timestamptz not null default now()
);

create table if not exists public.photo_assets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade,
  building_id uuid references public.buildings(id) on delete cascade,
  storage_bucket text not null,
  storage_path text not null,
  uploaded_by uuid,
  uploaded_at timestamptz not null default now(),
  metadata_json jsonb not null default '{}'::jsonb
);

create table if not exists public.condition_annotations (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade,
  building_id uuid references public.buildings(id) on delete cascade,
  target_path text not null,
  condition_label text not null,
  salvage_label text,
  note text,
  photo_asset_ids jsonb not null default '[]'::jsonb,
  actor_user_id uuid,
  created_at timestamptz not null default now()
);

-- ==========================================
-- Listing candidates (future-facing but modeled now)
-- ==========================================

create table if not exists public.listing_candidates (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade,
  building_id uuid references public.buildings(id) on delete cascade,
  source_passport_draft_id uuid references public.passport_drafts(id) on delete cascade,
  status text not null default 'derived',
  listing_payload_json jsonb not null,
  created_at timestamptz not null default now()
);

-- ==========================================
-- Updated_at trigger helper
-- ==========================================

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_buildings_updated_at on public.buildings;
create trigger trg_buildings_updated_at
before update on public.buildings
for each row execute function public.set_updated_at();

drop trigger if exists trg_projects_updated_at on public.projects;
create trigger trg_projects_updated_at
before update on public.projects
for each row execute function public.set_updated_at();

-- ==========================================
-- Suggested RLS note
-- ==========================================
-- In Supabase, enable RLS and scope project/building/passport rows to the owning org/user roles.
-- Keep raw source documents and observations accessible only through service-role or controlled backend paths.
