"""Product calls the Monitor API makes (machinery move step 4, slices S2 and S3a, #12504).

The Monitor routers under ``scripts/api`` are machinery. They do not import the
pipeline, audit, wiki, or activity modules below. ``scripts/api/state_helpers.py``
loads this module once, by the name in ``scripts/curriculum/monitor_paths.v1.json``
(field ``monitor_surface``), and the routers call it.
"""

from __future__ import annotations

import sqlite3
import sys
from collections.abc import Callable, Mapping
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
from scripts.audit import check_adrs
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
    "build_lineage_response",
    "collect_adr_governance",
    "collect_adr_governance_summary",
    "current_payload_for_module",
    "extract_image_page_context",
    "gather_discovery_sources_readonly",
    "get_source_paths",
    "hramatka_dimension_order",
    "hramatka_vesum_path",
    "list_discovery_slugs_readonly",
    "llm_qg_file_is_current_for_module",
    "load_pipeline_state",
    "load_wiki_progress",
    "phase_is_complete",
    "read_status",
    "read_wiki_log",
    "render_image_page_png",
    "scan_hramatka_lesson",
    "scan_wiki_track",
    "search_sources_literary",
    "search_sources_text",
    "sources_collection_stats",
    "textbook_pdfs_dir",
    "to_bare_slug",
    "verify_hramatka_words",
    "vesum_form_count",
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


def _matching_findings(findings: list[str], markers: tuple[str, ...]) -> list[str]:
    return [
        finding for finding in findings
        if any(marker in finding for marker in markers)
    ]


def collect_adr_governance() -> dict[str, Any]:
    """Full ADR findings for the governance endpoint."""
    result = check_adrs.run_check(check_promotions_flag=True)
    broken_chains = _matching_findings(
        result.errors,
        ("claims supersede by ADR-", "supersedes ADR-"),
    )
    orphaned_refs = _matching_findings(
        result.warnings,
        ("Orphaned reference to ADR-",),
    )
    stale_proposed = _matching_findings(
        result.warnings,
        ("in Proposed/DRAFT status",),
    )
    return {
        "total": len(result.adrs),
        "stale_proposed_count": len(stale_proposed),
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "broken_chains": broken_chains,
        "orphaned_refs": orphaned_refs,
        "promotion_candidates": result.promotion_candidates,
        "index": [record.as_dict() for record in result.adrs],
    }


def collect_adr_governance_summary() -> dict[str, int]:
    result = check_adrs.CheckResult()
    result.adrs = check_adrs._load_adrs()
    if not result.adrs:
        result.warnings.append("No ADRs found")
    else:
        check_adrs._check_numbering(result.adrs, result)
        check_adrs._check_required_fields(result.adrs, result)
        check_adrs._check_stale_proposed(
            result.adrs,
            result,
            check_adrs.STALE_PROPOSED_DAYS_DEFAULT,
        )
        check_adrs._check_supersede_chains(result.adrs, result)
        check_adrs._check_index_drift(result.adrs, result)
    return {
        "adrs_total": len(result.adrs),
        "adrs_warnings": len(result.warnings),
        "adrs_errors": len(result.errors),
    }


def build_lineage_response(project_root: Path, decision_id: str | None = None) -> dict[str, Any]:
    """Decision lineage for the Monitor's selected repository."""
    from scripts.audit.decision_lineage import build_lineage_response as build

    return build(project_root, decision_id=decision_id)


def hramatka_dimension_order() -> tuple[str, ...]:
    """The deterministic Hramatka quality-gate dimensions."""
    from scripts.audit.hramatka_qg_rules import DIMENSION_ORDER

    return DIMENSION_ORDER


def scan_hramatka_lesson(lesson: Mapping[str, Any]) -> dict[str, Any]:
    """Run the product quality gate for a generated Hramatka lesson."""
    from scripts.audit.hramatka_qg_rules import scan_hramatka_lesson as scan

    return scan(lesson)


def hramatka_vesum_path(explicit: str | Path | None = None) -> Path:
    """Resolve an explicit dictionary binding or the product's configured default."""
    from scripts.rag import config as rag_config
    from scripts.verification import vesum

    return vesum._resolve_vesum_db_path(explicit) if explicit is not None else rag_config.VESUM_DB_PATH


def verify_hramatka_words(
    words: list[str], *, pos_filter: str | None = None, db_path: Path
) -> dict[str, list[dict]]:
    """Attest forms using the product dictionary implementation."""
    from scripts.verification import vesum

    return vesum.verify_words(words, pos_filter=pos_filter, db_path=db_path)


def vesum_form_count(db_path: Path) -> int:
    """Number of forms in the bound dictionary, for Monitor readiness."""
    from scripts.verification import vesum

    conn = vesum.get_vesum_conn(db_path)
    return int(conn.execute("SELECT COUNT(*) FROM forms").fetchone()[0])


def _run_sources_query[T](handle: Any, callback: Callable[[], T]) -> T:
    """Run a lazy RAG query with the Monitor's context-owned read-only handle."""
    from rag.query import sources_db

    if handle is None or not handle.path.exists():
        raise FileNotFoundError("data/sources.db not found")
    connection = handle.connect(read_only=True)
    connection.row_factory = sqlite3.Row
    try:
        with sources_db.using_connection(connection):
            return callback()
    finally:
        connection.close()


def search_sources_text(
    handle: Any, q: str, *, grade: int | None = None, subject: str | None = None,
    trust_tier: int | None = None, limit: int = 5,
) -> list[dict[str, Any]]:
    """Search source text, or preserve the empty result when the corpus is absent."""
    from rag.query import search_text

    try:
        return _run_sources_query(
            handle, lambda: search_text(q, grade=grade, subject=subject, trust_tier=trust_tier, limit=limit)
        )
    except FileNotFoundError:
        return []


def search_sources_literary(
    handle: Any, q: str, *, work: str | None = None, genre: str | None = None,
    period: str | None = None, limit: int = 5,
) -> list[dict[str, Any]]:
    """Search literary sources, or preserve the absent-corpus empty result."""
    from rag.query import search_literary

    try:
        return _run_sources_query(
            handle, lambda: search_literary(q, work=work, genre=genre, period=period, limit=limit)
        )
    except FileNotFoundError:
        return []


def sources_collection_stats(handle: Any) -> dict[str, Any]:
    """Corpus statistics with the Monitor's documented missing-database envelope."""
    from rag.query import collection_stats

    try:
        return _run_sources_query(handle, collection_stats)
    except FileNotFoundError:
        return {"sources_db": {"error": "data/sources.db not found"}}


def extract_image_page_context(doc: Any, page_num: int) -> tuple[Any, Any, Any, float]:
    """Text and image boxes, page bounds and scale from the optional PDF helper."""
    from rag.poc_pair_page import SCALE, extract_images, extract_text_blocks

    page = doc[page_num - 1]
    return extract_text_blocks(page), extract_images(page), page.rect, SCALE


def render_image_page_png(doc: Any, page_num: int) -> bytes:
    """Render one page at the product helper's configured DPI."""
    from rag.poc_pair_page import RENDER_DPI

    png: bytes = doc[page_num - 1].get_pixmap(dpi=RENDER_DPI).tobytes("png")
    return png
