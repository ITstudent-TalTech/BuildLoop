import Link from "next/link";
import CandidateCard from "./CandidateCard";
import type { ResolutionCandidate } from "@/lib/api";

interface CandidateListProps {
  candidates: ResolutionCandidate[];
  resolutionRunId: string;
  originalAddress?: string;
}

export default function CandidateList({
  candidates,
  resolutionRunId,
  originalAddress = "",
}: CandidateListProps) {
  return (
    <>
      <div className="mt-8 space-y-3">
        {candidates.map((candidate, index) => (
          <CandidateCard
            candidate={candidate}
            isPrimary={index === 0}
            key={candidate.ehr_code}
            resolutionRunId={resolutionRunId}
          />
        ))}
      </div>
      <div className="mt-6">
        <Link
          className="text-sm text-ink-soft underline-offset-2 hover:underline"
          href={`/intake?address=${encodeURIComponent(originalAddress)}`}
        >
          None of these — edit address
        </Link>
      </div>
    </>
  );
}
