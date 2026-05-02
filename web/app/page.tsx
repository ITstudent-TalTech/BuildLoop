import Link from "next/link";
import StepIndicator from "@/components/shared/StepIndicator";
import TopBar from "@/components/shared/TopBar";

export default function Home() {
  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <section className="mx-auto max-w-3xl px-5 py-16 sm:py-24">
        <p className="font-mono text-xs font-medium uppercase tracking-[0.08em] text-ink-soft">
          BUILDLOOP · MVP DEMO
        </p>
        <h1 className="mt-5 max-w-2xl text-4xl font-semibold leading-tight text-ink sm:text-5xl">
          Building passports for the circular economy
        </h1>
        <p className="mt-4 max-w-prose text-lg leading-8 text-ink-soft">
          BUILDLoop generates digital material passports for buildings in
          Estonia using public construction register data. Document what&apos;s
          in your building before demolition or renovation — so the materials
          can be reused.
        </p>
        <Link
          className="mt-8 inline-flex items-center gap-2 rounded-md bg-forest px-6 py-3 font-medium text-white transition hover:bg-forest/95"
          href="/intake"
        >
          Start a passport
          <span aria-hidden="true">→</span>
        </Link>

        <div className="mt-12">
          <p className="mb-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-ink-soft">
            WHAT YOU&apos;LL DO
          </p>
          <StepIndicator currentStep={0} />
        </div>

        <Link
          className="mt-10 inline-flex text-sm text-ink-soft underline-offset-2 hover:underline"
          href="/intake"
        >
          Already have a passport in progress?
        </Link>
      </section>
    </main>
  );
}
