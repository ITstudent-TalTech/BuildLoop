import {
  ApiError,
  mockCreateIntake,
  mockEditDraftField,
  mockFetchSourceDocuments,
  mockGeneratePassportDraft,
  mockGetPassportDraft,
  mockParseSourceDocument,
  mockPublishDraft,
  mockResolveAddress,
  mockSelectCandidate,
} from "./mocks";
import { consumeFailNext, getMockDelayMs } from "./mock-config";
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

async function withMockNetwork<T>(operation: () => T): Promise<T> {
  const delayMs = Math.max(0, getMockDelayMs());

  await new Promise((resolve) => setTimeout(resolve, delayMs));

  const failure = consumeFailNext();

  if (failure) {
    throw new ApiError(failure.status, failure.code, failure.message);
  }

  return operation();
}

/**
 * POST /v1/intakes
 */
export function createIntake(input: IntakeRequest): Promise<IntakeResponse> {
  return withMockNetwork(() => mockCreateIntake(input));
}

/**
 * POST /v1/resolutions
 */
export function resolveAddress(intakeId: string): Promise<ResolutionResponse> {
  return withMockNetwork(() => mockResolveAddress(intakeId));
}

/**
 * POST /v1/resolutions/{resolution_run_id}/select
 */
export function selectCandidate(
  resolutionRunId: string,
  ehrCode: string,
): Promise<ResolutionResponse> {
  return withMockNetwork(() => mockSelectCandidate(resolutionRunId, ehrCode));
}

/**
 * POST /v1/projects/{project_id}/sources/fetch
 */
export function fetchSourceDocuments(
  projectId: string,
  ehrCode: string,
): Promise<SourceFetchResponse> {
  return withMockNetwork(() => mockFetchSourceDocuments(projectId, ehrCode));
}

/**
 * POST /v1/source-documents/{source_document_id}/parse
 */
export function parseSourceDocument(
  sourceDocumentId: string,
): Promise<ParseResponse> {
  return withMockNetwork(() => mockParseSourceDocument(sourceDocumentId));
}

/**
 * POST /v1/projects/{project_id}/passport-drafts
 */
export function generatePassportDraft(
  projectId: string,
): Promise<PassportDraftResponse> {
  return withMockNetwork(() => mockGeneratePassportDraft(projectId));
}

/**
 * GET /v1/projects/{project_id}/passport-draft
 */
export function getPassportDraft(projectId: string): Promise<PassportDraft> {
  return withMockNetwork(() => mockGetPassportDraft(projectId));
}

/**
 * PATCH /v1/passport-drafts/{passport_draft_id}/fields
 */
export function editDraftField(
  draftId: string,
  edit: FieldEditRequest,
): Promise<PassportDraft> {
  return withMockNetwork(() => mockEditDraftField(draftId, edit));
}

/**
 * POST /v1/passport-drafts/{passport_draft_id}/publish
 */
export function publishDraft(draftId: string): Promise<PublishResponse> {
  return withMockNetwork(() => mockPublishDraft(draftId));
}
