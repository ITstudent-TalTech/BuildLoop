"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import BuildingPartsSection from "@/components/passport/BuildingPartsSection";
import QualitySection from "@/components/passport/QualitySection";
import SectionCard from "@/components/shared/SectionCard";
import { editDraftField, publishDraft } from "@/lib/api";
import type { Confidence, FieldValue, PassportDraft, PassportQuality } from "@/lib/api";
import EditableFieldRow from "./EditableFieldRow";
import PublishBar from "./PublishBar";
import PublishConfirmDialog from "./PublishConfirmDialog";
import {
  EditContext,
  type AppliedEdit,
  type EditableFieldValue,
  type PendingEdit,
} from "./ReviewContext";

interface EditablePassportLayoutProps {
  projectId: string;
  initialDraft: PassportDraft;
}

type PublishState = "idle" | "confirming" | "publishing" | "error";

const actor = "Mart Kask";

function cloneDraft(draft: PassportDraft): PassportDraft {
  return structuredClone(draft);
}

function confidenceLabel(fields: FieldValue<unknown>[]): Confidence {
  const counts = { high: 0, medium: 0, low: 0 };
  fields.forEach((field) => {
    if (field.value !== null) counts[field.confidence] += 1;
  });
  if (counts.low >= counts.medium && counts.low >= counts.high) return "low";
  if (counts.medium >= counts.high) return "medium";
  return "high";
}

function sectionStats(fields: FieldValue<unknown>[]) {
  return {
    fields_populated: fields.filter((field) => field.value !== null).length,
    fields_total: fields.length,
    confidence_label: confidenceLabel(fields),
  };
}

function recomputeQuality(draft: PassportDraft): PassportQuality {
  const identity = Object.values(draft.identity) as FieldValue<unknown>[];
  const profile = Object.values(draft.building_profile) as FieldValue<unknown>[];
  const structural = Object.values(draft.structural_systems) as FieldValue<unknown>[];
  const technical = Object.values(draft.technical_systems) as FieldValue<unknown>[];
  const location = Object.values(draft.location) as FieldValue<unknown>[];
  const partsPopulated = draft.building_parts.parts.length;
  const section_breakdown = {
    identity: sectionStats(identity),
    building_profile: sectionStats(profile),
    structural_systems: sectionStats(structural),
    technical_systems: sectionStats(technical),
    location: sectionStats(location),
    building_parts: {
      fields_populated: partsPopulated,
      fields_total: 5,
      confidence_label: draft.building_parts.confidence,
    },
  };
  const populated = Object.values(section_breakdown).reduce(
    (sum, item) => sum + item.fields_populated,
    0,
  );
  const total = Object.values(section_breakdown).reduce(
    (sum, item) => sum + item.fields_total,
    0,
  );
  const confidenceValues = Object.values(section_breakdown).map(
    (item) => item.confidence_label,
  );
  const qualityFields = [
    ...identity,
    ...profile,
    ...structural,
    ...technical,
    ...location,
  ];

  return {
    ...draft.quality,
    schema_completeness_score: Math.round((populated / total) * 100),
    confidence_score: Math.round(
      (qualityFields.reduce((sum, field) => {
        if (field.value === null) return sum;
        if (field.confidence === "high") return sum + 100;
        if (field.confidence === "medium") return sum + 70;
        return sum + 40;
      }, 0) /
        Math.max(1, qualityFields.filter((field) => field.value !== null).length)),
    ),
    confidence_label: confidenceValues.includes("low")
      ? "low"
      : confidenceValues.includes("medium")
        ? "medium"
        : "high",
    section_breakdown,
    missing_fields: draft.quality.missing_fields,
  };
}

function fieldValueAtPath(draft: PassportDraft, fieldPath: string) {
  const parts = fieldPath.split(".");
  let current: unknown = draft;

  for (const part of parts) {
    if (current === null || typeof current !== "object") return undefined;
    current = (current as Record<string, unknown>)[part];
  }

  return current as FieldValue<unknown> | undefined;
}

function applyValueAtPath(draft: PassportDraft, fieldPath: string, value: unknown) {
  const next = cloneDraft(draft);
  const parts = fieldPath.split(".");

  if (parts[0] === "building_profile" && parts[1] === "floors" && parts[2]) {
    next.building_profile.floors.value = {
      above_ground: next.building_profile.floors.value?.above_ground ?? null,
      below_ground: next.building_profile.floors.value?.below_ground ?? null,
      [parts[2]]: value,
    };
    next.building_profile.floors.confidence = "high";
    next.quality = recomputeQuality(next);
    return next;
  }

  const field = fieldValueAtPath(next, fieldPath);
  if (field) {
    field.value = value;
    field.confidence = "high";
  }

  next.quality = recomputeQuality(next);
  return next;
}

function editableEvidenceField<T>(
  field: FieldValue<T>,
): EditableFieldValue {
  return field as EditableFieldValue;
}

function floorsField(
  field: PassportDraft["building_profile"]["floors"],
  value: number | null | undefined,
): EditableFieldValue {
  return {
    ...field,
    value: value ?? null,
  };
}

function StaticLocationPreview({ coordinates }: { coordinates: string | null }) {
  return (
    <div className="mb-3 overflow-hidden rounded-md border border-ink/10 bg-surface">
      <svg
        aria-label="Static location reference"
        className="h-40 w-full"
        preserveAspectRatio="none"
        role="img"
        viewBox="0 0 640 160"
      >
        <rect fill="#f6f8f7" height="160" width="640" />
        {Array.from({ length: 9 }).map((_, index) => (
          <line
            key={`vertical-${index}`}
            stroke="#4a5852"
            strokeOpacity="0.08"
            x1={index * 80}
            x2={index * 80}
            y1="0"
            y2="160"
          />
        ))}
        {Array.from({ length: 5 }).map((_, index) => (
          <line
            key={`horizontal-${index}`}
            stroke="#4a5852"
            strokeOpacity="0.08"
            x1="0"
            x2="640"
            y1={index * 40}
            y2={index * 40}
          />
        ))}
        <path d="M302 62 L352 72 L344 105 L296 97 Z" fill="#1f4d3a" fillOpacity="0.9" />
        <path d="M302 62 L352 72 L344 105 L296 97 Z" fill="none" stroke="#0d1f17" strokeOpacity="0.2" />
        <rect fill="#ffffff" fillOpacity="0.82" height="24" rx="4" width="230" x="16" y="120" />
        <text fill="#4a5852" fontFamily="ui-monospace, monospace" fontSize="12" x="26" y="136">
          {coordinates ?? "Coordinates unavailable"}
        </text>
        <rect fill="#ffffff" fillOpacity="0.82" height="24" rx="4" width="118" x="506" y="120" />
        <text fill="#4a5852" fontFamily="ui-monospace, monospace" fontSize="12" x="516" y="136">
          Static reference
        </text>
      </svg>
    </div>
  );
}

export default function EditablePassportLayout({
  projectId,
  initialDraft,
}: EditablePassportLayoutProps) {
  const router = useRouter();
  const [draft, setDraft] = useState(initialDraft);
  const [pendingEdits, setPendingEdits] = useState<Map<string, PendingEdit>>(
    () => new Map(),
  );
  const [appliedEdits, setAppliedEdits] = useState<AppliedEdit[]>([]);
  const [activeFieldPath, setActiveFieldPath] = useState<string | null>(null);
  const [publishState, setPublishState] = useState<PublishState>("idle");
  const [publishError, setPublishError] = useState<string | null>(null);

  const saveEdit = useCallback(
    async (
      fieldPath: string,
      fieldValue: EditableFieldValue,
      edit: PendingEdit,
    ) => {
      setPendingEdits((current) => new Map(current).set(fieldPath, edit));
      await editDraftField(draft.passport_draft_id, {
        target_field_path: fieldPath,
        new_value: edit.new_value,
        reason: edit.reason,
      });
      setDraft((current) => applyValueAtPath(current, fieldPath, edit.new_value));
      setAppliedEdits((current) => [
        ...current,
        {
          target_field_path: fieldPath,
          old_value: fieldValue.value,
          new_value: edit.new_value,
          reason: edit.reason,
          edit_type: edit.edit_type,
          actor,
          applied_at: new Date().toISOString(),
        },
      ]);
      setPendingEdits((current) => {
        const next = new Map(current);
        next.delete(fieldPath);
        return next;
      });
      setActiveFieldPath(null);
    },
    [draft.passport_draft_id],
  );

  function discardAllEdits() {
    if (!confirm("Discard all edits from this review session?")) {
      return;
    }

    setDraft(initialDraft);
    setAppliedEdits([]);
    setPendingEdits(new Map());
    setActiveFieldPath(null);
  }

  async function publish() {
    setPublishState("publishing");
    setPublishError(null);

    try {
      const response = await publishDraft(draft.passport_draft_id);
      router.push(
        `/passport/${projectId}/published?version=${response.version_number}`,
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Publish failed";
      setPublishError(message);
      setPublishState("error");
    }
  }

  const contextValue = useMemo(
    () => ({
      activeFieldPath,
      appliedEdits,
      startEdit: (fieldPath: string) => setActiveFieldPath(fieldPath),
      cancelEdit: (fieldPath: string) => {
        if (activeFieldPath === fieldPath) setActiveFieldPath(null);
      },
      saveEdit,
    }),
    [activeFieldPath, appliedEdits, saveEdit],
  );

  const qualityDraft = useMemo(
    () => ({ ...draft, quality: recomputeQuality(draft) }),
    [draft],
  );

  return (
    <EditContext.Provider value={contextValue}>
      <div className="mt-8 space-y-6 pb-24">
        <SectionCard
          confidenceLabel="high"
          fieldsPopulated={5}
          fieldsTotal={5}
          title="Identity"
        >
          <EditableFieldRow editable={false} fieldPath="identity.ehr_code" fieldValue={editableEvidenceField(draft.identity.ehr_code)} isMono label="EHR code" />
          <EditableFieldRow editable={false} fieldPath="identity.normalized_address" fieldValue={editableEvidenceField(draft.identity.normalized_address)} label="Normalized address" />
          <EditableFieldRow editable={false} fieldPath="identity.address_aliases" fieldValue={editableEvidenceField(draft.identity.address_aliases)} label="Address aliases" />
          <EditableFieldRow editable={false} fieldPath="identity.country" fieldValue={editableEvidenceField(draft.identity.country)} label="Country" />
          <EditableFieldRow editable={false} fieldPath="identity.input_address" fieldValue={editableEvidenceField(draft.identity.input_address)} label="Original input" />
        </SectionCard>

        <SectionCard
          confidenceLabel={qualityDraft.quality.section_breakdown.building_profile.confidence_label}
          fieldsPopulated={qualityDraft.quality.section_breakdown.building_profile.fields_populated}
          fieldsTotal={qualityDraft.quality.section_breakdown.building_profile.fields_total}
          title="Building profile"
        >
          <EditableFieldRow fieldPath="building_profile.building_type" fieldValue={editableEvidenceField(draft.building_profile.building_type)} label="Building type" />
          <EditableFieldRow fieldPath="building_profile.building_status" fieldValue={editableEvidenceField(draft.building_profile.building_status)} label="Building status" />
          <EditableFieldRow fieldPath="building_profile.building_name" fieldValue={editableEvidenceField(draft.building_profile.building_name)} label="Building name" />
          <EditableFieldRow fieldPath="building_profile.use_categories" fieldValue={editableEvidenceField(draft.building_profile.use_categories)} label="Use categories" />
          <EditableFieldRow fieldPath="building_profile.floors.above_ground" fieldValue={floorsField(draft.building_profile.floors, draft.building_profile.floors.value?.above_ground)} label="Floors above ground" />
          <EditableFieldRow fieldPath="building_profile.floors.below_ground" fieldValue={floorsField(draft.building_profile.floors, draft.building_profile.floors.value?.below_ground)} label="Floors below ground" />
          <EditableFieldRow fieldPath="building_profile.footprint_area_m2" fieldValue={editableEvidenceField(draft.building_profile.footprint_area_m2)} label="Footprint area" />
          <EditableFieldRow fieldPath="building_profile.heated_area_m2" fieldValue={editableEvidenceField(draft.building_profile.heated_area_m2)} label="Heated area" />
          <EditableFieldRow fieldPath="building_profile.net_area_m2" fieldValue={editableEvidenceField(draft.building_profile.net_area_m2)} label="Net area" />
          <EditableFieldRow fieldPath="building_profile.public_use_area_m2" fieldValue={editableEvidenceField(draft.building_profile.public_use_area_m2)} label="Public-use area" />
          <EditableFieldRow fieldPath="building_profile.technical_area_m2" fieldValue={editableEvidenceField(draft.building_profile.technical_area_m2)} label="Technical area" />
          <EditableFieldRow fieldPath="building_profile.height_m" fieldValue={editableEvidenceField(draft.building_profile.height_m)} label="Height" />
          <EditableFieldRow fieldPath="building_profile.length_m" fieldValue={editableEvidenceField(draft.building_profile.length_m)} label="Length" />
          <EditableFieldRow fieldPath="building_profile.width_m" fieldValue={editableEvidenceField(draft.building_profile.width_m)} label="Width" />
          <EditableFieldRow fieldPath="building_profile.volume_m3" fieldValue={editableEvidenceField(draft.building_profile.volume_m3)} label="Volume" />
        </SectionCard>

        <SectionCard confidenceLabel={qualityDraft.quality.section_breakdown.structural_systems.confidence_label} fieldsPopulated={qualityDraft.quality.section_breakdown.structural_systems.fields_populated} fieldsTotal={7} title="Structural systems">
          <EditableFieldRow fieldPath="structural_systems.foundation_type" fieldValue={editableEvidenceField(draft.structural_systems.foundation_type)} label="Foundation type" />
          <EditableFieldRow fieldPath="structural_systems.load_bearing_material" fieldValue={editableEvidenceField(draft.structural_systems.load_bearing_material)} label="Load-bearing material" />
          <EditableFieldRow fieldPath="structural_systems.wall_type" fieldValue={editableEvidenceField(draft.structural_systems.wall_type)} label="Wall type" />
          <EditableFieldRow fieldPath="structural_systems.facade_finish_material" fieldValue={editableEvidenceField(draft.structural_systems.facade_finish_material)} label="Facade finish" />
          <EditableFieldRow fieldPath="structural_systems.floor_structure_material" fieldValue={editableEvidenceField(draft.structural_systems.floor_structure_material)} label="Floor structure" />
          <EditableFieldRow fieldPath="structural_systems.roof_structure_material" fieldValue={editableEvidenceField(draft.structural_systems.roof_structure_material)} label="Roof structure" />
          <EditableFieldRow fieldPath="structural_systems.roof_covering_material" fieldValue={editableEvidenceField(draft.structural_systems.roof_covering_material)} label="Roof covering" />
        </SectionCard>

        <SectionCard confidenceLabel={qualityDraft.quality.section_breakdown.technical_systems.confidence_label} fieldsPopulated={qualityDraft.quality.section_breakdown.technical_systems.fields_populated} fieldsTotal={7} title="Technical systems">
          <EditableFieldRow fieldPath="technical_systems.electricity" fieldValue={editableEvidenceField(draft.technical_systems.electricity)} label="Electricity" />
          <EditableFieldRow fieldPath="technical_systems.water" fieldValue={editableEvidenceField(draft.technical_systems.water)} label="Water" />
          <EditableFieldRow fieldPath="technical_systems.sewer" fieldValue={editableEvidenceField(draft.technical_systems.sewer)} label="Sewer" />
          <EditableFieldRow fieldPath="technical_systems.heat_source" fieldValue={editableEvidenceField(draft.technical_systems.heat_source)} label="Heat source" />
          <EditableFieldRow fieldPath="technical_systems.gas" fieldValue={editableEvidenceField(draft.technical_systems.gas)} label="Gas" />
          <EditableFieldRow fieldPath="technical_systems.ventilation" fieldValue={editableEvidenceField(draft.technical_systems.ventilation)} label="Ventilation" />
          <EditableFieldRow fieldPath="technical_systems.lift_count" fieldValue={editableEvidenceField(draft.technical_systems.lift_count)} label="Lifts" />
        </SectionCard>

        <SectionCard confidenceLabel={qualityDraft.quality.section_breakdown.location.confidence_label} fieldsPopulated={qualityDraft.quality.section_breakdown.location.fields_populated} fieldsTotal={3} title="Location">
          <StaticLocationPreview coordinates={draft.location.coordinates.value} />
          <EditableFieldRow fieldPath="location.geometry_method" fieldValue={editableEvidenceField(draft.location.geometry_method)} label="Geometry method" />
          <EditableFieldRow fieldPath="location.shape_type" fieldValue={editableEvidenceField(draft.location.shape_type)} label="Shape type" />
          <EditableFieldRow fieldPath="location.coordinates" fieldValue={editableEvidenceField(draft.location.coordinates)} isMono label="Coordinates" />
        </SectionCard>

        <div>
          <BuildingPartsSection buildingParts={draft.building_parts} />
          <p className="mt-2 text-sm text-ink-soft">
            Editing building parts comes next.
          </p>
        </div>

        <QualitySection quality={qualityDraft.quality} />
      </div>

      {publishError ? (
        <p className="fixed bottom-24 right-6 z-30 rounded-md bg-white px-3 py-2 text-sm text-red-700 shadow" role="alert">
          {publishError}
        </p>
      ) : null}

      <PublishBar
        edits={appliedEdits}
        onDiscard={discardAllEdits}
        onPublishClick={() => setPublishState("confirming")}
      />

      {publishState === "confirming" || publishState === "publishing" ? (
        <PublishConfirmDialog
          edits={appliedEdits}
          isPublishing={publishState === "publishing"}
          onCancel={() => setPublishState("idle")}
          onPublish={() => {
            void publish();
          }}
        />
      ) : null}

      <span className="sr-only">{pendingEdits.size} pending edits</span>
    </EditContext.Provider>
  );
}
