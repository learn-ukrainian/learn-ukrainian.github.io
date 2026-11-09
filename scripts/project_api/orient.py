"""Product sections of ``GET /api/orient``: pipeline, wiki and governance, plus a health field.

The machinery orient endpoint composes these with its own sections in the
order the response always had: ``pipeline`` after ``idle_prs``, ``wiki``
after ``rollovers`` and ``governance`` after ``wiki`` (Monitor split, C-4687).
:func:`orient_sections` reads the collectors from this module when called, so
a collector replaced here is the one that runs.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from typing import Any

from scripts.api.monitor_context import MonitorContext, resolve_context
from scripts.api.product_contribution import OrientSection

from . import state_router as state_api
from . import wiki_router as wiki_api
from .context import product_roots
from .governance_router import collect_governance_summary

GOVERNANCE_FALLBACK = {
    "decisions_total": 0,
    "decisions_stale": 0,
    "decisions_approaching_expiry": 0,
    "adrs_total": 0,
    "adrs_warnings": 0,
    "adrs_errors": 0,
}


async def collect_pipeline_orient_data(ctx: MonitorContext | None = None) -> dict:
    resolved_ctx = resolve_context(ctx)
    return {"summary": await state_api.state_summary(fresh=False, ctx=resolved_ctx)}


def collect_wiki_orient_data(ctx: MonitorContext | None = None) -> dict:
    """Per-track compiled article counts.

    The previous implementation called ``_resolve_article`` inside the per-slug
    loop (~22 tracks × ~80 slugs = ~1776 calls). Each ``_resolve_article``
    rebuilds the full slug→candidates index from a wiki-tree scan, so the
    1776 calls × ~4 ms = ~7 s consistently exceeded the 5 s
    ``ORIENT_SECTION_HARD_TIMEOUT_S`` cap and the section returned
    ``error: section_timeout_5.0s`` on every cold cache miss.

    Fix: build the candidates index once (~6 ms) and resolve in pure dict
    lookups + Path.exists() checks. Same answer, ~50× faster.
    """
    resolved_ctx = resolve_context(ctx)
    wiki_api.wiki_state.get_status_summary()

    candidates = wiki_api._list_article_candidates(resolved_ctx)  # one context-scoped full-tree scan
    wiki_dir = wiki_api._wiki_dir(resolved_ctx)

    by_track: dict[str, dict[str, Any]] = {}
    known_tracks = wiki_api._known_tracks(ctx=resolved_ctx)
    for track in known_tracks:
        slugs = wiki_api._track_slugs(track)
        if not slugs:
            continue
        compiled = 0
        for slug in slugs:
            slug_cands = candidates.get(slug)
            if not slug_cands:
                continue
            # Mirror _resolve_article: prefer domain-matching candidates,
            # fall back to any candidate. Take the lexicographically-first
            # path within the chosen group, then check it actually exists.
            domain_matches = [c for c in slug_cands if wiki_api._matches_track_domain(track, c["path"])]
            chosen = sorted(
                domain_matches or slug_cands,
                key=lambda item: item["path"],
            )[0]
            if (wiki_dir / chosen["path"]).exists():
                compiled += 1
        total = len(slugs)
        by_track[track] = {
            "compiled": compiled,
            "total": total,
            "pct": round(compiled / total * 100, 1) if total else 0,
        }
    return {"by_track": by_track}


def collect_governance_orient_data(ctx: MonitorContext | None = None) -> dict[str, int]:
    return collect_governance_summary(ctx=resolve_context(ctx))


def orient_sections() -> Mapping[str, OrientSection]:
    """The product orient sections, built from this module's current collectors."""
    module = sys.modules[__name__]
    return {
        "pipeline": OrientSection(
            module.collect_pipeline_orient_data, {"summary": {}}, True, 0.0, "fs", after="idle_prs"
        ),
        "wiki": OrientSection(module.collect_wiki_orient_data, {"by_track": {}}, False, 120.0, "fs", after="rollovers"),
        "governance": OrientSection(
            module.collect_governance_orient_data,
            GOVERNANCE_FALLBACK,
            False,
            120.0,
            "fs",
            after="wiki",
            lean=True,
            merge_meta=True,
        ),
    }


def _readable_file(path: os.PathLike[str]) -> bool:
    return os.path.isfile(path) and os.access(path, os.R_OK)


def health_fields(ctx: MonitorContext) -> dict[str, Any]:
    """Product fields of the orient health section."""
    return {"sources_db": _readable_file(product_roots(ctx).sources_db_path)}
