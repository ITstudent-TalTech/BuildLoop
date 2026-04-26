import {
  completeDraftFixture,
  partialDraftFixture,
  sparseDraftFixture,
} from "./fixtures/passport-drafts";
import { intakeFixture } from "./fixtures/intake";
import {
  ambiguousFixture,
  resolvedFixture,
  unresolvedFixture,
} from "./fixtures/resolution";
import {
  consumeFailNext,
  getMockDraftVariant,
  getMockResolutionMode,
} from "./mock-config";
import type {
  FieldEditRequest,
  IntakeRequest,
  IntakeResponse,
  ParseResponse,
  PassportDraft,
  PassportDraftResponse,
  PublishResponse,
  ResolutionResponse,
  SourceFetchResponse,
} from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function clone<T>(value: T): T {
  return structuredClone(value);
}

function currentDraftFixture() {
  const variant = getMockDraftVariant();

  if (variant === "partial") {
    return partialDraftFixture;
  }

  if (variant === "sparse") {
    return sparseDraftFixture;
  }

  return completeDraftFixture;
}

function throwIfFailNext() {
  const failure = consumeFailNext();

  if (failure) {
    throw new ApiError(failure.status, failure.code, failure.message);
  }
}

export function mockCreateIntake(input: IntakeRequest): IntakeResponse {
  throwIfFailNext();

  if (!input.address_input.trim()) {
    throw new ApiError(400, "address_required", "Address input is required");
  }

  return clone(intakeFixture);
}

export function mockResolveAddress(_intakeId: string): ResolutionResponse {
  throwIfFailNext();
  void _intakeId;

  const mode = getMockResolutionMode();

  if (mode === "ambiguous") {
    return clone(ambiguousFixture);
  }

  if (mode === "unresolved") {
    return clone(unresolvedFixture);
  }

  return clone(resolvedFixture);
}

export function mockSelectCandidate(
  resolutionRunId: string,
  ehrCode: string,
): ResolutionResponse {
  throwIfFailNext();

  const candidate = ambiguousFixture.candidates.find(
    (item) => item.ehr_code === ehrCode,
  );

  if (!candidate) {
    throw new ApiError(404, "candidate_not_found", "Resolution candidate not found");
  }

  return {
    status: "resolved",
    resolution_run_id: resolutionRunId,
    ehr_code: candidate.ehr_code,
    normalized_address: candidate.normalized_address,
    address_aliases:
      candidate.ehr_code === "101035685" ? ["Lai tn 1", "Nunne tn 4"] : [],
    confidence_score: candidate.confidence_score,
  };
}

export function mockFetchSourceDocuments(
  _projectId: string,
  ehrCode: string,
): SourceFetchResponse {
  throwIfFailNext();

  if (ehrCode !== "101035685") {
    throw new ApiError(404, "source_not_found", "No source document for EHR code");
  }

  return {
    status: "ok",
    source_document_id: "src_ehr_pdf_001",
    source_type: "ehr_pdf",
    fetch_status: "ok",
  };
}

export function mockParseSourceDocument(sourceDocumentId: string): ParseResponse {
  throwIfFailNext();

  if (sourceDocumentId !== "src_ehr_pdf_001") {
    throw new ApiError(404, "source_document_not_found", "Source document not found");
  }

  return {
    status: "ok",
    extraction_run_id: "extract_lai_001",
    observation_count: 87,
  };
}

export function mockGeneratePassportDraft(
  _projectId: string,
): PassportDraftResponse {
  throwIfFailNext();
  void _projectId;

  const draft = currentDraftFixture();

  return {
    status: "ok",
    passport_draft_id: draft.passport_draft_id,
    schema_version: draft.schema_version,
    schema_completeness_score: draft.quality.schema_completeness_score,
    confidence_score: draft.quality.confidence_score,
  };
}

export function mockGetPassportDraft(projectId: string): PassportDraft {
  throwIfFailNext();

  const draft = currentDraftFixture();

  if (projectId !== draft.project_id && projectId !== "demo-project-id") {
    throw new ApiError(404, "passport_draft_not_found", "Passport draft not found");
  }

  return clone(draft);
}

export function mockEditDraftField(
  draftId: string,
  _edit: FieldEditRequest,
): PassportDraft {
  throwIfFailNext();
  void _edit;

  const draft = clone(currentDraftFixture());

  if (draftId !== draft.passport_draft_id) {
    throw new ApiError(404, "passport_draft_not_found", "Passport draft not found");
  }

  return draft;
}

export function mockPublishDraft(draftId: string): PublishResponse {
  throwIfFailNext();

  const draft = currentDraftFixture();

  if (draftId !== draft.passport_draft_id) {
    throw new ApiError(404, "passport_draft_not_found", "Passport draft not found");
  }

  return {
    status: "published",
    passport_version_id: "version_lai_001",
    version_number: 1,
  };
}
