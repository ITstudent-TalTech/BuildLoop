import FieldRow from "@/components/shared/FieldRow";
import SectionCard from "@/components/shared/SectionCard";
import type { Confidence, FieldValue, PassportDraft } from "@/lib/api";

interface StructuralSystemsSectionProps {
  systems: PassportDraft["structural_systems"];
}

function evidence(field: FieldValue<unknown>) {
  return { confidence: field.confidence, sourcePage: field.source?.page, sourceLabel: field.source?.label, lastUpdated: field.last_updated };
}

function confidenceLabel(fields: FieldValue<unknown>[]): Confidence {
  const counts = { high: 0, medium: 0, low: 0 };
  fields.forEach((field) => { if (field.value !== null) counts[field.confidence] += 1; });
  if (counts.low >= counts.medium && counts.low >= counts.high) return "low";
  if (counts.medium >= counts.high) return "medium";
  return "high";
}

export default function StructuralSystemsSection({ systems }: StructuralSystemsSectionProps) {
  const fields = Object.values(systems) as FieldValue<unknown>[];
  const populated = fields.filter((field) => field.value !== null).length;

  return (
    <SectionCard confidenceLabel={confidenceLabel(fields)} fieldsPopulated={populated} fieldsTotal={fields.length} title="Structural systems">
      <div id="field-structural_systems-foundation_type"><FieldRow evidence={evidence(systems.foundation_type)} label="Foundation type" value={systems.foundation_type.value} /></div>
      <div id="field-structural_systems-load_bearing_material"><FieldRow evidence={evidence(systems.load_bearing_material)} label="Load-bearing material" value={systems.load_bearing_material.value} /></div>
      <div id="field-structural_systems-wall_type"><FieldRow evidence={evidence(systems.wall_type)} label="Wall type" value={systems.wall_type.value} /></div>
      <div id="field-structural_systems-facade_finish_material"><FieldRow evidence={evidence(systems.facade_finish_material)} label="Facade finish" value={systems.facade_finish_material.value} /></div>
      <div id="field-structural_systems-floor_structure_material"><FieldRow evidence={evidence(systems.floor_structure_material)} label="Floor structure" value={systems.floor_structure_material.value} /></div>
      <div id="field-structural_systems-roof_structure_material"><FieldRow evidence={evidence(systems.roof_structure_material)} label="Roof structure" value={systems.roof_structure_material.value} /></div>
      <div id="field-structural_systems-roof_covering_material"><FieldRow evidence={evidence(systems.roof_covering_material)} label="Roof covering" value={systems.roof_covering_material.value} /></div>
    </SectionCard>
  );
}
