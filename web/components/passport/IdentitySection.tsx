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

// Address aliases are meaningful only when they differ from the normalized
// address (e.g., corner buildings like Lai 1 // Nunne 4 → ["Lai tn 1", "Nunne tn 4"]).
// For non-corner buildings the resolver stores a single-entry array equal to
// the full address itself, which adds nothing. Treat those as "not applicable"
// rather than missing data.
function formatAliases(
  aliases: string[] | null | undefined,
  normalizedAddress: string | null,
): string | null {
  if (!aliases || aliases.length === 0) return null;
  // Single alias that's the same as normalized address: redundant, hide.
  if (aliases.length === 1 && aliases[0] === normalizedAddress) return null;
  return aliases.join(" · ");
}

export default function IdentitySection({ identity }: IdentitySectionProps) {
  // Compute the displayable alias string upfront so we can treat the field as
  // "not applicable" (rather than "missing") when aliases add no info.
  const aliasDisplay = formatAliases(
    identity.address_aliases.value,
    identity.normalized_address.value,
  );

  // Stats use a relaxed "populated" check for aliases: if they're not
  // meaningfully present, the field doesn't count toward populated OR total.
  const baseFields = [
    identity.ehr_code,
    identity.normalized_address,
    identity.country,
    identity.input_address,
  ] satisfies FieldValue<unknown>[];
  const aliasesAreMeaningful = aliasDisplay !== null;
  const fieldsForConfidence = aliasesAreMeaningful
    ? [...baseFields, identity.address_aliases]
    : baseFields;
  const populated = fieldsForConfidence.filter((field) => field.value !== null).length;
  const total = fieldsForConfidence.length;

  return (
    <SectionCard
      confidenceLabel={confidenceLabel(fieldsForConfidence)}
      fieldsPopulated={populated}
      fieldsTotal={total}
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
      {aliasesAreMeaningful ? (
        <div id="field-identity-address_aliases">
          <FieldRow
            evidence={evidence(identity.address_aliases)}
            label="Address aliases"
            value={aliasDisplay}
          />
        </div>
      ) : null}
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