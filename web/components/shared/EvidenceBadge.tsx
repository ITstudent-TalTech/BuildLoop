"use client";

import { useEffect, useId, useRef, useState } from "react";

export type Confidence = "high" | "medium" | "low";

export interface EvidenceBadgeProps {
  confidence: Confidence;
  sourcePage?: number;
  sourceLabel?: string;
  sourceUrl?: string;
  lastUpdated?: string;
  className?: string;
}

const confidenceLabels: Record<Confidence, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("et-EE", {
    dateStyle: "medium",
  }).format(date);
}

function ConfidenceCue({ confidence }: { confidence: Confidence }) {
  if (confidence === "high") {
    return (
      <span className="inline-flex size-4 items-center justify-center rounded-full bg-forest-light text-[10px] font-bold leading-none text-forest">
        ✓
      </span>
    );
  }

  if (confidence === "medium") {
    return (
      <span className="inline-block size-4 rounded-full border-[1.5px] border-forest" />
    );
  }

  return (
    <span className="inline-block size-4 rounded-full border-[1.5px] border-ink-soft/70" />
  );
}

function SourceHeader({
  sourceLabel,
  sourcePage,
}: {
  sourceLabel?: string;
  sourcePage?: number;
}) {
  if (sourceLabel && sourcePage) {
    return <>From {sourceLabel}, page {sourcePage}</>;
  }

  if (sourceLabel) {
    return <>From {sourceLabel}</>;
  }

  if (sourcePage) {
    return <>From source, page {sourcePage}</>;
  }

  return null;
}

export default function EvidenceBadge({
  confidence,
  sourcePage,
  sourceLabel,
  sourceUrl,
  lastUpdated,
  className,
}: EvidenceBadgeProps) {
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const hasSourceData = Boolean(sourcePage || sourceLabel || sourceUrl);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    popoverRef.current?.focus();

    function handlePointerDown(event: PointerEvent) {
      const target = event.target as Node;

      if (
        popoverRef.current?.contains(target) ||
        triggerRef.current?.contains(target)
      ) {
        return;
      }

      setIsOpen(false);
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  return (
    <span className={["relative inline-flex", className].filter(Boolean).join(" ")}>
      <button
        aria-expanded={isOpen}
        aria-label={`${confidenceLabels[confidence]} confidence evidence`}
        className="inline-flex size-5 items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-forest/40"
        onClick={() => setIsOpen((current) => !current)}
        onMouseEnter={() => setIsOpen(true)}
        ref={triggerRef}
        type="button"
      >
        <ConfidenceCue confidence={confidence} />
      </button>

      {isOpen ? (
        <div
          aria-labelledby={titleId}
          className="absolute right-0 top-[calc(100%+8px)] z-30 w-[280px] rounded-lg border border-ink/10 bg-white p-3 text-left text-xs leading-5 text-ink shadow-[0_12px_30px_rgba(13,31,23,0.12)] outline-none"
          ref={popoverRef}
          role="dialog"
          tabIndex={-1}
        >
          {hasSourceData ? (
            <>
              <p className="font-medium text-ink" id={titleId}>
                <SourceHeader sourceLabel={sourceLabel} sourcePage={sourcePage} />
              </p>
              <div className="mt-2 flex items-center gap-2 text-ink-soft">
                <ConfidenceCue confidence={confidence} />
                <span>
                  Confidence:{" "}
                  <span className="font-medium text-ink">
                    {confidenceLabels[confidence]}
                  </span>
                </span>
              </div>
              {lastUpdated ? (
                <p className="mt-1 text-ink-soft">
                  Last updated {formatDate(lastUpdated)}
                </p>
              ) : null}
              {sourceUrl ? (
                <a
                  className="mt-2 inline-flex text-sm font-medium text-forest underline-offset-4 hover:underline"
                  href={sourceUrl}
                >
                  View source
                </a>
              ) : null}
            </>
          ) : (
            <p className="font-medium text-ink" id={titleId}>
              No source — manually entered
            </p>
          )}
        </div>
      ) : null}
    </span>
  );
}
