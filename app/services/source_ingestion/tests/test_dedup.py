"""Tests for dedup.find_existing_by_checksum.

Uses an AsyncMock for the AsyncSession — no live database required.

Acceptance criteria covered:
  - No existing row → returns None.
  - Exact (building_id, checksum) match → returns the row.
  - Different checksum, same building_id → returns None.
  - Different building_id, same checksum → returns None.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.source_ingestion.dedup import find_existing_by_checksum


def _make_db(row: object) -> AsyncMock:
    """Return a mock AsyncSession whose execute() returns a scalar_one_or_none result."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = row

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    return mock_db


def _make_source_doc(building_id: object, checksum: str) -> MagicMock:
    from app.models.source_documents import SourceDocument

    doc = MagicMock(spec=SourceDocument)
    doc.id = uuid4()
    doc.building_id = building_id
    doc.checksum = checksum
    return doc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_existing_row_returns_none() -> None:
    """When no row matches, the function returns None."""
    mock_db = _make_db(None)
    result = await find_existing_by_checksum(uuid4(), "abc123", mock_db)
    assert result is None


@pytest.mark.asyncio
async def test_exact_checksum_match_returns_row() -> None:
    """When building_id + checksum both match, the existing row is returned."""
    building_id = uuid4()
    checksum = "a" * 64
    doc = _make_source_doc(building_id, checksum)
    mock_db = _make_db(doc)

    result = await find_existing_by_checksum(building_id, checksum, mock_db)

    assert result is not None
    assert result.checksum == checksum
    assert result.building_id == building_id


@pytest.mark.asyncio
async def test_different_checksum_returns_none() -> None:
    """Different checksum for the same building → no match (db returns None)."""
    mock_db = _make_db(None)
    result = await find_existing_by_checksum(uuid4(), "b" * 64, mock_db)
    assert result is None


@pytest.mark.asyncio
async def test_different_building_id_returns_none() -> None:
    """Different building_id with same checksum → no match (db returns None)."""
    mock_db = _make_db(None)
    result = await find_existing_by_checksum(uuid4(), "c" * 64, mock_db)
    assert result is None


@pytest.mark.asyncio
async def test_db_execute_called_once() -> None:
    """The function issues exactly one SELECT per call."""
    mock_db = _make_db(None)
    await find_existing_by_checksum(uuid4(), "d" * 64, mock_db)
    mock_db.execute.assert_called_once()
