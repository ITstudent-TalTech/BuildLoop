"""Passport engine — projects observations into FieldValue<T>-shaped drafts.

Public API:
  PassportEngine   — service class for generate_draft / get_current_draft
  ProjectionResult — result dataclass returned by generate_draft
"""

from app.services.passport_engine.service import PassportEngine
from app.services.passport_engine.types import ProjectionResult

__all__ = ["PassportEngine", "ProjectionResult"]
