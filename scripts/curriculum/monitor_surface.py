"""Product calls the Monitor API makes (machinery move step 4, slices S2 and S3a, #12504).

The Monitor routers under ``scripts/api`` are machinery. They do not import the
pipeline, audit, wiki, or activity modules below. ``scripts/api/state_helpers.py``
loads this module once, by the name in ``scripts/curriculum/monitor_paths.v1.json``
(field ``monitor_surface``), and the routers call it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# ``pipeline.*`` uses bare imports (``from pipeline.core import log``), so
# scripts/ must be importable. These are the module objects the Monitor used
# before this wrapper existed. The wiki compiler is the top-level ``wiki``
# package on that path. ``scripts.wiki`` is a second module object, and the
# route sweep rewrites state paths on ``wiki``, so this wrapper imports ``wiki``.
_SCRIPTS_DIR = str(Path(__file__).resolve().parents[1])
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import wiki.config as wiki_config
import wiki.quality_gate as wiki_quality
import wiki.sources as wiki_sources
import wiki.state as wiki_state
from pipeline.consultation import TemplateChange
from pipeline.consultation import apply_template_patch as _apply_template_patch
from pipeline.state import is_complete as phase_is_complete
from pipeline.state import load_state as load_pipeline_state
from scripts.audit.checks.activity_validation import (
    check_fill_in_answer_in_options,
    check_mark_the_words_answers_in_text,
    check_quiz_single_correct,
    check_select_min_correct,
    check_translate_single_correct,
    check_unjumble_out_of_scope_dative,
    check_unjumble_runon_answer,
)
from scripts.audit.config import (
    ACTIVITY_COMPLEXITY,
    ACTIVITY_RESTRICTIONS,
    LEVEL_CONFIG,
    VALID_ACTIVITY_TYPES,
)
from scripts.audit.llm_qg_store import (
    current_payload_for_module,
    llm_qg_file_is_current_for_module,
)
from scripts.audit.status_cache import get_source_paths, read_status
from scripts.slug_utils import to_bare_slug
from scripts.yaml_activities import ActivityParser

__all__ = [
    "ACTIVITY_COMPLEXITY",
    "ACTIVITY_RESTRICTIONS",
    "LEVEL_CONFIG",
    "VALID_ACTIVITY_TYPES",
    "ActivityParser",
    "activity_validation_violations",
    "apply_template_patch",
    "current_payload_for_module",
    "gather_discovery_sources_readonly",
    "get_source_paths",
    "list_discovery_slugs_readonly",
    "llm_qg_file_is_current_for_module",
    "load_pipeline_state",
    "load_wiki_progress",
    "phase_is_complete",
    "read_status",
    "read_wiki_log",
    "scan_wiki_track",
    "textbook_pdfs_dir",
    "to_bare_slug",
    "wiki_dir",
    "wiki_state_dir",
    "wiki_status_summary",
    "wiki_track_domains",
]


def apply_template_patch(
    template_path: Path,
    changes: list[dict[str, Any]],
    output_path: Path,
) -> tuple[bool, int]:
    """Apply a consultation proposal's change mappings to one template copy.

    Each mapping is one ``proposed_changes`` entry (``find``, ``replace``,
    ``file``, ``rationale``). Returns ``(success, num_applied)`` from
    ``pipeline.consultation.apply_template_patch``.
    """
    template_changes = [
        TemplateChange(
            find=change.get("find", ""),
            replace=change.get("replace", ""),
            file=change.get("file", ""),
            rationale=change.get("rationale", ""),
        )
        for change in changes
    ]
    result: tuple[bool, int] = _apply_template_patch(template_path, template_changes, output_path)
    return result


def textbook_pdfs_dir() -> Path:
    """Bulk textbook-PDF root from ``scripts.wiki.config.TEXTBOOK_PDFS_DIR``."""
    return Path(wiki_config.TEXTBOOK_PDFS_DIR)


def wiki_dir() -> Path:
    """Wiki tree the compiler is configured to read."""
    return Path(wiki_config.WIKI_DIR)


def wiki_state_dir() -> Path:
    """Wiki compiler state directory."""
    return Path(wiki_state.WIKI_STATE_DIR)


def wiki_status_summary() -> dict[str, Any]:
    """Compilation summary from ``scripts.wiki.state.get_status_summary``.

    The wiki router keeps a ``wiki_state`` name so ``scripts/api/main.py`` orient
    can call ``wiki_state.get_status_summary()`` without importing product code.
    """
    summary: dict[str, Any] = wiki_state.get_status_summary()
    return summary


def wiki_track_domains() -> dict[str, list[str]]:
    """Track id to wiki domain prefixes."""
    domains: dict[str, list[str]] = wiki_config.TRACK_DOMAINS
    return domains


def list_discovery_slugs_readonly(track: str) -> list[str]:
    """Track slugs from plans and discovery files, without writing discovery."""
    slugs: list[str] = list(wiki_sources.list_discovery_slugs_readonly(track))
    return slugs


def gather_discovery_sources_readonly(track: str, slug: str) -> dict[str, Any]:
    """Source inventory for one module, without writing discovery."""
    data: dict[str, Any] = wiki_sources.gather_discovery_sources_readonly(track, slug)
    return data


def load_wiki_progress() -> dict[str, Any]:
    """Wiki compilation progress in the shape ``wiki.state.load_progress`` returns."""
    progress: dict[str, Any] = wiki_state.load_progress()
    return progress


def read_wiki_log(*, track: str | None = None, last_n: int = 200) -> list[dict[str, Any]]:
    """Recent wiki build-log events."""
    events: list[dict[str, Any]] = wiki_state.read_log(track=track, last_n=last_n)
    return events


def scan_wiki_track(track: str) -> dict[str, list[str]]:
    """Quality-gate issues for one wiki track."""
    issues: dict[str, list[str]] = wiki_quality.scan_track(track)
    return issues


def activity_validation_violations(activities: list[Any]) -> list[Any]:
    """The seven structural activity checks the Blue monitor runs, in that order."""
    violations: list[Any] = []
    violations.extend(check_select_min_correct(activities))
    violations.extend(check_quiz_single_correct(activities))
    violations.extend(check_fill_in_answer_in_options(activities))
    violations.extend(check_translate_single_correct(activities))
    violations.extend(check_mark_the_words_answers_in_text(activities))
    violations.extend(check_unjumble_runon_answer(activities))
    violations.extend(check_unjumble_out_of_scope_dative(activities))
    return violations
