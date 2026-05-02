import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import SharePassportLink from "@/components/published/SharePassportLink";
import StepIndicator from "@/components/shared/StepIndicator";
import TopBar from "@/components/shared/TopBar";
import { ApiError, getPassportDraft } from "@/lib/api";
import type { PassportDraft } from "@/lib/api";

export const metadata = {
  title: "Passport published",
};

type SearchParams = {
  version?: string;
};

function formatPublishedAt() {
  return new Intl.DateTimeFormat("et-EE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date());
}

function PublishedInfoCard({
  draft,
  version,
}: {
  draft: PassportDraft;
  version: string;
}) {
  return (
    <div className="mt-8 rounded-lg border border-ink/10 bg-white p-5 text-sm">
      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-[0.06em] text-ink-soft">
            Version
          </p>
          <p className="mt-1 font-mono text-ink">v{version}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.06em] text-ink-soft">
            Published
          </p>
          <p className="mt-1 text-ink">{formatPublishedAt()}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.06em] text-ink-soft">
            Building
          </p>
          <p className="mt-1 text-ink">{draft.identity.normalized_address.value}</p>
        </div>
      </div>
    </div>
  );
}

function PassportPublishedLoadError({ projectId }: { projectId: string }) {
  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <section className="mx-auto max-w-2xl px-5 py-12">
        <h1 className="text-3xl font-semibold text-ink">
          We couldn&apos;t load the published passport
        </h1>
        <p className="mt-2 text-ink-soft">
          The passport was published, but the confirmation details could not be
          fetched. You can still return to the passport view.
        </p>
        <Link
          className="mt-6 inline-flex rounded-md bg-forest px-6 py-3 font-medium text-white"
          href={`/passport/${projectId}`}
        >
          View passport
        </Link>
      </section>
    </main>
  );
}

export default async function PassportPublishedPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { id } = await params;
  const { version } = await searchParams;

  if (!version) {
    redirect(`/passport/${id}`);
  }

  let draft: PassportDraft;
  try {
    draft = await getPassportDraft(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }

    return <PassportPublishedLoadError projectId={id} />;
  }

  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <section className="mx-auto max-w-2xl px-5 py-12">
        <StepIndicator currentStep={4} />

        <div className="mt-10 text-center">
          <div className="mx-auto inline-flex size-16 items-center justify-center rounded-full bg-forest-light text-3xl font-semibold text-forest">
            ✓
          </div>
          <h1 className="mt-6 text-3xl font-semibold text-ink">
            Passport published
          </h1>
          <p className="mx-auto mt-3 max-w-prose text-ink-soft">
            Version {version} is now immutable and shareable. You can publish a
            new version at any time after making further edits.
          </p>
        </div>

        <PublishedInfoCard draft={draft} version={version} />

        <div className="mt-8 grid gap-3">
          <button
            className="rounded-md bg-ink-soft/15 px-6 py-3 font-medium text-ink-soft"
            disabled
            type="button"
          >
            Download PDF <span className="font-normal">(coming soon)</span>
          </button>
          <Link
            className="rounded-md bg-forest px-6 py-3 text-center font-medium text-white transition hover:bg-forest/95"
            href={`/passport/${id}`}
          >
            View passport
          </Link>
          <Link
            className="rounded-md border border-ink/10 bg-white px-6 py-3 text-center font-medium text-ink transition hover:border-forest"
            href="/intake"
          >
            Create another passport
          </Link>
        </div>

        <SharePassportLink />
      </section>
    </main>
  );
}
