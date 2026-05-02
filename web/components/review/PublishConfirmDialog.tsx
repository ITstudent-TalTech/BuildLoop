"use client";

import { useEffect, useRef } from "react";
import type { AppliedEdit } from "./ReviewContext";

interface PublishConfirmDialogProps {
  edits: AppliedEdit[];
  isPublishing: boolean;
  onCancel: () => void;
  onPublish: () => void;
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "missing";
  if (Array.isArray(value)) return value.join(" · ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export default function PublishConfirmDialog({
  edits,
  isPublishing,
  onCancel,
  onPublish,
}: PublishConfirmDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    cancelRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onCancel();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 z-40 bg-ink/30 px-5 backdrop-blur-sm">
      <div
        aria-modal="true"
        className="mx-auto mt-20 max-w-lg rounded-lg bg-white p-6 shadow-xl"
        role="dialog"
      >
        <h2 className="text-xl font-semibold text-ink">Publish this passport?</h2>
        <p className="mt-2 text-sm leading-6 text-ink-soft">
          You&apos;re about to publish a versioned passport with {edits.length}{" "}
          manual edits. Once published, this version is immutable. You can still
          create new versions later.
        </p>
        <div className="mt-5 max-h-56 space-y-3 overflow-y-auto">
          {edits.map((edit) => (
            <div className="border-t border-ink/10 pt-3" key={edit.target_field_path}>
              <p className="font-mono text-xs text-ink">
                {edit.target_field_path} → {formatValue(edit.new_value)}
              </p>
              <p className="mt-1 text-xs text-ink-soft">Reason: {edit.reason}</p>
            </div>
          ))}
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="text-sm text-ink-soft underline-offset-2 hover:underline"
            onClick={onCancel}
            ref={cancelRef}
            type="button"
          >
            Cancel
          </button>
          <button
            className="rounded-md bg-forest px-5 py-2.5 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-forest/45"
            disabled={isPublishing}
            onClick={onPublish}
            type="button"
          >
            {isPublishing ? "Publishing…" : "Publish"}
          </button>
        </div>
      </div>
    </div>
  );
}
