import StepIndicator from "@/components/shared/StepIndicator";
import type { PassportDraft } from "@/lib/api";

interface StickyIdentityStripProps {
  draft: PassportDraft;
}

function DraftQualityPill({ quality }: { quality: PassportDraft["quality"] }) {
  return (
    <div className="inline-flex w-full flex-wrap items-center rounded-md border border-ink/10 bg-white px-3 py-1.5 text-xs text-ink-soft sm:w-auto">
      <span className="font-mono font-semibold uppercase tracking-[0.06em]">
        DRAFT QUALITY:
      </span>
      <span className="ml-2 font-mono tabular-nums text-ink">
        {Math.round(quality.schema_completeness_score)}%
      </span>
      <span className="ml-1">complete ·</span>
      <span className="ml-1 font-mono tabular-nums text-ink">
        {Math.round(quality.confidence_score)}%
      </span>
      <span className="ml-1">confidence</span>
    </div>
  );
}

export default function StickyIdentityStrip({ draft }: StickyIdentityStripProps) {
  return (
    <header
      className="sticky top-0 z-10 border-b border-ink-soft/10 bg-surface/95 backdrop-blur-sm"
      role="banner"
    >
      <div className="mx-auto max-w-4xl px-5 py-4 sm:px-8">
        <StepIndicator currentStep={3} />
        <div className="mt-3 flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="break-words text-lg font-semibold text-ink">
              {draft.identity.normalized_address.value}
            </div>
            <div className="mt-0.5 font-mono text-xs text-ink-soft">
              EHR {draft.identity.ehr_code.value}
            </div>
          </div>
          <DraftQualityPill quality={draft.quality} />
        </div>
      </div>
    </header>
  );
}
