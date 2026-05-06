"""Checksum-based deduplication for source documents.

Dedup scope: (building_id, checksum) — not project_id.

Rationale: the same physical EHR PDF doesn't change across user projects
for the same building. If user A fetched it last week and user B asks for
the same building this week, B receives the existing source_documents row
rather than a duplicate Storage object.

See DECISIONS.md § "Checksum-based dedup scoped to (building_id, checksum)".
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_documents import SourceDocument


async def find_existing_by_checksum(
    building_id: UUID,
    checksum: str,
    db: AsyncSession,
) -> SourceDocument | None:
    """Return an existing SourceDocument row matching (building_id, checksum), or None.

    Inputs:
      building_id — scopes the search to one physical building.
      checksum    — SHA-256 hex digest of the PDF bytes.
      db          — async SQLAlchemy session.
    Outputs:
      The matching SourceDocument row, or None if no match exists.
    Side effects:
      Read-only — issues a SELECT, does not modify any row.
    """
    stmt = select(SourceDocument).where(
        SourceDocument.building_id == building_id,
        SourceDocument.checksum == checksum,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
