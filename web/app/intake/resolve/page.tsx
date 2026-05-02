import Link from "next/link";
import { redirect } from "next/navigation";
import CandidateList from "@/components/resolve/CandidateList";
import RetryResolveButton from "@/components/resolve/RetryResolveButton";
import UnresolvedState from "@/components/resolve/UnresolvedState";
import StepIndicator from "@/components/shared/StepIndicator";
import TopBar from "@/components/shared/TopBar";
import { resolveAddress } from "@/lib/api";
import type { ResolutionResponse } from "@/lib/api";

type SearchParams = {
  run?: string;
  intake?: string;
  address?: string;
};

function PageHeader({
  originalAddress,
  status,
}: {
  originalAddress: string;
  status: "ambiguous" | "unresolved";
}) {
  const isAmbiguous = status === "ambiguous";

  return (
    <header>
      <p className="font-mono text-xs font-semibold uppercase tracking-wider text-ink-soft">
        YOU SEARCHED FOR
      </p>
      <div className="mt-2 inline-flex rounded-md border border-ink/10 bg-white px-3 py-1.5 font-mono text-sm text-ink">
        {originalAddress}
      </div>
      <h1 className="mt-6 text-3xl font-semibold text-ink">
        {isAmbiguous
          ? "We found a few possible matches"
          : "We couldn't match this address"}
      </h1>
      <p className="mt-2 text-ink-soft">
        {isAmbiguous
          ? "Pick the building you mean. We'll fetch its register record next."
          : "The address didn't match anything in the Estonian construction register. This usually means a typo, a very new building, or an unusual format."}
      </p>
    </header>
  );
}

function ResolveErrorState({ intakeId }: { intakeId: string }) {
  return (
    <section>
      <h1 className="text-3xl font-semibold text-ink">Something went wrong</h1>
      <p className="mt-2 max-w-prose text-ink-soft">
        We couldn&apos;t reach the construction register. Try again, or go back
        and edit your address.
      </p>
      <div className="mt-8 flex flex-wrap items-start gap-3">
        <RetryResolveButton intakeId={intakeId} />
        <Link
          className="inline-flex items-center rounded-md border border-ink/15 bg-white px-6 py-3 font-medium text-ink transition hover:bg-surface"
          href="/intake"
        >
          Edit address
        </Link>
      </div>
    </section>
  );
}

export default async function ResolvePage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const intakeId = params.intake;
  const originalAddress = params.address ?? "Lai 1, 10133 Tallinn";

  if (!intakeId) {
    redirect("/intake");
  }

  let resolution: ResolutionResponse;

  try {
    resolution = await resolveAddress(intakeId);
  } catch {
    return (
      <main className="min-h-screen bg-surface">
        <TopBar />
        <section className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
          <StepIndicator currentStep={2} />
          <div className="mt-8">
            <ResolveErrorState intakeId={intakeId} />
          </div>
        </section>
      </main>
    );
  }

  if (resolution.status === "resolved") {
    redirect("/intake?notice=resolution-already-complete");
  }

  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <section className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
        <StepIndicator currentStep={2} />
        <div className="mt-8">
          <PageHeader
            originalAddress={originalAddress}
            status={resolution.status}
          />
          {resolution.status === "ambiguous" ? (
            <CandidateList
              candidates={resolution.candidates}
              originalAddress={originalAddress}
              resolutionRunId={resolution.resolution_run_id}
            />
          ) : (
            <UnresolvedState originalAddress={originalAddress} />
          )}
        </div>
      </section>
    </main>
  );
}
