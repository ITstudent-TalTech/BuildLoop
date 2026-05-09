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

// ── API mode ──────────────────────────────────────────────────────────────────

function getApiMode(): "mock" | "real" {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_MODE === "real") {
    return "real";
  }
  return "mock";
}

function getApiUrl(): string {
  const url =
    typeof process !== "undefined" ? process.env.NEXT_PUBLIC_API_URL : undefined;
  return (url ?? "http://localhost:8000").replace(/\/$/, "");
}

// ── Real fetch helper ─────────────────────────────────────────────────────────
// NOTE: Deployed environments require CORSMiddleware on the FastAPI side.
// For local dev, FastAPI's default permissive CORS suffices.

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new ApiError(0, "network_error", "Could not reach backend");
  }
  if (!response.ok) {
    let body: Record<string, string> = {};
    try {
      body = (await response.json()) as Record<string, string>;
    } catch {
      body = { detail: response.statusText };
    }
    throw new ApiError(
      response.status,
      body["code"] ?? body["detail"] ?? "unknown",
      body["message"] ?? body["detail"] ?? response.statusText,
    );
  }
  return response.json() as Promise<T>;
}

// ── Pipeline response shape (internal mapping — not surfaced in types.ts) ─────

interface PipelineSuccessResponse {
  status: "ok";
  source_document_id: string;
  extraction_run_id: string;
  passport_draft_id: string;
  schema_version: string;
  schema_completeness_score: number;
  confidence_score: number;
  fetch_status: "ok" | "deduped";
  observation_count: number;
}

// ── Mock network wrapper (unchanged from original) ────────────────────────────

async function withMockNetwork<T>(operation: () => T): Promise<T> {
  const delayMs = Math.max(0, getMockDelayMs());
  await new Promise((resolve) => setTimeout(resolve, delayMs));
  const failure = consumeFailNext();
  if (failure) {
    throw new ApiError(failure.status, failure.code, failure.message);
  }
  return operation();
}

// ── Client functions ──────────────────────────────────────────────────────────

/**
 * POST /v1/intakes
 */
export function createIntake(input: IntakeRequest): Promise<IntakeResponse> {
  if (getApiMode() === "real") {
    return fetchJson<IntakeResponse>(`${getApiUrl()}/v1/intakes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        address_input: input.address_input,
        project_title: input.project_title,
      }),
    });
  }
  return withMockNetwork(() => mockCreateIntake(input));
}

/**
 * POST /v1/resolutions
 */
export function resolveAddress(intakeId: string): Promise<ResolutionResponse> {
  if (getApiMode() === "real") {
    return fetchJson<ResolutionResponse>(`${getApiUrl()}/v1/resolutions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intake_request_id: intakeId }),
    });
  }
  return withMockNetwork(() => mockResolveAddress(intakeId));
}

/**
 * POST /v1/resolutions/{resolution_run_id}/select
 */
export function selectCandidate(
  resolutionRunId: string,
  ehrCode: string,
): Promise<ResolutionResponse> {
  if (getApiMode() === "real") {
    return fetchJson<ResolutionResponse>(
      `${getApiUrl()}/v1/resolutions/${resolutionRunId}/select`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ehr_code: ehrCode }),
      },
    );
  }
  return withMockNetwork(() => mockSelectCandidate(resolutionRunId, ehrCode));
}

/**
 * POST /v1/projects/{project_id}/sources/fetch
 */
export function fetchSourceDocuments(
  projectId: string,
  ehrCode: string,
): Promise<SourceFetchResponse> {
  if (getApiMode() === "real") {
    return fetchJson<SourceFetchResponse>(
      `${getApiUrl()}/v1/projects/${projectId}/sources/fetch`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ehr_code: ehrCode }),
      },
    );
  }
  return withMockNetwork(() => mockFetchSourceDocuments(projectId, ehrCode));
}

/**
 * POST /v1/source-documents/{source_document_id}/parse
 */
export function parseSourceDocument(sourceDocumentId: string): Promise<ParseResponse> {
  if (getApiMode() === "real") {
    return fetchJson<ParseResponse>(
      `${getApiUrl()}/v1/source-documents/${sourceDocumentId}/parse`,
      { method: "POST" },
    );
  }
  return withMockNetwork(() => mockParseSourceDocument(sourceDocumentId));
}

/**
 * POST /v1/projects/{project_id}/passport-pipeline-auto
 * Consolidated fetch → parse → project pipeline. Backend reads the EHR code
 * from the project's resolved building — no ehr_code needed in the request.
 */
export function generatePassportDraft(
  projectId: string,
): Promise<PassportDraftResponse> {
  if (getApiMode() === "real") {
    return fetchJson<PipelineSuccessResponse>(
      `${getApiUrl()}/v1/projects/${projectId}/passport-pipeline-auto`,
      { method: "POST" },
    ).then(
      (res): PassportDraftResponse => ({
        status: "ok",
        passport_draft_id: res.passport_draft_id,
        schema_version: res.schema_version as PassportDraft["schema_version"],
        schema_completeness_score: res.schema_completeness_score,
        confidence_score: res.confidence_score,
      }),
    );
  }
  return withMockNetwork(() => mockGeneratePassportDraft(projectId));
}

/**
 * GET /v1/projects/{project_id}/passport-draft
 */
export function getPassportDraft(projectId: string): Promise<PassportDraft> {
  if (getApiMode() === "real") {
    return fetchJson<PassportDraft>(
      `${getApiUrl()}/v1/projects/${projectId}/passport-draft`,
    );
  }
  return withMockNetwork(() => mockGetPassportDraft(projectId));
}

/**
 * PATCH /v1/passport-drafts/{passport_draft_id}/fields
 * Session C pending — real mode returns 501 until endpoint is built.
 */
export function editDraftField(
  draftId: string,
  edit: FieldEditRequest,
): Promise<PassportDraft> {
  if (getApiMode() === "real") {
    return Promise.reject(
      new ApiError(
        501,
        "not_yet_implemented",
        "Field editing is not yet available. This will be wired up in Session C.",
      ),
    );
  }
  return withMockNetwork(() => mockEditDraftField(draftId, edit));
}

/**
 * POST /v1/passport-drafts/{passport_draft_id}/publish
 * Session C pending — real mode returns 501 until endpoint is built.
 */
export function publishDraft(draftId: string): Promise<PublishResponse> {
  if (getApiMode() === "real") {
    return Promise.reject(
      new ApiError(
        501,
        "not_yet_implemented",
        "Publishing is not yet available. This will be wired up in Session C.",
      ),
    );
  }
  return withMockNetwork(() => mockPublishDraft(draftId));
}
