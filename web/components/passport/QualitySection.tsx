import SectionCard from "@/components/shared/SectionCard";
import MissingFieldJumpButton from "./MissingFieldJumpButton";
import type { PassportDraft } from "@/lib/api";

interface QualitySectionProps {
  quality: PassportDraft["quality"];
}

const missingFieldTargets: Record<string, string> = {
  "Building name": "field-building_profile-building_name",
  "Public-use area": "field-building_profile-public_use_area_m2",
  "Technical area": "field-building_profile-technical_area_m2",
  Length: "field-building_profile-length_m",
  Depth: "field-building_profile-depth_m",
  "Facade finish material": "field-structural_systems-facade_finish_material",
  Ventilation: "field-technical_systems-ventilation",
  "Use categories": "field-building_profile-use_categories",
  "Footprint area": "field-building_profile-footprint_area_m2",
  "Net area": "field-building_profile-net_area_m2",
  Height: "field-building_profile-height_m",
  Width: "field-building_profile-width_m",
  Volume: "field-building_profile-volume_m3",
  "Foundation type": "field-structural_systems-foundation_type",
  "Wall type": "field-structural_systems-wall_type",
  "Floor structure material": "field-structural_systems-floor_structure_material",
  "Roof structure material": "field-structural_systems-roof_structure_material",
  "Roof covering material": "field-structural_systems-roof_covering_material",
};

function QualityBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3 text-sm">
        <span className="text-ink-soft">{label}</span>
        <span className="font-mono tabular-nums text-ink">{Math.round(value)}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-forest-light">
        <div
          className="h-full rounded-full bg-forest"
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}

function sectionLabel(sectionName: string) {
  return sectionName
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function QualitySection({ quality }: QualitySectionProps) {
  const breakdown = Object.entries(quality.section_breakdown);

  return (
    <SectionCard
      confidenceLabel={quality.confidence_label}
      fieldsPopulated={Math.round(quality.schema_completeness_score)}
      fieldsTotal={100}
      title="Quality"
    >
      <div className="grid gap-5 md:grid-cols-2">
        <QualityBar
          label="Schema completeness"
          value={quality.schema_completeness_score}
        />
        <QualityBar label="Confidence" value={quality.confidence_score} />
      </div>

      <table className="mt-6 w-full text-sm">
        <thead>
          <tr className="text-xs uppercase tracking-wider text-ink-soft">
            <th className="py-2 text-left font-medium">Section</th>
            <th className="py-2 text-left font-medium">Fields</th>
            <th className="py-2 text-left font-medium">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {breakdown.map(([sectionName, item]) => (
            <tr className="border-t border-ink-soft/10" key={sectionName}>
              <td className="py-3 text-ink">{sectionLabel(sectionName)}</td>
              <td className="py-3 text-ink-soft">
                {item.fields_populated} of {item.fields_total} fields
              </td>
              <td className="py-3 text-ink-soft">{item.confidence_label}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {quality.missing_fields.length > 0 ? (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-ink">Missing fields</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {quality.missing_fields.map((field) => (
              <MissingFieldJumpButton
                field={field}
                key={field}
                targetId={missingFieldTargets[field] ?? "field-building_profile-building_name"}
              />
            ))}
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
