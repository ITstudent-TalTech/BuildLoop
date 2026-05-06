"""Pydantic request/response schemas for the /v1/intakes endpoint.

Shapes match /web/lib/api/types.ts exactly:
  IntakeRequest  → IntakeRequest (TS)
  IntakeResponse → IntakeResponse (TS)
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class IntakeRequestBody(BaseModel):
    """POST /v1/intakes request body."""

    address_input: str
    project_title: str


class IntakeResponse(BaseModel):
    """POST /v1/intakes response — matches IntakeResponse in types.ts."""

    intake_request_id: UUID
    project_id: UUID
    status: Literal["received"] = "received"
