export default function ResolvingSkeleton() {
  return (
    <div className="mt-8 space-y-3" aria-label="Loading candidate matches">
      {[0, 1, 2].map((item) => (
        <div
          className="rounded-lg border border-ink-soft/10 bg-white p-5"
          key={item}
        >
          <div className="h-5 w-3/4 animate-pulse rounded bg-ink-soft/10" />
          <div className="mt-3 h-3 w-32 animate-pulse rounded bg-ink-soft/10" />
          <div className="mt-5 h-2 w-24 animate-pulse rounded bg-forest-light" />
        </div>
      ))}
    </div>
  );
}
