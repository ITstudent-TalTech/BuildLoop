"""ORM model registry — import all models here so alembic can discover them."""

from app.models.buildings import Building
from app.models.condition_annotations import ConditionAnnotation
from app.models.extraction_runs import ExtractionRun
from app.models.intake_requests import IntakeRequest
from app.models.listing_candidates import ListingCandidate
from app.models.manual_edits import ManualEdit
from app.models.observations import Observation
from app.models.passport_drafts import PassportDraft
from app.models.passport_versions import PassportVersion
from app.models.photo_assets import PhotoAsset
from app.models.projects import Project
from app.models.resolver_runs import ResolverCandidate, ResolverRun
from app.models.source_documents import SourceDocument

__all__ = [
    "Building",
    "ConditionAnnotation",
    "ExtractionRun",
    "IntakeRequest",
    "ListingCandidate",
    "ManualEdit",
    "Observation",
    "PassportDraft",
    "PassportVersion",
    "PhotoAsset",
    "Project",
    "ResolverCandidate",
    "ResolverRun",
    "SourceDocument",
]
