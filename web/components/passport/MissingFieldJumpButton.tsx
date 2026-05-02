"use client";

interface MissingFieldJumpButtonProps {
  field: string;
  targetId: string;
}

export default function MissingFieldJumpButton({
  field,
  targetId,
}: MissingFieldJumpButtonProps) {
  return (
    <button
      aria-label={`Jump to ${field}`}
      className="rounded border border-ink/10 bg-surface px-2 py-1 text-left text-sm text-ink-soft transition hover:border-forest/40 hover:text-ink"
      onClick={() => {
        document.getElementById(targetId)?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }}
      type="button"
    >
      {field}
    </button>
  );
}
