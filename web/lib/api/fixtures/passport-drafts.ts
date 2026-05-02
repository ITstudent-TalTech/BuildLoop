import type {
  BuildingPart,
  Confidence,
  FieldSource,
  FieldValue,
  PassportDraft,
  PassportQuality,
} from "../types";

const source: FieldSource = {
  document_id: "src_ehr_pdf_001",
  label: "EHR PDF",
};

const updated = "2026-04-24T09:30:00.000Z";

function field<T>(
  value: T | null,
  confidence: Confidence = "high",
  page = 1,
  unit?: string,
): FieldValue<T> {
  return {
    value,
    unit,
    confidence,
    source: {
      ...source,
      page,
    },
    last_updated: updated,
  };
}

function missing<T>(confidence: Confidence = "low", page = 1, unit?: string): FieldValue<T> {
  return field<T>(null, confidence, page, unit);
}

const identity = {
  ehr_code: field("101035685", "high", 1),
  normalized_address: field(
    "Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4",
    "high",
    1,
  ),
  address_aliases: field(["Lai tn 1", "Nunne tn 4"], "high", 1),
  country: field("Estonia", "high", 1),
  input_address: field("Lai 1, 10133 Tallinn", "high", 1),
};

const completeBuildingProfile = {
  building_type: field("Residential", "high", 1),
  building_status: field("In use", "high", 1),
  building_name: field("Lai 1 / Nunne 4 residential building", "medium", 1),
  use_categories: field(["Apartment building (11200)"], "high", 2),
  floors: field({ above_ground: 4, below_ground: 1 }, "high", 2),
  footprint_area_m2: field(412, "high", 3, "m²"),
  heated_area_m2: field(1648, "high", 3, "m²"),
  net_area_m2: field(1532, "high", 3, "m²"),
  public_use_area_m2: field(0, "medium", 3, "m²"),
  technical_area_m2: field(38, "medium", 3, "m²"),
  height_m: field(14.2, "high", 4, "m"),
  length_m: field(32, "medium", 4, "m"),
  width_m: field(13, "medium", 4, "m"),
  depth_m: field(12.5, "medium", 4, "m"),
  volume_m3: field(5860, "high", 4, "m³"),
};

const completeStructuralSystems = {
  foundation_type: field("Concrete strip foundation", "high", 5),
  load_bearing_material: field("Brick masonry", "high", 5),
  wall_type: field("Load-bearing exterior walls", "high", 5),
  facade_finish_material: field("Plaster", "medium", 5),
  floor_structure_material: field("Reinforced concrete", "high", 6),
  roof_structure_material: field("Wooden truss", "high", 6),
  roof_covering_material: field("Clay tile", "high", 6),
};

const completeTechnicalSystems = {
  electricity: field("Connected", "high", 7),
  water: field("Central network", "high", 7),
  sewer: field("Central network", "high", 7),
  heat_source: field("District heating", "high", 7),
  gas: field("Not connected", "high", 7),
  ventilation: field("Natural ventilation", "medium", 7),
  lift_count: field(0, "high", 7),
};

const completeLocation = {
  geometry_method: field("Cadastral footprint", "high", 8),
  shape_type: field("Polygon", "high", 8),
  coordinates: field("59.4395° N, 24.7445° E", "high", 8),
};

function part(
  id: string,
  type: string,
  name: string,
  use: string,
  area: number,
  confidence: Confidence = "high",
): BuildingPart {
  return {
    part_identifier: field(id, confidence, 8),
    part_type: field(type, confidence, 8),
    part_name: field(name, confidence, 8),
    part_use: field(use, confidence, 8),
    part_area_m2: field(area, confidence, 8, "m²"),
  };
}

const completeParts = {
  parts: [
    part("part_001", "Exterior wall", "Brick exterior walls", "Envelope", 620),
    part("part_002", "Floor slab", "Reinforced concrete slabs", "Structure", 1532),
    part("part_003", "Roof", "Timber roof and clay tiles", "Envelope", 420),
    part("part_004", "Windows", "Timber frame windows", "Openings", 96, "medium"),
    part("part_005", "Stair", "Main reinforced concrete stair", "Circulation", 48),
  ],
  confidence: "high" as const,
  source: { ...source, page: 8 },
};

function quality(
  completeness: number,
  confidenceScore: number,
  confidenceLabel: Confidence,
  missingFields: string[],
  overrides: PassportQuality["section_breakdown"] = {},
): PassportQuality {
  return {
    schema_completeness_score: completeness,
    confidence_score: confidenceScore,
    confidence_label: confidenceLabel,
    section_breakdown: {
      identity: { fields_populated: 5, fields_total: 5, confidence_label: "high" },
      building_profile: {
        fields_populated: 15,
        fields_total: 15,
        confidence_label: "high",
      },
      structural_systems: {
        fields_populated: 7,
        fields_total: 7,
        confidence_label: "high",
      },
      technical_systems: {
        fields_populated: 7,
        fields_total: 7,
        confidence_label: "high",
      },
      location: { fields_populated: 3, fields_total: 3, confidence_label: "high" },
      building_parts: {
        fields_populated: 5,
        fields_total: 5,
        confidence_label: "high",
      },
      ...overrides,
    },
    missing_fields: missingFields,
  };
}

export const completeDraftFixture: PassportDraft = {
  passport_draft_id: "draft_lai_complete_001",
  building_id: "building_101035685",
  project_id: "demo-project-id",
  schema_version: "buildloop.passport.mvp.v1",
  status: "draft",
  generated_at: "2026-04-24T10:15:00.000Z",
  identity,
  building_profile: completeBuildingProfile,
  structural_systems: completeStructuralSystems,
  technical_systems: completeTechnicalSystems,
  location: completeLocation,
  building_parts: completeParts,
  quality: quality(96, 91, "high", []),
};

export const partialDraftFixture: PassportDraft = {
  ...completeDraftFixture,
  passport_draft_id: "draft_lai_partial_001",
  generated_at: "2026-04-24T10:25:00.000Z",
  building_profile: {
    ...completeBuildingProfile,
    building_status: completeBuildingProfile.building_status,
    building_name: missing<string>("low", 1),
    use_categories: field(["Apartment building (11200)"], "medium", 2),
    public_use_area_m2: missing<number>("low", 3, "m²"),
    technical_area_m2: missing<number>("medium", 3, "m²"),
    length_m: missing<number>("medium", 4, "m"),
    width_m: field(13, "medium", 4, "m"),
    depth_m: missing<number>("low", 4, "m"),
  },
  structural_systems: {
    ...completeStructuralSystems,
    facade_finish_material: missing<string>("medium", 5),
    roof_covering_material: field("Clay tile", "medium", 6),
  },
  technical_systems: {
    ...completeTechnicalSystems,
    ventilation: missing<string>("medium", 7),
  },
  building_parts: {
    parts: [
      part("part_001", "Exterior wall", "Brick exterior walls", "Envelope", 620, "medium"),
      part("part_002", "Floor slab", "Reinforced concrete slabs", "Structure", 1532, "medium"),
      part("part_003", "Roof", "Timber roof and clay tiles", "Envelope", 420, "low"),
    ],
    confidence: "medium",
    source: { ...source, page: 8 },
  },
  quality: quality(62, 69, "medium", [
    "Building name",
    "Public-use area",
    "Technical area",
    "Length",
    "Depth",
    "Facade finish material",
    "Ventilation",
  ], {
    building_profile: {
      fields_populated: 10,
      fields_total: 15,
      confidence_label: "medium",
    },
    structural_systems: {
      fields_populated: 6,
      fields_total: 7,
      confidence_label: "medium",
    },
    technical_systems: {
      fields_populated: 6,
      fields_total: 7,
      confidence_label: "medium",
    },
    building_parts: {
      fields_populated: 3,
      fields_total: 5,
      confidence_label: "medium",
    },
  }),
};

export const sparseDraftFixture: PassportDraft = {
  ...completeDraftFixture,
  passport_draft_id: "draft_lai_sparse_001",
  generated_at: "2026-04-24T10:35:00.000Z",
  building_profile: {
    building_type: field("Residential", "medium", 1),
    building_status: field("In use", "medium", 1),
    building_name: missing<string>("low", 1),
    use_categories: missing<string[]>("low", 2),
    floors: field({ above_ground: 4, below_ground: null }, "medium", 2),
    footprint_area_m2: missing<number>("low", 3, "m²"),
    heated_area_m2: field(1648, "medium", 3, "m²"),
    net_area_m2: missing<number>("low", 3, "m²"),
    public_use_area_m2: missing<number>("low", 3, "m²"),
    technical_area_m2: missing<number>("low", 3, "m²"),
    height_m: missing<number>("low", 4, "m"),
    length_m: missing<number>("low", 4, "m"),
    width_m: missing<number>("low", 4, "m"),
    depth_m: missing<number>("low", 4, "m"),
    volume_m3: missing<number>("low", 4, "m³"),
  },
  structural_systems: {
    foundation_type: missing<string>("low", 5),
    load_bearing_material: field("Brick masonry", "medium", 5),
    wall_type: missing<string>("low", 5),
    facade_finish_material: missing<string>("low", 5),
    floor_structure_material: missing<string>("low", 6),
    roof_structure_material: missing<string>("low", 6),
    roof_covering_material: missing<string>("low", 6),
  },
  technical_systems: {
    electricity: missing<string>("low", 7),
    water: missing<string>("low", 7),
    sewer: missing<string>("low", 7),
    heat_source: field("District heating", "medium", 7),
    gas: missing<string>("low", 7),
    ventilation: missing<string>("low", 7),
    lift_count: missing<number>("low", 7),
  },
  location: {
    geometry_method: missing<string>("low", 8),
    shape_type: missing<string>("low", 8),
    coordinates: missing<string>("low", 8),
  },
  building_parts: {
    parts: [],
    confidence: "low",
    source: { ...source, page: 8 },
  },
  quality: quality(31, 42, "low", [
    "Use categories",
    "Footprint area",
    "Net area",
    "Public-use area",
    "Technical area",
    "Height",
    "Length",
    "Width",
    "Depth",
    "Volume",
    "Foundation type",
    "Wall type",
    "Facade finish material",
    "Floor structure material",
    "Roof structure material",
    "Roof covering material",
    "Building parts",
  ], {
    building_profile: {
      fields_populated: 4,
      fields_total: 15,
      confidence_label: "low",
    },
    structural_systems: {
      fields_populated: 1,
      fields_total: 7,
      confidence_label: "low",
    },
    technical_systems: {
      fields_populated: 1,
      fields_total: 7,
      confidence_label: "low",
    },
    location: { fields_populated: 0, fields_total: 3, confidence_label: "low" },
    building_parts: {
      fields_populated: 0,
      fields_total: 5,
      confidence_label: "low",
    },
  }),
};
