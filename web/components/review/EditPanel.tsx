"use client";

import { useId, useState } from "react";
import type { EditableFieldValue, EditType, PendingEdit } from "./ReviewContext";

interface EditPanelProps {
  fieldPath: string;
  fieldValue: EditableFieldValue;
  onSave: (edit: PendingEdit) => Promise<void>;
  onCancel: () => void;
  label: string;
  unit?: string;
  isMono?: boolean;
}

function stringifyInitialValue(fieldValue: EditableFieldValue) {
  if (fieldValue.value === null || fieldValue.value === undefined) {
    return "";
  }

  if (Array.isArray(fieldValue.value)) {
    return fieldValue.value.join(" · ");
  }

  if (typeof fieldValue.value === "object") {
    return JSON.stringify(fieldValue.value);
  }

  return String(fieldValue.value);
}

function parseValueForType(value: string, fieldValue: EditableFieldValue) {
  if (typeof fieldValue.value === "number" || fieldValue.unit) {
    const parsed = Number.parseFloat(value);

    if (Number.isNaN(parsed)) {
      throw new Error("Enter a valid number");
    }

    return parsed;
  }

  return value;
}

export default function EditPanel({
  fieldPath,
  fieldValue,
  onSave,
  onCancel,
  label,
  unit,
  isMono = false,
}: EditPanelProps) {
  const inputId = useId();
  const reasonId = useId();
  const isArray = Array.isArray(fieldValue.value);
  const [newValue, setNewValue] = useState(stringifyInitialValue(fieldValue));
  const [editType, setEditType] = useState<EditType>(
    fieldValue.value === null ? "override" : "correction",
  );
  const [reason, setReason] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (!reason.trim() || isArray) {
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      await onSave({
        new_value: parseValueForType(newValue, fieldValue),
        reason: reason.trim(),
        edit_type: editType,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Save failed";
      setError(message);
      setIsSaving(false);
    }
  }

  return (
    <div
      aria-label={`Edit ${label}`}
      className="rounded-md border border-forest/20 bg-surface p-3"
      data-field-path={fieldPath}
      role="group"
    >
      {isArray ? (
        <p className="text-sm text-ink-soft">
          Editing this field type comes in a later release.
        </p>
      ) : (
        <>
          <label className="sr-only" htmlFor={inputId}>
            New value for {label}
          </label>
          <div className="flex items-center gap-2">
            <input
              className={[
                "w-full rounded-md border border-ink/15 bg-white px-3 py-2 text-sm text-ink outline-none focus:border-forest focus:ring-2 focus:ring-forest/15",
                isMono ? "font-mono" : "font-sans",
              ].join(" ")}
              id={inputId}
              onChange={(event) => setNewValue(event.target.value)}
              type={typeof fieldValue.value === "number" || unit ? "number" : "text"}
              value={newValue}
            />
            {unit ? <span className="text-sm text-ink-soft">{unit}</span> : null}
          </div>

          <fieldset className="mt-3">
            <legend className="sr-only">Edit type</legend>
            <div className="flex flex-wrap gap-2">
              {[
                ["correction", "Correction"],
                ["override", "Override"],
                ["confirmation", "Confirmation"],
              ].map(([value, text]) => (
                <label
                  className="inline-flex items-center gap-1.5 rounded border border-ink/10 bg-white px-2 py-1 text-xs text-ink-soft"
                  key={value}
                >
                  <input
                    checked={editType === value}
                    onChange={() => setEditType(value as EditType)}
                    type="radio"
                  />
                  {text}
                </label>
              ))}
            </div>
          </fieldset>

          <label className="mt-3 block text-xs font-medium text-ink" htmlFor={reasonId}>
            Reason
          </label>
          <textarea
            aria-required="true"
            className="mt-1 min-h-16 w-full rounded-md border border-ink/15 bg-white px-3 py-2 text-sm text-ink outline-none focus:border-forest focus:ring-2 focus:ring-forest/15"
            id={reasonId}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Why are you making this edit?"
            rows={2}
            value={reason}
          />

          {error ? (
            <p className="mt-2 text-sm text-red-700" role="alert">
              {error}
            </p>
          ) : null}
        </>
      )}

      <div className="mt-3 flex items-center gap-3">
        {!isArray ? (
          <button
            className="inline-flex items-center rounded-md bg-forest px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-forest/45"
            disabled={!reason.trim() || isSaving}
            onClick={() => {
              void handleSave();
            }}
            type="button"
          >
            {isSaving ? (
              <>
                <span
                  aria-hidden="true"
                  className="mr-2 size-3 animate-spin rounded-full border-2 border-forest-light/40 border-t-forest-light"
                />
                Saving…
              </>
            ) : (
              "Save"
            )}
          </button>
        ) : null}
        <button
          className="text-sm text-ink-soft underline-offset-2 hover:underline"
          onClick={onCancel}
          type="button"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
