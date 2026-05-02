import FieldRow from "@/components/shared/FieldRow";
import SectionCard from "@/components/shared/SectionCard";
import type { Confidence, FieldValue, PassportDraft } from "@/lib/api";

interface BuildingProfileSectionProps {
  profile: PassportDraft["building_profile"];
}

function evidence(field: FieldValue<unknown>) {
  return {
    confidence: field.confidence,
    sourcePage: field.source?.page,
    sourceLabel: field.source?.label,
    lastUpdated: field.last_updated,
  };
}

function confidenceLabel(fields: FieldValue<unknown>[]): Confidence {
  const counts = { high: 0, medium: 0, low: 0 };
  fields.forEach((field) => {
    if (field.value !== null) counts[field.confidence] += 1;
  });
  if (counts.low >= counts.medium && counts.low >= counts.high) return "low";
  if (counts.medium >= counts.high) return "medium";
  return "high";
}

export default function BuildingProfileSection({
  profile,
}: BuildingProfileSectionProps) {
  const fields = Object.values(profile) as FieldValue<unknown>[];
  const populated = fields.filter((field) => field.value !== null).length;

  return (
    <SectionCard
      confidenceLabel={confidenceLabel(fields)}
      fieldsPopulated={populated}
      fieldsTotal={fields.length}
      title="Building profile"
    >
      <div id="field-building_profile-building_type">
        <FieldRow evidence={evidence(profile.building_type)} label="Building type" value={profile.building_type.value} />
      </div>
      <div id="field-building_profile-building_status">
        <FieldRow evidence={evidence(profile.building_status)} label="Building status" value={profile.building_status.value} />
      </div>
      <div id="field-building_profile-building_name">
        <FieldRow evidence={evidence(profile.building_name)} label="Building name" value={profile.building_name.value} />
      </div>
      <div id="field-building_profile-use_categories">
        <FieldRow evidence={evidence(profile.use_categories)} label="Use categories" value={profile.use_categories.value?.join(" · ") ?? null} />
      </div>
      <div id="field-building_profile-floors_above_ground">
        <FieldRow evidence={evidence(profile.floors)} label="Floors above ground" value={profile.floors.value?.above_ground} />
      </div>
      <div id="field-building_profile-floors_below_ground">
        <FieldRow evidence={evidence(profile.floors)} label="Floors below ground" value={profile.floors.value?.below_ground} />
      </div>
      <div id="field-building_profile-footprint_area_m2">
        <FieldRow evidence={evidence(profile.footprint_area_m2)} label="Footprint area" unit={profile.footprint_area_m2.unit} value={profile.footprint_area_m2.value} />
      </div>
      <div id="field-building_profile-heated_area_m2">
        <FieldRow evidence={evidence(profile.heated_area_m2)} label="Heated area" unit={profile.heated_area_m2.unit} value={profile.heated_area_m2.value} />
      </div>
      <div id="field-building_profile-net_area_m2">
        <FieldRow evidence={evidence(profile.net_area_m2)} label="Net area" unit={profile.net_area_m2.unit} value={profile.net_area_m2.value} />
      </div>
      <div id="field-building_profile-public_use_area_m2">
        <FieldRow evidence={evidence(profile.public_use_area_m2)} label="Public-use area" unit={profile.public_use_area_m2.unit} value={profile.public_use_area_m2.value} />
      </div>
      <div id="field-building_profile-technical_area_m2">
        <FieldRow evidence={evidence(profile.technical_area_m2)} label="Technical area" unit={profile.technical_area_m2.unit} value={profile.technical_area_m2.value} />
      </div>
      <div id="field-building_profile-height_m">
        <FieldRow evidence={evidence(profile.height_m)} label="Height" unit={profile.height_m.unit} value={profile.height_m.value} />
      </div>
      <div id="field-building_profile-length_m">
        <FieldRow evidence={evidence(profile.length_m)} label="Length" unit={profile.length_m.unit} value={profile.length_m.value} />
      </div>
      <div id="field-building_profile-width_m">
        <FieldRow evidence={evidence(profile.width_m)} label="Width" unit={profile.width_m.unit} value={profile.width_m.value} />
      </div>
      <div id="field-building_profile-volume_m3">
        <FieldRow evidence={evidence(profile.volume_m3)} label="Volume" unit={profile.volume_m3.unit} value={profile.volume_m3.value} />
      </div>
    </SectionCard>
  );
}
