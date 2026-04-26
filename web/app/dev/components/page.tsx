import FieldRow from "@/components/shared/FieldRow";
import SectionCard from "@/components/shared/SectionCard";
import StepIndicator from "@/components/shared/StepIndicator";
import TopBar from "@/components/shared/TopBar";
import { getPassportDraft } from "@/lib/api";

const states = [1, 2, 3, 4] as const;

const highEvidence = {
  confidence: "high" as const,
  sourceLabel: "EHR PDF",
  sourcePage: 1,
  lastUpdated: "2026-04-26",
};

export default async function ComponentReviewPage() {
  const draft = await getPassportDraft("demo-project-id");
  const heatedArea = draft.building_profile.heated_area_m2;

  return (
    <main className="min-h-screen bg-surface text-ink">
      <TopBar />

      <section className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-5 py-10 sm:px-8">
        <div>
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.08em] text-ink-soft">
            Component review
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-ink">
            Shared BUILDLoop chrome
          </h1>
        </div>

        <div className="border-y border-ink/10 bg-surface py-6">
          <div className="px-5 sm:px-6">
            <TopBar />
          </div>
        </div>

        <div className="grid gap-4">
          {states.map((state) => (
            <section
              className="border-y border-ink/10 bg-surface px-5 py-5 sm:px-6"
              key={state}
            >
              <p className="mb-4 font-mono text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-soft">
                Step {state}
              </p>
              <StepIndicator currentStep={state} />
            </section>
          ))}
        </div>

        <section className="mt-6 flex flex-col gap-4">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-[0.08em] text-ink-soft">
              Data primitives
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-ink">
              Passport field review
            </h2>
          </div>

          <SectionCard
            confidenceLabel="high"
            fieldsPopulated={5}
            fieldsTotal={5}
            title="Identity"
          >
            <FieldRow
              evidence={highEvidence}
              isMono
              label="EHR code"
              value="101035685"
            />
            <FieldRow
              evidence={highEvidence}
              label="Normalized address"
              value="Harju maakond, Tallinn, Kesklinna linnaosa, Lai tn 1 // Nunne tn 4"
            />
            <FieldRow
              evidence={highEvidence}
              label="Address aliases"
              value="Lai tn 1 · Nunne tn 4"
            />
            <FieldRow evidence={highEvidence} label="Country" value="Estonia" />
            <FieldRow
              evidence={highEvidence}
              label="Original input"
              value="Lai 1, 10133 Tallinn"
            />
          </SectionCard>

          <SectionCard
            confidenceLabel="medium"
            fieldsPopulated={13}
            fieldsTotal={15}
            title="Building profile"
          >
            <FieldRow
              evidence={{ ...highEvidence, confidence: "high" }}
              label="Building type"
              value="Residential"
            />
            <FieldRow
              evidence={{
                confidence: "medium",
                sourceLabel: "EHR PDF",
                sourcePage: 3,
                lastUpdated: "2026-04-26",
              }}
              isMono
              label="Heated area"
              unit="m²"
              value={1648}
            />
            <FieldRow
              evidence={{
                confidence: "medium",
                sourceLabel: "EHR PDF",
                sourcePage: 3,
                lastUpdated: "2026-04-26",
              }}
              isMono
              label="Footprint area"
              unit="m²"
              value={412}
            />
            <FieldRow
              evidence={{
                confidence: "low",
                sourceLabel: "EHR PDF",
                sourcePage: 1,
              }}
              label="Building name"
              value={null}
            />
            <FieldRow
              evidence={{ ...highEvidence, confidence: "high", sourcePage: 2 }}
              isMono
              label="Floors above ground"
              value={4}
            />
            <FieldRow label="Public-use area" unit="m²" value={null} />
            <FieldRow
              evidence={{
                confidence: "low",
                sourceLabel: "EHR PDF",
                sourcePage: 4,
                sourceUrl: "#",
                lastUpdated: "2026-04-26",
              }}
              isMono
              label="Volume"
              unit="m³"
              value={5860}
            />
          </SectionCard>

          <SectionCard
            confidenceLabel="high"
            defaultExpanded={false}
            fieldsPopulated={7}
            fieldsTotal={7}
            title="Quality"
          >
            <FieldRow
              evidence={{
                confidence: "high",
                sourceLabel: "BUILDLoop validation",
                lastUpdated: "2026-04-26",
              }}
              label="Completeness check"
              value="All required identity fields resolved"
            />
          </SectionCard>
        </section>

        <section className="mt-6 flex flex-col gap-4">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-[0.08em] text-ink-soft">
              API mocks smoke test
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-ink">
              Draft payload sample
            </h2>
          </div>
          <pre className="overflow-x-auto rounded-lg border border-ink/10 bg-white p-5 font-mono text-xs leading-5 text-ink">
            {JSON.stringify(heatedArea, null, 2)}
          </pre>
        </section>
      </section>
    </main>
  );
}
