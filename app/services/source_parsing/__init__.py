"""source_parsing — PDF parsing service and canonical observation extraction.

Public surface:
  SourceParsingService  — service class; orchestrates parse + persist.
  ParseResult           — result dataclass returned by parse_source_document().
"""

from app.services.source_parsing.service import SourceParsingService
from app.services.source_parsing.types import ParseResult

__all__ = ["SourceParsingService", "ParseResult"]
