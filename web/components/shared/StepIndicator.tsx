"use client";

type StepIndicatorProps = {
  currentStep: 0 | 1 | 2 | 3 | 4;
};

const steps = ["ADDRESS", "RESOLUTION", "DRAFT", "PUBLISHED"] as const;

export default function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <nav aria-label="Passport progress">
      <ol className="flex flex-wrap items-center gap-2 font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-soft">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;

          return (
            <li className="flex items-center gap-2" key={step}>
              {index > 0 ? (
                <span
                  aria-hidden
                  className={[
                    "hidden h-px w-6 shrink-0 sm:inline-block",
                    stepNumber <= currentStep ? "bg-forest/35" : "bg-ink-soft/20",
                  ].join(" ")}
                />
              ) : null}

              <span
                aria-current={isCurrent ? "step" : undefined}
                className={[
                  "inline-flex items-center gap-1.5",
                  isCurrent
                    ? "font-semibold text-forest"
                    : isCompleted
                      ? "text-ink-soft"
                      : "text-ink-soft/65",
                ].join(" ")}
              >
                <span
                  className={[
                    "inline-flex size-4 shrink-0 items-center justify-center rounded-[3px] text-[10px] font-bold leading-none",
                    isCompleted
                      ? "bg-forest-light text-forest"
                      : isCurrent
                        ? "bg-forest text-white"
                        : "border border-ink/20 bg-white text-ink-soft/75",
                  ].join(" ")}
                >
                  {isCompleted ? (
                    <span aria-hidden className="text-[10px] leading-none">
                      ✓
                    </span>
                  ) : (
                    <span>{stepNumber}</span>
                  )}
                </span>
                {step}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
