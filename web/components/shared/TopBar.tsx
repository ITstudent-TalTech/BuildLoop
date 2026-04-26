function LanguageSwitcher() {
  const languages = ["ET", "EN"] as const;

  return (
    <div
      aria-label="Language"
      className="inline-flex overflow-hidden rounded-md border border-ink/10 font-mono text-[11px] font-semibold uppercase leading-none"
      role="group"
    >
      {languages.map((language) => {
        const isActive = language === "ET";

        return (
          <button
            aria-pressed={isActive}
            className={[
              "min-w-8 px-2.5 py-2 transition-colors",
              isActive
                ? "bg-ink text-white"
                : "bg-white text-ink-soft hover:bg-surface",
            ].join(" ")}
            key={language}
            type="button"
          >
            {language}
          </button>
        );
      })}
    </div>
  );
}

function UserMenuPlaceholder() {
  return (
    <button
      className="inline-flex h-8 items-center gap-2 rounded-md border border-ink/10 bg-white py-1 pl-1.5 pr-2.5 text-sm text-ink transition-colors hover:bg-surface"
      type="button"
    >
      <span className="flex size-5 items-center justify-center rounded-full bg-forest-light text-[10px] font-semibold text-forest">
        MK
      </span>
      <span className="hidden text-ink-soft sm:inline">Mart Kask</span>
      <span aria-hidden className="text-[10px] text-ink-soft">
        v
      </span>
    </button>
  );
}

export default function TopBar() {
  return (
    <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-ink/10 bg-white px-4 sm:px-7">
      <div className="flex min-w-0 items-center gap-3.5">
        <div className="text-[17px] font-bold leading-none text-ink">
          BUILD<span className="text-forest">Loop</span>
        </div>
        <span className="rounded border border-ink/10 bg-surface px-2 py-1 font-mono text-[10.5px] font-medium uppercase tracking-[0.08em] text-ink-soft">
          V0.1 &middot; MVP
        </span>
      </div>

      <div className="flex items-center gap-3">
        <LanguageSwitcher />
        <span aria-hidden className="hidden h-5 w-px bg-ink/10 sm:block" />
        <UserMenuPlaceholder />
      </div>
    </header>
  );
}
