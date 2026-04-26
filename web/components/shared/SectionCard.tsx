"use client";

import { type ReactNode, useId, useState } from "react";

interface SectionCardProps {
  title: string;
  fieldsPopulated: number;
  fieldsTotal: number;
  confidenceLabel: "high" | "medium" | "low";
  defaultExpanded?: boolean;
  children: ReactNode;
}

export default function SectionCard({
  title,
  fieldsPopulated,
  fieldsTotal,
  confidenceLabel,
  defaultExpanded = true,
  children,
}: SectionCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const bodyId = useId();

  return (
    <section className="overflow-hidden rounded-lg border border-ink/10 bg-white">
      <header className="flex items-center justify-between gap-5 p-5">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold leading-6 text-ink">{title}</h2>
          <p className="mt-1 text-sm leading-5 text-ink-soft">
            {fieldsPopulated} of {fieldsTotal} fields populated ·{" "}
            {confidenceLabel} confidence
          </p>
        </div>
        <button
          aria-controls={bodyId}
          aria-expanded={isExpanded}
          aria-label={`${isExpanded ? "Collapse" : "Expand"} ${title}`}
          className="inline-flex size-8 shrink-0 items-center justify-center rounded-md border border-ink/10 bg-white text-ink-soft transition-colors hover:bg-surface focus:outline-none focus-visible:ring-2 focus-visible:ring-forest/40"
          onClick={() => setIsExpanded((current) => !current)}
          type="button"
        >
          <span
            aria-hidden
            className={[
              "text-sm leading-none transition-transform duration-200",
              isExpanded ? "rotate-0" : "rotate-180",
            ].join(" ")}
          >
            ^
          </span>
        </button>
      </header>

      <div
        className={[
          "grid transition-[grid-template-rows] duration-200 ease-out",
          isExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
        ].join(" ")}
        id={bodyId}
      >
        <div className="min-h-0 overflow-hidden">
          <div className="px-5 pb-5">{children}</div>
        </div>
      </div>
    </section>
  );
}
