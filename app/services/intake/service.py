"""IntakeService — creates a new intake request and associated project.

Minimal intake creation sufficient for the resolver to have an
intake_request_id to work with. The project_id is stored on the proper
FK column intake_requests.project_id (migration 734960e74be2).

normalized_input is initialized to {} here; the resolver populates it
with the parsed address shape during resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intake_requests import IntakeRequest
from app.models.projects import Project


@dataclass
class IntakeCreated:
    intake_request_id: UUID
    project_id: UUID


class IntakeService:
    """Creates an IntakeRequest + Project pair for one address submission.

    Inputs (create):
      address_input — raw address string from the user.
      project_title — human-readable project label.
      db            — async SQLAlchemy session (caller owns the lifecycle).
    Outputs:
      IntakeCreated with both IDs and status="received".
    Persistence:
      - One projects row (status="draft", raw_input_address=address_input).
      - One intake_requests row (status="received", project_id=project.id).
    """

    async def create(
        self,
        address_input: str,
        project_title: str,
        db: AsyncSession,
    ) -> IntakeCreated:
        """Persist an intake request + project pair and return their IDs."""
        project = Project(
            title=project_title,
            raw_input_address=address_input,
            status="draft",
        )
        db.add(project)
        await db.flush()  # populate project.id (Python-side uuid4 default)

        intake = IntakeRequest(
            raw_address_input=address_input,
            normalized_input={},
            project_id=project.id,
            status="received",
        )
        db.add(intake)
        await db.commit()

        return IntakeCreated(
            intake_request_id=intake.id,
            project_id=project.id,
        )
