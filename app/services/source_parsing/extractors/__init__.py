"""Extractor functions for each canonical observation namespace.

Each extractor accepts a page_map and/or full text and returns a
list[ObservationDraft]. Import all from here for convenience.
"""

from app.services.source_parsing.extractors.building_parts import extract_building_parts
from app.services.source_parsing.extractors.building_profile import extract_building_profile
from app.services.source_parsing.extractors.identity import extract_identity
from app.services.source_parsing.extractors.location import extract_location
from app.services.source_parsing.extractors.structural_systems import extract_structural_systems
from app.services.source_parsing.extractors.technical_systems import extract_technical_systems

__all__ = [
    "extract_identity",
    "extract_building_profile",
    "extract_structural_systems",
    "extract_technical_systems",
    "extract_location",
    "extract_building_parts",
]
