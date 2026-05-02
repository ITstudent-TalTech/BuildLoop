import IntakeForm from "@/components/intake/IntakeForm";
import WhatHappensNext from "@/components/intake/WhatHappensNext";
import StepIndicator from "@/components/shared/StepIndicator";
import TopBar from "@/components/shared/TopBar";

export default function IntakePage() {
  return (
    <main className="min-h-screen bg-surface">
      <TopBar />
      <section className="mx-auto max-w-2xl px-5 py-12 sm:px-8">
        <StepIndicator currentStep={1} />
        <h1 className="mt-8 text-3xl font-semibold text-ink">
          Create a building passport
        </h1>
        <p className="mt-3 max-w-prose text-ink-soft">
          Enter the address of the building you want to assess. We&apos;ll
          resolve it against the Estonian construction register (EHR) and
          prepare a draft passport for review.
        </p>
        <div className="mt-8">
          <IntakeForm />
        </div>
        <div className="mt-12">
          <WhatHappensNext />
        </div>
      </section>
    </main>
  );
}
