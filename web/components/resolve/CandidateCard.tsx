"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { selectCandidate } from "@/lib/api";
import type { ResolutionCandidate } from "@/lib/api";

interface CandidateCardProps {
  candidate: ResolutionCandidate;
  resolutionRunId: string;
  isPrimary: boolean;
}

function confidencePercentage(score: number) {
  return Math.round(score <= 1 ? score * 100 : score);
}

function ConfidenceBar({ percentage }: { percentage: number }) {
  return (
    <div
      aria-hidden="true"
      className="h-1 w-[60px] overflow-hidden rounded-full bg-forest-light"
    >
      <div
        className="h-full rounded-full bg-forest"
        style={{ width: `${Math.max(0, Math.min(100, percentage))}%` }}
      />
    </div>
  );
}

function addressAliases(normalizedAddress: string) {
  if (!normalizedAddress.includes("//")) {
    return [];
  }

  const citySuffix = normalizedAddress.includes(",")
    ? normalizedAddress.slice(normalizedAddress.lastIndexOf(","))
    : "";

  return normalizedAddress
    .split("//")
    .map((part, index) => {
      const trimmed = part.trim();
      return index === 0 ? trimmed.split(",").at(-1)?.trim() ?? trimmed : trimmed;
    })
    .map((part) => part.replace(citySuffix, "").trim())
    .filter(Boolean);
}

export default function CandidateCard({
  candidate,
  resolutionRunId,
  isPrimary,
}: CandidateCardProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const percentage = confidencePercentage(candidate.confidence_score);
  const aliases = addressAliases(candidate.normalized_address);

  async function handleSelect() {
    setIsLoading(true);
    setError(null);

    try {
      await selectCandidate(resolutionRunId, candidate.ehr_code);
      router.push("/passport/demo-project-id");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Selection failed";
      setError(message);
      setIsLoading(false);
    }
  }

  return (
    <button
      aria-busy={isLoading}
      className="group w-full rounded-lg border border-ink-soft/15 bg-white p-5 text-left transition-colors hover:border-forest hover:shadow-sm disabled:cursor-not-allowed disabled:opacity-60"
      disabled={isLoading}
      onClick={() => {
        void handleSelect();
      }}
      type="button"
    >
      {isPrimary ? (
        <span
          aria-label="Primary match"
          className="mb-2 inline-block rounded bg-forest-light px-2 py-1 text-xs font-medium text-forest md:float-right md:mb-0 md:ml-4"
        >
          PRIMARY MATCH
        </span>
      ) : null}

      <div className="text-base font-semibold leading-6 text-ink">
        {candidate.normalized_address}
      </div>
      <div className="mt-1 font-mono text-xs text-ink-soft">
        EHR {candidate.ehr_code}
      </div>

      {aliases.length > 0 ? (
        <div className="mt-2 text-xs text-ink-soft">
          <span className="mr-2 uppercase tracking-wider">Also known as:</span>
          {aliases.map((alias, index) => (
            <span key={alias}>
              {index > 0 ? <span className="mx-1.5">·</span> : null}
              {alias}
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-3 flex items-center gap-2">
        <ConfidenceBar percentage={percentage} />
        <span
          aria-label={`${percentage} percent confidence`}
          className="text-xs tabular-nums text-ink-soft"
        >
          {percentage}% confidence
        </span>
      </div>

      {isLoading ? (
        <div className="mt-3 text-sm text-ink-soft">Selecting building…</div>
      ) : null}

      {error ? (
        <div className="mt-3 text-sm text-red-700" role="alert">
          {error}
        </div>
      ) : null}
    </button>
  );
}
