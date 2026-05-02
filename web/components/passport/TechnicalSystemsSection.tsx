import FieldRow from "@/components/shared/FieldRow";
import SectionCard from "@/components/shared/SectionCard";
import type { Confidence, FieldValue, PassportDraft } from "@/lib/api";

interface TechnicalSystemsSectionProps {
  systems: PassportDraft["technical_systems"];
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

export default function TechnicalSystemsSection({ systems }: TechnicalSystemsSectionProps) {
  const fields = Object.values(systems) as FieldValue<unknown>[];
  const populated = fields.filter((field) => field.value !== null).length;

  return (
    <SectionCard confidenceLabel={confidenceLabel(fields)} fieldsPopulated={populated} fieldsTotal={fields.length} title="Technical systems">
      <div id="field-technical_systems-electricity"><FieldRow evidence={evidence(systems.electricity)} label="Electricity" value={systems.electricity.value} /></div>
      <div id="field-technical_systems-water"><FieldRow evidence={evidence(systems.water)} label="Water" value={systems.water.value} /></div>
      <div id="field-technical_systems-sewer"><FieldRow evidence={evidence(systems.sewer)} label="Sewer" value={systems.sewer.value} /></div>
      <div id="field-technical_systems-heat_source"><FieldRow evidence={evidence(systems.heat_source)} label="Heat source" value={systems.heat_source.value} /></div>
      <div id="field-technical_systems-gas"><FieldRow evidence={evidence(systems.gas)} label="Gas" value={systems.gas.value} /></div>
      <div id="field-technical_systems-ventilation"><FieldRow evidence={evidence(systems.ventilation)} label="Ventilation" value={systems.ventilation.value} /></div>
      <div id="field-technical_systems-lift_count"><FieldRow evidence={evidence(systems.lift_count)} label="Lifts" value={systems.lift_count.value} /></div>
    </SectionCard>
  );
}
