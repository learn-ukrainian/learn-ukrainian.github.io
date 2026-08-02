"""Deterministic, promoted-only recall workflows over the context-link store.

Implements the Phase-2 workflows of ADR-018 / the rollout plan:

- ``search_past_work`` — bounded, Unicode-casefold ranked locator cards;
- ``explain_change`` — typed provenance traversal (commit ↔ receipt joins);
- ``prepare_handoff`` — a bounded capsule of verified locators/excerpts.

Every candidate is re-resolved against its canonical local system and its
canonical digest is recomputed before it may enter an LLM-facing result or
handoff capsule. Missing, stale, tombstoned, partial-terminal, unsupported,
or digest-mismatched evidence is omitted with a body-free machine reason.
Query text is never persisted and never echoed into any result payload.
Nothing here calls Entire, the network, GitHub, or any protected rail.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .model import LOCATOR_ID_RE, canonical_json
from .resolvers import REASON_SOURCE_MISSING, ResolutionError, reverify_link
from .store import ContextLinkStore

MAX_QUERY_BYTES = 256
MAX_SCAN_ROWS = 500
MAX_RESULTS = 10
MAX_HANDOFF_ITEMS = 5
MAX_CAPSULE_BYTES = 8192
MAX_EXPLAIN_DEPTH = 2
MAX_EXPLAIN_NODES = 50
MAX_HANDOFF_SEEDS = 500
MAX_SEARCH_OMISSIONS = 50

REASON_TOMBSTONED = "tombstoned"
REASON_HANDOFF_ITEM_CAP = "handoff_item_cap"
REASON_CAPSULE_BUDGET = "capsule_budget"

#: Weighted ranking facets, evaluated in this fixed declaration order.
_FACET_WEIGHTS: tuple[tuple[str, int], ...] = (
    ("title", 30),
    ("labels", 20),
    ("touched_paths", 15),
    ("repository", 12),
    ("document_path", 12),
    ("document_heading", 12),
    ("track", 10),
    ("stream_epic", 10),
    ("state", 8),
    ("source_kind", 8),
    ("actor", 8),
    ("model", 8),
    ("harness", 8),
    ("participants", 8),
    ("token_bucket", 4),
)

_EXACT_ID_SCORE = 1000
_CANONICAL_ID_SUBSTR_SCORE = 25
_NAMESPACE_SUBSTR_SCORE = 40
_GIT_SHA_SUBSTR_SCORE = 10
_KIND_SUBSTR_SCORE = 5


class RecallInputError(ValueError):
    """Caller input violated a bounded-workflow rule (never echoes the input)."""


class GateReject(Exception):
    """A candidate failed the re-resolve/digest gate with a machine reason."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    link: dict[str, Any]
    score: int
    matched_fields: tuple[str, ...]


def validate_query(query: Any) -> str:
    """Validate the bounded query and return its Unicode casefold needle."""
    if not isinstance(query, str) or not query.strip():
        raise RecallInputError("query_invalid")
    if "\x00" in query or len(query.encode("utf-8")) > MAX_QUERY_BYTES:
        raise RecallInputError("query_invalid")
    return query.casefold()


def _facet_values(facets: dict[str, Any], key: str) -> list[str]:
    value = facets.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def rank_candidate(link: dict[str, Any], needle: str) -> RankedCandidate:
    """Score one candidate deterministically against the casefold needle."""
    needle = needle.casefold()  # idempotent; callers pass an already-folded needle
    score = 0
    matched: list[str] = []
    canonical_id = str(link["canonical_id"]).casefold()
    git_sha = str(link.get("git_sha") or "").casefold()
    locator_id = str(link["locator_id"])
    if needle in (canonical_id, locator_id) or (git_sha and needle == git_sha):
        score += _EXACT_ID_SCORE
        matched.append("exact_id")
    else:
        if needle in canonical_id:
            score += _CANONICAL_ID_SUBSTR_SCORE
            matched.append("canonical_id")
        if git_sha and needle in git_sha:
            score += _GIT_SHA_SUBSTR_SCORE
            matched.append("git_sha")
    namespace = str(link["canonical_namespace"]).casefold()
    if needle in namespace:
        score += _NAMESPACE_SUBSTR_SCORE
        matched.append("canonical_namespace")
    if needle in str(link["kind"]).casefold():
        score += _KIND_SUBSTR_SCORE
        matched.append("kind")
    facets = link.get("facets") or {}
    for facet_key, weight in _FACET_WEIGHTS:
        if any(needle in value.casefold() for value in _facet_values(facets, facet_key)):
            score += weight
            matched.append(facet_key)
    return RankedCandidate(link=link, score=score, matched_fields=tuple(matched))


def _verified_card(
    store: ContextLinkStore,
    link: dict[str, Any],
    *,
    repo: Path,
    acp_root: Path | None,
    rollover_root: Path | None,
    fleet_root: Path | None,
    monitor_root: Path | None,
    issue_cache_path: Path | None,
    now: datetime | None,
) -> dict[str, Any]:
    """Re-check promotion state and re-resolve/recompute the canonical digest."""
    fresh = store.lookup(str(link["locator_id"]))
    if fresh is None:
        raise GateReject(REASON_TOMBSTONED)
    try:
        excerpt = reverify_link(
            fresh,
            repo=repo,
            acp_root=acp_root,
            rollover_root=rollover_root,
            fleet_root=fleet_root,
            monitor_root=monitor_root,
            issue_cache_path=issue_cache_path,
            now=now,
        )
    except ResolutionError as exc:
        raise GateReject(exc.reason) from exc
    return {
        "locator_id": fresh["locator_id"],
        "kind": fresh["kind"],
        "canonical_namespace": fresh["canonical_namespace"],
        "canonical_id": fresh["canonical_id"],
        "canonical_digest": fresh["canonical_digest"],
        "entire_checkpoint_id": fresh["entire_checkpoint_id"],
        "git_sha": fresh["git_sha"],
        "facets": fresh["facets"],
        "excerpt": excerpt,
    }


def _omitted(locator_id: str, reason: str) -> dict[str, str]:
    return {"locator_id": locator_id, "reason": reason}


# ── search-past-work ─────────────────────────────────────────────────────────


def search_past_work(
    store: ContextLinkStore,
    query: str,
    *,
    repo: Path,
    acp_root: Path | None,
    rollover_root: Path | None = None,
    fleet_root: Path | None = None,
    monitor_root: Path | None = None,
    issue_cache_path: Path | None = None,
    limit: int = MAX_RESULTS,
    scan_limit: int = MAX_SCAN_ROWS,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Rank promoted candidates and return verified locator cards only.

    The query is used only as an in-memory ranking needle: it is never
    persisted and never echoed into the result payload.
    """
    needle = validate_query(query)
    capped_scan = max(0, min(int(scan_limit), MAX_SCAN_ROWS))
    capped_limit = max(0, min(int(limit), MAX_RESULTS))
    candidates = store.candidates(limit=capped_scan)
    ranked = sorted(
        (rank_candidate(link, needle) for link in candidates),
        key=lambda entry: (-entry.score, entry.link["locator_id"]),
    )
    results: list[dict[str, Any]] = []
    omitted: list[dict[str, str]] = []
    omissions_truncated = False
    for entry in ranked:
        if entry.score <= 0 or len(results) >= capped_limit:
            break
        locator_id = entry.link["locator_id"]
        try:
            card = _verified_card(
                store,
                entry.link,
                repo=repo,
                acp_root=acp_root,
                rollover_root=rollover_root,
                fleet_root=fleet_root,
                monitor_root=monitor_root,
                issue_cache_path=issue_cache_path,
                now=now,
            )
        except GateReject as exc:
            if len(omitted) < MAX_SEARCH_OMISSIONS:
                omitted.append(_omitted(locator_id, exc.reason))
            else:
                omissions_truncated = True
            continue
        card["score"] = entry.score
        card["matched_fields"] = list(entry.matched_fields)
        results.append(card)
    return {
        "schema": "ec-search.v1",
        "results": results,
        "omitted": omitted,
        "omissions_truncated": omissions_truncated,
        "scanned": len(candidates),
        "limit": capped_limit,
    }


# ── explain-change ───────────────────────────────────────────────────────────


def _resolve_seeds(
    store: ContextLinkStore,
    *,
    locator_id: str | None,
    canonical_id: str | None,
    git_sha: str | None,
) -> list[dict[str, Any]]:
    if locator_id is not None:
        if not LOCATOR_ID_RE.fullmatch(locator_id):
            raise RecallInputError("seed_invalid")
        found = store.lookup(locator_id)
        return [found] if found is not None else []
    candidates = store.candidates(limit=MAX_SCAN_ROWS)
    if canonical_id is not None:
        if not isinstance(canonical_id, str) or not canonical_id:
            raise RecallInputError("seed_invalid")
        return sorted(
            (link for link in candidates if link["canonical_id"] == canonical_id),
            key=lambda link: link["locator_id"],
        )[:MAX_EXPLAIN_NODES]
    if git_sha is not None:
        if (
            not isinstance(git_sha, str)
            or len(git_sha) != 40
            or any(character not in "0123456789abcdef" for character in git_sha)
        ):
            raise RecallInputError("seed_invalid")
        needle = git_sha.lower()
        return sorted(
            (link for link in candidates if link.get("git_sha") == needle or link["canonical_id"] == needle),
            key=lambda link: link["locator_id"],
        )[:MAX_EXPLAIN_NODES]
    raise RecallInputError("seed_invalid")


def explain_change(
    store: ContextLinkStore,
    *,
    locator_id: str | None = None,
    canonical_id: str | None = None,
    git_sha: str | None = None,
    repo: Path,
    acp_root: Path | None,
    rollover_root: Path | None = None,
    fleet_root: Path | None = None,
    monitor_root: Path | None = None,
    issue_cache_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Traverse typed provenance joins from an exact seed identifier.

    The traversal is a bounded breadth-first walk over promoted links using
    the explicit typed joins (shared commit SHA, commit cross-reference,
    shared canonical ID). Every visited node is re-verified before it enters
    the result; unverifiable nodes are omitted and their edges dropped.
    """
    seeds = _resolve_seeds(store, locator_id=locator_id, canonical_id=canonical_id, git_sha=git_sha)
    if not seeds:
        return {"schema": "ec-explain.v1", "found": False}
    seed_ids = {str(seed["locator_id"]) for seed in seeds}
    nodes: dict[str, dict[str, Any]] = {str(seed["locator_id"]): seed for seed in seeds}
    edges: set[tuple[str, str, str]] = set()
    relation_rows_examined = 0
    truncation_reasons: set[str] = set()
    frontier = sorted(seed_ids)
    depth = 0
    while frontier and depth < MAX_EXPLAIN_DEPTH and len(nodes) < MAX_EXPLAIN_NODES:
        next_frontier: list[str] = []
        for current_id in frontier:
            related_scan = store.find_related(nodes[current_id])
            relation_rows_examined += related_scan.examined
            if related_scan.truncated:
                truncation_reasons.add("relation_scan_cap")
            for related, join in related_scan.items:
                related_id = str(related["locator_id"])
                edges.add((current_id, related_id, join))
                if related_id not in nodes and len(nodes) < MAX_EXPLAIN_NODES:
                    nodes[related_id] = related
                    next_frontier.append(related_id)
                elif related_id not in nodes:
                    truncation_reasons.add("node_cap")
        frontier = next_frontier
        depth += 1
    if frontier:
        truncation_reasons.add("depth_cap")

    verified: dict[str, dict[str, Any]] = {}
    omitted: list[dict[str, str]] = []
    for node_id in sorted(nodes):
        try:
            verified[node_id] = _verified_card(
                store,
                nodes[node_id],
                repo=repo,
                acp_root=acp_root,
                rollover_root=rollover_root,
                fleet_root=fleet_root,
                monitor_root=monitor_root,
                issue_cache_path=issue_cache_path,
                now=now,
            )
        except GateReject as exc:
            omitted.append(_omitted(node_id, exc.reason))
    kept_edges = [
        {"from": source, "to": target, "join": join}
        for source, target, join in sorted(edges)
        if source in verified and target in verified
    ]
    return {
        "schema": "ec-explain.v1",
        "found": True,
        "seeds": [verified[node_id] for node_id in sorted(seed_ids) if node_id in verified],
        "nodes": [verified[node_id] for node_id in sorted(verified)],
        "edges": kept_edges,
        "omitted": omitted,
        "depth": depth,
        "relation_scan": {
            "examined": relation_rows_examined,
            "truncated": "relation_scan_cap" in truncation_reasons,
        },
        "complete": not truncation_reasons,
        "truncation_reasons": sorted(truncation_reasons),
    }


# ── prepare-handoff ──────────────────────────────────────────────────────────


def prepare_handoff(
    store: ContextLinkStore,
    locator_ids: list[str],
    *,
    repo: Path,
    acp_root: Path | None,
    rollover_root: Path | None = None,
    fleet_root: Path | None = None,
    monitor_root: Path | None = None,
    issue_cache_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a bounded capsule of verified locator cards and excerpts.

    The capsule holds at most ``MAX_HANDOFF_ITEMS`` items and at most
    ``MAX_CAPSULE_BYTES`` of canonical JSON. Items are processed in
    deterministic locator-ID order; an item that would exceed the byte
    budget is omitted whole, so the serialized capsule is always valid
    JSON and never a truncated stream. A handoff is never a summary.
    """
    for locator_id in locator_ids:
        if not isinstance(locator_id, str) or not LOCATOR_ID_RE.fullmatch(locator_id):
            raise RecallInputError("locator_id_invalid")
    unique_locator_ids = sorted(set(locator_ids))
    if len(unique_locator_ids) > MAX_HANDOFF_SEEDS:
        raise RecallInputError("handoff_seed_limit")
    capsule: dict[str, Any] = {
        "schema": "ec-handoff.v1",
        "items": [],
        "omitted": [],
        "complete": True,
        "omissions_truncated": False,
    }
    items: list[dict[str, Any]] = capsule["items"]
    omitted: list[dict[str, str]] = capsule["omitted"]

    def append_omission(locator_id: str, reason: str) -> None:
        capsule["complete"] = False
        omitted.append(_omitted(locator_id, reason))
        if len(canonical_json(capsule).encode("utf-8")) <= MAX_CAPSULE_BYTES:
            return
        omitted.pop()
        capsule["omissions_truncated"] = True
        while omitted and len(canonical_json(capsule).encode("utf-8")) > MAX_CAPSULE_BYTES:
            omitted.pop()

    for locator_id in unique_locator_ids:
        if len(items) >= MAX_HANDOFF_ITEMS:
            append_omission(locator_id, REASON_HANDOFF_ITEM_CAP)
            continue
        link = store.lookup(locator_id)
        if link is None:
            append_omission(locator_id, REASON_SOURCE_MISSING)
            continue
        try:
            card = _verified_card(
                store,
                link,
                repo=repo,
                acp_root=acp_root,
                rollover_root=rollover_root,
                fleet_root=fleet_root,
                monitor_root=monitor_root,
                issue_cache_path=issue_cache_path,
                now=now,
            )
        except GateReject as exc:
            append_omission(locator_id, exc.reason)
            continue
        items.append(card)
        if len(canonical_json(capsule).encode("utf-8")) > MAX_CAPSULE_BYTES:
            items.pop()
            append_omission(locator_id, REASON_CAPSULE_BUDGET)
    if len(canonical_json(capsule).encode("utf-8")) > MAX_CAPSULE_BYTES:
        raise AssertionError("handoff capsule exceeded its hard byte cap")
    return capsule


def serialize_capsule(capsule: dict[str, Any]) -> str:
    """Deterministic canonical-JSON serialization of a handoff capsule."""
    return canonical_json(capsule)
