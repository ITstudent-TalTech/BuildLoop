import StepIndicator from "@/components/shared/StepIndicator";
import TopBar from "@/components/shared/TopBar";

export default function PassportLoading() {
  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <section className="mx-auto max-w-4xl px-5 py-8 sm:px-8">
        <StepIndicator currentStep={3} />
        <div className="mt-16 flex flex-col items-center text-center">
          <div
            aria-hidden="true"
            className="size-8 animate-spin rounded-full border-2 border-forest-light border-t-forest"
          />
          <h1 className="mt-6 text-2xl font-semibold text-ink">
            Generating passport draft…
          </h1>
          <p className="mt-3 max-w-prose text-ink-soft">
            Fetching the construction register record and assembling your
            passport draft. This usually takes 5–10 seconds for a building not
            seen before.
          </p>
        </div>
      </section>
    </main>
  );
}
