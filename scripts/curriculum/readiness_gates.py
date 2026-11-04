"""Product gates for curriculum readiness and the lifecycle pilot."""

from __future__ import annotations

from scripts.audit import lint_bio_dossier_xref, post_build_review
from scripts.audit.wiki_completeness_gate import check_wiki_completeness
from scripts.build import linear_pipeline
from scripts.level_config import base_level, resolve_content_track, resolve_manifest_module_track
from scripts.validate import check_discovery_integrity, check_wiki_subject, lint_seminar_quality
from scripts.wiki.domains import resolve_write_domain
from scripts.wiki.sources_schema import load_sources_registry, validate_sources_registry

__all__ = [
    "base_level",
    "check_discovery_integrity",
    "check_wiki_completeness",
    "check_wiki_subject",
    "linear_pipeline",
    "lint_bio_dossier_xref",
    "lint_seminar_quality",
    "load_sources_registry",
    "post_build_review",
    "resolve_content_track",
    "resolve_manifest_module_track",
    "resolve_write_domain",
    "validate_sources_registry",
]
