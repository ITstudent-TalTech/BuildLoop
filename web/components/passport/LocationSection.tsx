import FieldRow from "@/components/shared/FieldRow";
import SectionCard from "@/components/shared/SectionCard";
import type { Confidence, FieldValue, PassportDraft } from "@/lib/api";

interface LocationSectionProps {
  location: PassportDraft["location"];
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

export default function LocationSection({ location }: LocationSectionProps) {
  const fields = Object.values(location) as FieldValue<unknown>[];
  const populated = fields.filter((field) => field.value !== null).length;
  const coordinates = location.coordinates.value ?? "Coordinates unavailable";

  return (
    <SectionCard confidenceLabel={confidenceLabel(fields)} fieldsPopulated={populated} fieldsTotal={fields.length} title="Location">
      <div className="mb-3 overflow-hidden rounded-md border border-ink/10 bg-surface">
        <svg
          aria-label="Static location reference"
          className="h-40 w-full"
          preserveAspectRatio="none"
          role="img"
          viewBox="0 0 640 160"
        >
          <rect fill="#f6f8f7" height="160" width="640" />
          {Array.from({ length: 9 }).map((_, index) => (
            <line
              key={`vertical-${index}`}
              stroke="#4a5852"
              strokeOpacity="0.08"
              x1={index * 80}
              x2={index * 80}
              y1="0"
              y2="160"
            />
          ))}
          {Array.from({ length: 5 }).map((_, index) => (
            <line
              key={`horizontal-${index}`}
              stroke="#4a5852"
              strokeOpacity="0.08"
              x1="0"
              x2="640"
              y1={index * 40}
              y2={index * 40}
            />
          ))}
          <path
            d="M302 62 L352 72 L344 105 L296 97 Z"
            fill="#1f4d3a"
            fillOpacity="0.9"
          />
          <path
            d="M302 62 L352 72 L344 105 L296 97 Z"
            fill="none"
            stroke="#0d1f17"
            strokeOpacity="0.2"
          />
          <rect fill="#ffffff" fillOpacity="0.82" height="24" rx="4" width="230" x="16" y="120" />
          <text fill="#4a5852" fontFamily="ui-monospace, monospace" fontSize="12" x="26" y="136">
            {coordinates}
          </text>
          <rect fill="#ffffff" fillOpacity="0.82" height="24" rx="4" width="118" x="506" y="120" />
          <text fill="#4a5852" fontFamily="ui-monospace, monospace" fontSize="12" x="516" y="136">
            Static reference
          </text>
        </svg>
      </div>
      <div id="field-location-geometry_method"><FieldRow evidence={evidence(location.geometry_method)} label="Geometry method" value={location.geometry_method.value} /></div>
      <div id="field-location-shape_type"><FieldRow evidence={evidence(location.shape_type)} label="Shape type" value={location.shape_type.value} /></div>
      <div id="field-location-coordinates"><FieldRow evidence={evidence(location.coordinates)} isMono label="Coordinates" value={location.coordinates.value} /></div>
    </SectionCard>
  );
}
