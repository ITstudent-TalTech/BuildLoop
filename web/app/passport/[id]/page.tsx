import type { Metadata } from "next";
import Link from "next/link";
import BuildingPartsSection from "@/components/passport/BuildingPartsSection";
import BuildingProfileSection from "@/components/passport/BuildingProfileSection";
import DraftActions from "@/components/passport/DraftActions";
import IdentitySection from "@/components/passport/IdentitySection";
import LocationSection from "@/components/passport/LocationSection";
import PassportRetryButton from "@/components/passport/PassportRetryButton";
import QualitySection from "@/components/passport/QualitySection";
import StickyIdentityStrip from "@/components/passport/StickyIdentityStrip";
import StructuralSystemsSection from "@/components/passport/StructuralSystemsSection";
import TechnicalSystemsSection from "@/components/passport/TechnicalSystemsSection";
import TopBar from "@/components/shared/TopBar";
import { ApiError, generatePassportDraft, getPassportDraft } from "@/lib/api";
import type { PassportDraft } from "@/lib/api";

export const metadata: Metadata = {
  title: "Passport draft",
};

function PageIntro() {
  return (
    <header>
      <h1 className="mt-6 text-3xl font-semibold text-ink">Passport draft</h1>
      <p className="mt-2 max-w-prose text-ink-soft">
        This is what we extracted from the construction register. Review each
        section before publishing.
      </p>
    </header>
  );
}

function PassportGenerationError({
  projectId,
  error,
}: {
  projectId: string;
  error: unknown;
}) {
  const message =
    error instanceof ApiError
      ? error.message
      : error instanceof Error
        ? error.message
        : "An unexpected error occurred while building the passport draft.";

  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <section className="mx-auto max-w-4xl px-5 py-8 sm:px-8">
        <h1 className="mt-6 text-3xl font-semibold text-ink">
          We couldn&apos;t generate your passport
        </h1>
        <p className="mt-2 max-w-prose text-ink-soft">
          The pipeline failed to build a draft from the construction register
          data.
        </p>
        <p className="mt-3 rounded-md border border-ink/10 bg-white px-4 py-3 font-mono text-sm text-ink-soft">
          {message}
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <PassportRetryButton />
          <Link
            className="inline-flex items-center rounded-md border border-ink/15 bg-white px-6 py-3 font-medium text-ink transition hover:bg-surface"
            href="/intake"
          >
            Start over
          </Link>
        </div>
        <p className="mt-4 font-mono text-xs text-ink-soft">Project {projectId}</p>
      </section>
    </main>
  );
}

function PassportLoadError({ projectId }: { projectId: string }) {
  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <section className="mx-auto max-w-4xl px-5 py-8 sm:px-8">
        <h1 className="mt-6 text-3xl font-semibold text-ink">
          We couldn&apos;t load your passport draft
        </h1>
        <p className="mt-2 max-w-prose text-ink-soft">
          Something went wrong fetching your draft. Try again, or go back to
          start over.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <PassportRetryButton />
          <Link
            className="inline-flex items-center rounded-md border border-ink/15 bg-white px-6 py-3 font-medium text-ink transition hover:bg-surface"
            href="/intake"
          >
            Start over
          </Link>
        </div>
        <p className="mt-4 font-mono text-xs text-ink-soft">
          Project {projectId}
        </p>
      </section>
    </main>
  );
}

export default async function PassportDraftPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let draft: PassportDraft;

  try {
    draft = await getPassportDraft(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      // No draft yet — likely a freshly-resolved project. Run the pipeline now.
      // The pipeline is idempotent (fetch dedup'd, parse skipped if done,
      // projection upserts), so calling it here on refresh is safe.
      try {
        const genResult = await generatePassportDraft(id);
        draft = genResult.draft ?? await getPassportDraft(id);
      } catch (genErr) {
        return <PassportGenerationError projectId={id} error={genErr} />;
      }
    } else {
      return <PassportLoadError projectId={id} />;
    }
  }

  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <StickyIdentityStrip draft={draft} />
      <section className="mx-auto max-w-4xl px-5 py-8 sm:px-8">
        <PageIntro />
        <DraftActions draftId={draft.passport_draft_id} projectId={id} />
        <div className="mt-8 space-y-6">
          <IdentitySection identity={draft.identity} />
          <BuildingProfileSection profile={draft.building_profile} />
          <StructuralSystemsSection systems={draft.structural_systems} />
          <TechnicalSystemsSection systems={draft.technical_systems} />
          <LocationSection location={draft.location} />
          <BuildingPartsSection buildingParts={draft.building_parts} />
          <QualitySection quality={draft.quality} />
        </div>
      </section>
    </main>
  );
}
