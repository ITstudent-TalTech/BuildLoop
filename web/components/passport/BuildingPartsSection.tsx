import EvidenceBadge from "@/components/shared/EvidenceBadge";
import SectionCard from "@/components/shared/SectionCard";
import type { PassportDraft } from "@/lib/api";

interface BuildingPartsSectionProps {
  buildingParts: PassportDraft["building_parts"];
}

function formatArea(value: number | null, unit?: string) {
  if (value === null) return "—";

  const formatted = new Intl.NumberFormat("et-EE")
    .format(value)
    .replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0");

  return unit ? `${formatted}\u202F${unit}` : formatted;
}

export default function BuildingPartsSection({
  buildingParts,
}: BuildingPartsSectionProps) {
  const parts = buildingParts.parts;

  return (
    <SectionCard
      confidenceLabel={buildingParts.confidence}
      fieldsPopulated={parts.length}
      fieldsTotal={parts.length || 1}
      title="Building parts"
    >
      {parts.length === 0 ? (
        <p className="py-3 text-sm text-ink-soft">
          No building parts in the register record. You can add them during
          review.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="mt-2 w-full text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wider text-ink-soft">
                <th className="py-2 text-left font-medium">Identifier</th>
                <th className="py-2 text-left font-medium">Type</th>
                <th className="py-2 text-left font-medium">Name</th>
                <th className="py-2 text-left font-medium">Use</th>
                <th className="py-2 text-right font-medium">Area</th>
                <th className="w-10 py-2 text-right font-medium">
                  <span className="sr-only">Source</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {parts.map((part, index) => (
                <tr
                  className="border-t border-ink-soft/10"
                  key={part.part_identifier.value ?? index}
                >
                  <td className="py-3 font-mono text-ink">
                    {part.part_identifier.value}
                  </td>
                  <td className="py-3 text-ink">{part.part_type.value}</td>
                  <td className="py-3 text-ink">{part.part_name.value}</td>
                  <td className="py-3 text-ink-soft">{part.part_use.value}</td>
                  <td className="py-3 text-right tabular-nums text-ink">
                    {formatArea(part.part_area_m2.value, part.part_area_m2.unit)}
                  </td>
                  <td className="py-3 text-right">
                    <EvidenceBadge
                      confidence={part.part_identifier.confidence}
                      lastUpdated={part.part_identifier.last_updated}
                      sourceLabel={part.part_identifier.source?.label}
                      sourcePage={part.part_identifier.source?.page}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionCard>
  );
}
