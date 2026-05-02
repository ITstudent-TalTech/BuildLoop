import Link from "next/link";

interface UnresolvedStateProps {
  originalAddress: string;
}

const suggestions = [
  "Use the street address only (no apartment number)",
  "Try a nearby landmark or postal code",
  "Enter the EHR code directly if you have it",
];

export default function UnresolvedState({ originalAddress }: UnresolvedStateProps) {
  return (
    <section className="mt-8">
      <div
        aria-hidden="true"
        className="flex size-11 items-center justify-center rounded-full border border-ink-soft/25 bg-white font-mono text-lg text-ink-soft"
      >
        ?
      </div>

      <p className="mt-6 text-ink">Try one of these:</p>
      <ul className="mt-4 space-y-3">
        {suggestions.map((suggestion) => (
          <li className="flex gap-3 text-sm" key={suggestion}>
            <span className="text-ink-soft">•</span>
            <span className="text-ink">{suggestion}</span>
          </li>
        ))}
      </ul>

      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          className="inline-flex items-center rounded-md bg-forest px-6 py-3 font-medium text-white transition hover:bg-forest/95"
          href={`/intake?address=${encodeURIComponent(originalAddress)}`}
        >
          Edit address
        </Link>
        <button
          className="inline-flex cursor-not-allowed items-center rounded-md border border-ink/15 bg-white px-6 py-3 font-medium text-ink-soft"
          disabled
          type="button"
        >
          Enter EHR code instead
        </button>
      </div>
    </section>
  );
}
