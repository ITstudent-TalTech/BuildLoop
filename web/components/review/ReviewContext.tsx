"use client";

import { createContext, useContext } from "react";
import type { FieldValue } from "@/lib/api";

export type EditType = "override" | "confirmation" | "correction";

export type PendingEdit = {
  new_value: unknown;
  reason: string;
  edit_type: EditType;
};

export type AppliedEdit = {
  target_field_path: string;
  old_value: unknown;
  new_value: unknown;
  reason: string;
  edit_type: EditType;
  actor: string;
  applied_at: string;
};

export type EditableFieldValue = FieldValue<
  string | number | string[] | { above_ground: number | null; below_ground: number | null }
>;

type EditContextValue = {
  activeFieldPath: string | null;
  appliedEdits: AppliedEdit[];
  startEdit: (fieldPath: string) => void;
  cancelEdit: (fieldPath: string) => void;
  saveEdit: (
    fieldPath: string,
    fieldValue: EditableFieldValue,
    edit: PendingEdit,
  ) => Promise<void>;
};

export const EditContext = createContext<EditContextValue | null>(null);

export function useEditContext() {
  const context = useContext(EditContext);

  if (!context) {
    throw new Error("useEditContext must be used inside EditContext.Provider");
  }

  return context;
}
