import FieldRow from "@/components/shared/FieldRow";
import SectionCard from "@/components/shared/SectionCard";
import type { Confidence, FieldValue, PassportDraft } from "@/lib/api";

interface IdentitySectionProps {
  identity: PassportDraft["identity"];
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

export default function IdentitySection({ identity }: IdentitySectionProps) {
  const fields = [
    identity.ehr_code,
    identity.normalized_address,
    identity.address_aliases,
    identity.country,
    identity.input_address,
  ] satisfies FieldValue<unknown>[];
  const populated = fields.filter((field) => field.value !== null).length;

  return (
    <SectionCard
      confidenceLabel={confidenceLabel(fields)}
      fieldsPopulated={populated}
      fieldsTotal={fields.length}
      title="Identity"
    >
      <div id="field-identity-ehr_code">
        <FieldRow
          evidence={evidence(identity.ehr_code)}
          isMono
          label="EHR code"
          value={identity.ehr_code.value}
        />
      </div>
      <div id="field-identity-normalized_address">
        <FieldRow
          evidence={evidence(identity.normalized_address)}
          label="Normalized address"
          value={identity.normalized_address.value}
        />
      </div>
      <div id="field-identity-address_aliases">
        <FieldRow
          evidence={evidence(identity.address_aliases)}
          label="Address aliases"
          value={identity.address_aliases.value?.join(" · ") ?? null}
        />
      </div>
      <div id="field-identity-country">
        <FieldRow
          evidence={evidence(identity.country)}
          label="Country"
          value={identity.country.value}
        />
      </div>
      <div id="field-identity-input_address">
        <FieldRow
          evidence={evidence(identity.input_address)}
          label="Original input"
          value={identity.input_address.value}
        />
      </div>
    </SectionCard>
  );
}
