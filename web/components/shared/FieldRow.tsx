import EvidenceBadge, { type Confidence } from "./EvidenceBadge";

interface FieldEvidence {
  confidence: Confidence;
  sourcePage?: number;
  sourceLabel?: string;
  sourceUrl?: string;
  lastUpdated?: string;
}

interface FieldRowProps {
  label: string;
  value: string | number | null | undefined;
  unit?: string;
  isMono?: boolean;
  evidence?: FieldEvidence;
}

function formatValue(value: string | number) {
  if (typeof value === "number") {
    return new Intl.NumberFormat("et-EE")
      .format(value)
      .replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0");
  }

  return value;
}

export default function FieldRow({
  label,
  value,
  unit,
  isMono = false,
  evidence,
}: FieldRowProps) {
  const isMissing = value == null;

  return (
    <div className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 border-b border-ink/10 py-3 last:border-b-0 md:grid-cols-[minmax(120px,30%)_1fr_auto] md:items-baseline md:gap-4">
      <div className="text-xs font-medium uppercase leading-5 tracking-[0.06em] text-ink-soft md:text-sm md:font-normal md:normal-case md:tracking-normal">
        {label}
      </div>
      <div
        className={[
          "col-span-2 break-words text-sm font-normal leading-5 md:col-span-1",
          isMissing ? "text-ink-soft" : "text-ink",
          isMono ? "font-mono" : "font-sans",
        ].join(" ")}
      >
        {isMissing ? (
          "—"
        ) : (
          <>
            {formatValue(value)}
            {unit ? <span>{"\u202F"}{unit}</span> : null}
          </>
        )}
      </div>
      <div className="row-start-1 flex min-w-10 items-center justify-end self-start md:col-start-3 md:min-w-16 md:self-center">
        {isMissing ? (
          <span className="rounded border border-ink/10 bg-surface px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.06em] text-ink-soft">
            MISSING
          </span>
        ) : evidence ? (
          <EvidenceBadge {...evidence} />
        ) : null}
      </div>
    </div>
  );
}
