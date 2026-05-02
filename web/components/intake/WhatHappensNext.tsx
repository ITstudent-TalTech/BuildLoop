const steps = [
  {
    number: "01",
    title: "Enter address",
    body: "Any Estonian street address. Apartment number isn't needed — passports are issued per building.",
  },
  {
    number: "02",
    title: "We resolve it to a building",
    body: "BUILDLoop matches your address to its EHR code and pulls the public construction register record.",
  },
  {
    number: "03",
    title: "Review and publish",
    body: "You review the draft, attach photos and condition notes, then publish a versioned passport.",
  },
];

export default function WhatHappensNext() {
  return (
    <section>
      <h2 className="mb-4 font-mono text-xs font-semibold uppercase tracking-wider text-ink-soft">
        WHAT HAPPENS NEXT
      </h2>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {steps.map((step) => (
          <article
            className="rounded-lg border border-ink-soft/10 bg-white p-5"
            key={step.number}
          >
            <p className="font-mono text-xs font-medium text-ink-soft">
              {step.number}
            </p>
            <h3 className="mt-2 text-base font-semibold text-ink">
              {step.title}
            </h3>
            <p className="mt-1 text-sm leading-relaxed text-ink-soft">
              {step.body}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
