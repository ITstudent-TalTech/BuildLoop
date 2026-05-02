"use client";

import EvidenceBadge from "@/components/shared/EvidenceBadge";
import FieldRow from "@/components/shared/FieldRow";
import EditPanel from "./EditPanel";
import EditedPill from "./EditedPill";
import { type EditableFieldValue, useEditContext } from "./ReviewContext";

interface EditableFieldRowProps {
  fieldPath: string;
  label: string;
  fieldValue: EditableFieldValue;
  isMono?: boolean;
  editable?: boolean;
}

function fieldEvidence(fieldValue: EditableFieldValue) {
  return {
    confidence: fieldValue.confidence,
    sourcePage: fieldValue.source?.page,
    sourceLabel: fieldValue.source?.label,
    lastUpdated: fieldValue.last_updated,
  };
}

function displayValue(value: unknown) {
  if (value === null || value === undefined) {
    return null;
  }

  if (Array.isArray(value)) {
    return value.join(" · ");
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return value as string | number;
}

function displayFieldValue(fieldValue: EditableFieldValue, value: unknown) {
  return {
    ...fieldValue,
    value: displayValue(value),
  };
}

export default function EditableFieldRow({
  fieldPath,
  label,
  fieldValue,
  isMono = false,
  editable = true,
}: EditableFieldRowProps) {
  const { activeFieldPath, appliedEdits, startEdit, cancelEdit, saveEdit } =
    useEditContext();
  const appliedEdit = appliedEdits.find(
    (edit) => edit.target_field_path === fieldPath,
  );
  const isEditing = activeFieldPath === fieldPath;
  const currentValue = appliedEdit ? appliedEdit.new_value : fieldValue.value;
  const currentFieldValue = displayFieldValue(fieldValue, currentValue);

  if (!editable) {
    return (
      <div id={`field-${fieldPath.replace(/\./g, "-")}`}>
        <FieldRow
          evidence={fieldEvidence(fieldValue)}
          isMono={isMono}
          label={label}
          unit={fieldValue.unit}
          value={displayValue(fieldValue.value)}
        />
      </div>
    );
  }

  if (isEditing) {
    return (
      <div
        className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 border-b border-ink/10 py-3 last:border-b-0 md:grid-cols-[minmax(120px,30%)_1fr_auto] md:items-start md:gap-4"
        id={`field-${fieldPath.replace(/\./g, "-")}`}
      >
        <div className="text-xs font-medium uppercase leading-5 tracking-[0.06em] text-ink-soft md:text-sm md:font-normal md:normal-case md:tracking-normal">
          {label}
        </div>
        <div className="row-start-1 flex min-w-10 items-center justify-end self-start md:col-start-3 md:min-w-16 md:self-center">
          <EvidenceBadge {...fieldEvidence(fieldValue)} />
        </div>
        <div className="col-span-2 md:col-span-1 md:col-start-2">
        <EditPanel
          fieldPath={fieldPath}
          fieldValue={currentFieldValue}
          isMono={isMono}
          label={label}
          onCancel={() => cancelEdit(fieldPath)}
          onSave={(edit) => saveEdit(fieldPath, currentFieldValue, edit)}
          unit={fieldValue.unit}
        />
        </div>
      </div>
    );
  }

  return (
    <div
      className="group relative cursor-pointer rounded-md outline-none focus-visible:ring-2 focus-visible:ring-forest/40"
      id={`field-${fieldPath.replace(/\./g, "-")}`}
      onClick={() => startEdit(fieldPath)}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          startEdit(fieldPath);
        }
      }}
      role="button"
      tabIndex={0}
    >
      <FieldRow
        evidence={fieldEvidence(fieldValue)}
        isMono={isMono}
        label={label}
        unit={fieldValue.unit}
        value={currentFieldValue.value}
      />
      <div className="pointer-events-none absolute right-12 top-3 flex items-center gap-2 md:right-20 md:top-1/2 md:-translate-y-1/2">
        {appliedEdit ? (
          <EditedPill oldValue={appliedEdit.old_value} reason={appliedEdit.reason} />
        ) : null}
        <span
          aria-label={`Edit ${label}`}
          className="text-sm text-ink-soft opacity-0 transition-opacity group-hover:opacity-100 group-focus:opacity-100"
        >
          ✎
        </span>
      </div>
    </div>
  );
}
