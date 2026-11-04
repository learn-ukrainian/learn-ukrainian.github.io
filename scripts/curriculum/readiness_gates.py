"""Product gates for curriculum readiness, the lifecycle pilot and Sources diagnostics."""

from __future__ import annotations

import os
import signal
from collections.abc import Mapping
from pathlib import Path

from scripts.audit import lint_bio_dossier_xref, post_build_review
from scripts.audit.wiki_completeness_gate import check_wiki_completeness
from scripts.build import linear_pipeline
from scripts.level_config import base_level, resolve_content_track, resolve_manifest_module_track
from scripts.validate import check_discovery_integrity, check_wiki_subject, lint_seminar_quality
from scripts.wiki.domains import resolve_write_domain
from scripts.wiki.sources_schema import load_sources_registry, validate_sources_registry

__all__ = [
    "DEFAULT_DUMP_SUBDIR",
    "DUMP_DIR_ENV",
    "DUMP_SIGNAL",
    "base_level",
    "check_discovery_integrity",
    "check_wiki_completeness",
    "check_wiki_subject",
    "ensure_dump_dir",
    "faulthandler_log_path",
    "linear_pipeline",
    "lint_bio_dossier_xref",
    "lint_seminar_quality",
    "load_sources_registry",
    "post_build_review",
    "resolve_content_track",
    "resolve_dump_dir",
    "resolve_manifest_module_track",
    "resolve_write_domain",
    "validate_sources_registry",
]


DUMP_DIR_ENV = "LU_SOURCES_DUMP_DIR"


DEFAULT_DUMP_SUBDIR = Path("batch_state") / "sources-dumps"


DUMP_SIGNAL = signal.SIGUSR1


def resolve_dump_dir(project_root: Path, environ: Mapping[str, str] | None = None) -> Path:
    environ = os.environ if environ is None else environ
    override = environ.get(DUMP_DIR_ENV, "").strip()
    return Path(override) if override else project_root / DEFAULT_DUMP_SUBDIR


def faulthandler_log_path(dump_dir: Path, pid: int) -> Path:
    return dump_dir / f"faulthandler-{pid}.log"


def ensure_dump_dir(dump_dir: Path) -> Path:
    dump_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(dump_dir, 0o700)
    return dump_dir
