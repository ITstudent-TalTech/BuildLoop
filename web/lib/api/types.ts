export type Confidence = "high" | "medium" | "low";

export type ApiStatus = "ok";

export type FieldValue<T> = {
  value: T | null;
  unit?: string;
  confidence: Confidence;
  source?: FieldSource;
  last_updated?: string;
};

export type FieldSource = {
  document_id: string;
  page?: number;
  label: string;
};

export type IntakeRequest = {
  address_input: string;
  project_title: string;
};

export type IntakeResponse = {
  intake_request_id: string;
  project_id: string;
  status: "received";
};

export type ResolutionRequest = {
  intake_request_id: string;
};

export type ResolutionCandidate = {
  ehr_code: string;
  normalized_address: string;
  confidence_score: number;
};

export type ResolvedResolutionResponse = {
  status: "resolved";
  resolution_run_id: string;
  ehr_code: string;
  normalized_address: string;
  address_aliases: string[];
  confidence_score: number;
};

export type AmbiguousResolutionResponse = {
  status: "ambiguous";
  resolution_run_id: string;
  candidates: ResolutionCandidate[];
};

export type UnresolvedResolutionResponse = {
  status: "unresolved";
  resolution_run_id: string;
  candidates: [];
};

export type ResolutionResponse =
  | ResolvedResolutionResponse
  | AmbiguousResolutionResponse
  | UnresolvedResolutionResponse;

export type SourceDocument = {
  source_document_id: string;
  building_id: string;
  source_type: "ehr_pdf" | "ehr_register" | "cadastre" | "manual_upload";
  source_uri: string;
  mime_type: string;
  checksum: string;
  fetched_at: string;
  parser_status: "pending" | "parsed" | "failed";
  storage_key: string;
};

export type SourceFetchResponse = {
  status: ApiStatus;
  source_document_id: string;
  source_type: SourceDocument["source_type"];
  fetch_status: ApiStatus;
};

export type ExtractionRun = {
  extraction_run_id: string;
  source_document_id: string;
  parser_name: string;
  parser_version: string;
  status: "pending" | "running" | "completed" | "failed";
  started_at: string;
  completed_at?: string;
  error_summary?: string;
};

export type ParseResponse = {
  status: ApiStatus;
  extraction_run_id: string;
  observation_count: number;
};

export type BuildingPart = {
  part_identifier: FieldValue<string>;
  part_type: FieldValue<string>;
  part_name: FieldValue<string>;
  part_use: FieldValue<string>;
  part_area_m2: FieldValue<number>;
};

export type PassportDraft = {
  passport_draft_id: string;
  building_id: string;
  project_id: string;
  schema_version: "buildloop.passport.mvp.v1";
  status: "draft" | "published";
  generated_at: string;
  identity: {
    ehr_code: FieldValue<string>;
    normalized_address: FieldValue<string>;
    address_aliases: FieldValue<string[]>;
    country: FieldValue<string>;
    input_address: FieldValue<string>;
  };
  building_profile: {
    building_type: FieldValue<string>;
    building_status: FieldValue<string>;
    building_name: FieldValue<string>;
    use_categories: FieldValue<string[]>;
    floors: FieldValue<{
      above_ground: number | null;
      below_ground: number | null;
    }>;
    footprint_area_m2: FieldValue<number>;
    heated_area_m2: FieldValue<number>;
    net_area_m2: FieldValue<number>;
    public_use_area_m2: FieldValue<number>;
    technical_area_m2: FieldValue<number>;
    height_m: FieldValue<number>;
    length_m: FieldValue<number>;
    width_m: FieldValue<number>;
    depth_m: FieldValue<number>;
    volume_m3: FieldValue<number>;
  };
  structural_systems: {
    foundation_type: FieldValue<string>;
    load_bearing_material: FieldValue<string>;
    wall_type: FieldValue<string>;
    facade_finish_material: FieldValue<string>;
    floor_structure_material: FieldValue<string>;
    roof_structure_material: FieldValue<string>;
    roof_covering_material: FieldValue<string>;
  };
  technical_systems: {
    electricity: FieldValue<string>;
    water: FieldValue<string>;
    sewer: FieldValue<string>;
    heat_source: FieldValue<string>;
    gas: FieldValue<string>;
    ventilation: FieldValue<string>;
    lift_count: FieldValue<number>;
  };
  location: {
    geometry_method: FieldValue<string>;
    shape_type: FieldValue<string>;
    coordinates: FieldValue<string>;
  };
  building_parts: {
    parts: BuildingPart[];
    confidence: Confidence;
    source?: FieldSource;
  };
  quality: PassportQuality;
};

export type PassportQuality = {
  schema_completeness_score: number;
  confidence_score: number;
  confidence_label: Confidence;
  section_breakdown: {
    [sectionName: string]: {
      fields_populated: number;
      fields_total: number;
      confidence_label: Confidence;
    };
  };
  missing_fields: string[];
};

export type PassportDraftResponse = {
  status: ApiStatus;
  passport_draft_id: string;
  schema_version: PassportDraft["schema_version"];
  schema_completeness_score: number;
  confidence_score: number;
};

export type PassportVersion = {
  passport_version_id: string;
  passport_draft_id: string;
  version_number: number;
  payload_json: PassportDraft;
  pdf_storage_key?: string;
  published_at: string;
  published_by: string;
};

export type PublishResponse = {
  status: "published";
  passport_version_id: string;
  version_number: number;
};

export type ManualEdit = {
  manual_edit_id: string;
  building_id: string;
  target_field_path: string;
  old_value_json: unknown;
  new_value_json: unknown;
  edit_type: "override" | "confirmation" | "correction";
  reason: string;
  actor: string;
  created_at: string;
};

export type FieldEditRequest = {
  target_field_path: string;
  new_value: unknown;
  reason: string;
};
