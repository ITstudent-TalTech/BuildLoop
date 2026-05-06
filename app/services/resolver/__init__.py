"""Resolver service package.

Public exports for use by the API layer:
  ResolverService  — main orchestration class
  ResolutionResult — service return type
"""

from app.services.resolver.service import ResolverService
from app.services.resolver.types import ResolutionResult

__all__ = ["ResolverService", "ResolutionResult"]
