import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import StickyIdentityStrip from "@/components/passport/StickyIdentityStrip";
import EditablePassportLayout from "@/components/review/EditablePassportLayout";
import TopBar from "@/components/shared/TopBar";
import { ApiError, getPassportDraft } from "@/lib/api";
import type { PassportDraft } from "@/lib/api";

export const metadata: Metadata = {
  title: "Review and edit",
};

function ReviewIntro() {
  return (
    <header>
      <h1 className="text-3xl font-semibold text-ink">Review and edit</h1>
      <p className="mt-2 max-w-prose text-ink-soft">
        Verify each section. Click any field to correct it. Photos and condition
        notes can be added per building part. When you&apos;re satisfied, publish
        a versioned passport.
      </p>
    </header>
  );
}

function PassportLoadError({ projectId }: { projectId: string }) {
  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <section className="mx-auto max-w-4xl px-5 py-8 sm:px-8">
        <h1 className="text-3xl font-semibold text-ink">
          We couldn&apos;t load your passport draft
        </h1>
        <p className="mt-2 max-w-prose text-ink-soft">
          Something went wrong fetching your draft. Try again, or go back to
          start over.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Link
            className="inline-flex items-center rounded-md bg-forest px-6 py-3 font-medium text-white transition hover:bg-forest/95"
            href={`/passport/${projectId}/review`}
          >
            Retry
          </Link>
          <Link
            className="inline-flex items-center rounded-md border border-ink/15 bg-white px-6 py-3 font-medium text-ink transition hover:bg-surface"
            href="/intake"
          >
            Start over
          </Link>
        </div>
      </section>
    </main>
  );
}

export default async function PassportReviewPage({
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
      notFound();
    }

    return <PassportLoadError projectId={id} />;
  }

  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <StickyIdentityStrip draft={draft} />
      <section className="mx-auto max-w-4xl px-5 py-8 sm:px-8">
        <ReviewIntro />
        <EditablePassportLayout initialDraft={draft} projectId={id} />
      </section>
    </main>
  );
}
