"""Pydantic schemas for POST /v1/projects/{project_id}/passport-pipeline.

TypeScript equivalent for Session B integration:

  interface PipelineSuccessResponse {
    status: "ok";
    source_document_id: string;        // UUID
    extraction_run_id: string;         // UUID
    passport_draft_id: string;         // UUID
    schema_version: string;
    schema_completeness_score: number;
    confidence_score: number;
    fetch_status: "ok" | "deduped";
    observation_count: number;
    draft: PassportDraft | null;       // full draft payload — avoids second GET
  }

  interface PipelineFailureResponse {
    status: "fetch_failed" | "parse_failed" | "projection_failed";
    stage: "fetch" | "parse" | "project";
    error: string;
    source_document_id: string | null;
    extraction_run_id: string | null;
  }
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.passport import PassportDraftGetResponse


class PipelineRequest(BaseModel):
    ehr_code: str


class PipelineSuccessResponse(BaseModel):
    status: Literal["ok"] = "ok"
    source_document_id: UUID
    extraction_run_id: UUID
    passport_draft_id: UUID
    schema_version: str
    schema_completeness_score: float
    confidence_score: float
    fetch_status: Literal["ok", "deduped"]
    observation_count: int
    draft: PassportDraftGetResponse | None = None


class PipelineFailureResponse(BaseModel):
    status: Literal["fetch_failed", "parse_failed", "projection_failed"]
    stage: Literal["fetch", "parse", "project"]
    error: str
    source_document_id: UUID | None = None
    extraction_run_id: UUID | None = None
