"use client";

import type { AppliedEdit } from "./ReviewContext";

interface PublishBarProps {
  edits: AppliedEdit[];
  onDiscard: () => void;
  onPublishClick: () => void;
}

export default function PublishBar({
  edits,
  onDiscard,
  onPublishClick,
}: PublishBarProps) {
  if (edits.length === 0) {
    return null;
  }

  return (
    <aside
      aria-label="Publish review edits"
      className="sticky bottom-0 z-20 border-t border-ink/10 bg-white shadow-[0_-8px_24px_rgba(13,31,23,0.08)]"
    >
      <div className="mx-auto flex max-w-4xl flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <div className="text-sm text-ink">
          {edits.length} {edits.length === 1 ? "edit" : "edits"} ready to publish
        </div>
        <div className="flex flex-wrap items-center justify-end gap-3">
          <button
            className="text-sm text-ink-soft underline-offset-2 hover:underline"
            onClick={onDiscard}
            type="button"
          >
            <span className="hidden sm:inline">Discard all edits</span>
            <span className="sm:hidden">Discard</span>
          </button>
          <button
            className="rounded-md bg-forest px-5 py-2.5 text-sm font-medium text-white"
            onClick={onPublishClick}
            type="button"
          >
            Publish passport →
          </button>
        </div>
      </div>
    </aside>
  );
}
