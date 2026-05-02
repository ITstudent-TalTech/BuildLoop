interface EditedPillProps {
  oldValue: unknown;
  reason: string;
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "missing";
  }

  if (Array.isArray(value)) {
    return value.join(" · ");
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

export default function EditedPill({ oldValue, reason }: EditedPillProps) {
  return (
    <span
      className="inline-flex rounded bg-forest-light px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.06em] text-forest"
      title={`Edited from "${formatValue(oldValue)}" — Reason: "${reason}"`}
    >
      EDITED
    </span>
  );
}
