"""Deterministic relationship extraction and dependency-cycle detection."""

from __future__ import annotations

import re
from typing import Any

from scripts.work import SOURCE_PUBLIC, WORK_ID_PREFIX

_SUPERSEDED_BY_RE = re.compile(
    r"(?:superseded[- ]?by|replaced[- ]?by|obsoleted[- ]?by)\s*:?\s*#(\d+)",
    re.IGNORECASE,
)
_SUPERSEDES_RE = re.compile(
    r"(?:supersedes|replaces|obsoletes)\s*:?\s*#(\d+)",
    re.IGNORECASE,
)
_DUPLICATE_RE = re.compile(
    r"(?:duplicate of|duplicates)\s*:?\s*#(\d+)",
    re.IGNORECASE,
)
_BLOCKS_RE = re.compile(
    r"(?:blocks)\s*:?\s*#(\d+)",
    re.IGNORECASE,
)
_BLOCKED_BY_RE = re.compile(
    r"(?:blocked by|depends on|waiting on)\s*:?\s*#(\d+)",
    re.IGNORECASE,
)


def make_work_id(
    source_id: str,
    repository_id: str,
    resource_kind: str,
    remote_id: str | int,
) -> str:
    return (
        f"{WORK_ID_PREFIX}:{source_id}:{repository_id}:{resource_kind}:{remote_id}"
    )


def issue_work_id(repository_id: str, number: int | str) -> str:
    return make_work_id(SOURCE_PUBLIC, repository_id, "issue", str(number))


def parse_issue_work_id(work_id: str | None) -> tuple[str, int] | None:
    """Parse an issue work_id into (repository_id, issue_number)."""
    if not work_id or not isinstance(work_id, str):
        return None
    parts = work_id.split(":")
    if len(parts) == 5 and parts[0] == WORK_ID_PREFIX and parts[1] == SOURCE_PUBLIC and parts[3] == "issue":
        try:
            return parts[2], int(parts[4])
        except ValueError:
            return None
    return None


def pr_work_id(repository_id: str, number: int | str) -> str:
    return make_work_id(SOURCE_PUBLIC, repository_id, "pr", str(number))


def task_work_id(repository_id: str, task_id: str) -> str:
    return make_work_id(SOURCE_PUBLIC, repository_id, "task", task_id)


def review_work_id(repository_id: str, review_id: str) -> str:
    return make_work_id(SOURCE_PUBLIC, repository_id, "review", review_id)


def extract_body_relations(
    body: str | None,
    *,
    repository_id: str,
    self_number: int,
) -> list[dict[str, str]]:
    """Extract source-provided relations from public issue body text."""
    if not body:
        return []
    rels: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(rel_type: str, number: str, evidence: str) -> None:
        if number == str(self_number):
            return
        key = (rel_type, number)
        if key in seen:
            return
        seen.add(key)
        rels.append(
            {
                "type": rel_type,
                "target_id": issue_work_id(repository_id, number),
                "evidence": evidence,
            }
        )

    for match in _SUPERSEDED_BY_RE.finditer(body):
        add("superseded_by", match.group(1), "issue_body")
    for match in _SUPERSEDES_RE.finditer(body):
        add("supersedes", match.group(1), "issue_body")
    for match in _DUPLICATE_RE.finditer(body):
        add("duplicate_of", match.group(1), "issue_body")
    for match in _BLOCKS_RE.finditer(body):
        add("blocks", match.group(1), "issue_body")
    for match in _BLOCKED_BY_RE.finditer(body):
        add("blocked_by", match.group(1), "issue_body")
    return rels


def invert_relationships(items: list[dict[str, Any]]) -> None:
    """Add inverse edges when the target object exists in the item set."""
    by_id = {item["work_id"]: item for item in items}
    inverse = {
        "blocks": "blocked_by",
        "blocked_by": "blocks",
        "supersedes": "superseded_by",
        "superseded_by": "supersedes",
        "duplicate_of": "related",
        "related": "related",
    }
    for item in items:
        for rel in list(item.get("relationships") or []):
            target = by_id.get(rel.get("target_id") or "")
            if target is None:
                continue
            inv = inverse.get(rel["type"])
            if inv is None:
                continue
            existing = {
                (r.get("type"), r.get("target_id")) for r in target.get("relationships") or []
            }
            key = (inv, item["work_id"])
            if key in existing:
                continue
            target.setdefault("relationships", []).append(
                {
                    "type": inv,
                    "target_id": item["work_id"],
                    "evidence": f"inverse:{rel.get('evidence') or 'source'}",
                }
            )


def detect_dependency_cycles(items: list[dict[str, Any]]) -> list[list[str]]:
    """Detect cycles on blocks/blocked_by edges; returns sorted cycle node lists."""
    graph: dict[str, set[str]] = {item["work_id"]: set() for item in items}
    for item in items:
        src = item["work_id"]
        for rel in item.get("relationships") or []:
            if rel.get("type") in {"blocks", "blocked_by"} and rel.get("target_id") in graph:
                if rel["type"] == "blocks":
                    graph[src].add(rel["target_id"])
                else:
                    graph[rel["target_id"]].add(src)

    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> None:
        visiting.add(node)
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            if nxt in visiting:
                if nxt in stack:
                    idx = stack.index(nxt)
                    cycle = [*stack[idx:], nxt]
                    # Canonicalize cycle start for determinism.
                    body = cycle[:-1]
                    start = body.index(min(body))
                    canon = body[start:] + body[:start]
                    cycles.append(canon)
                continue
            if nxt not in visited:
                dfs(nxt)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        if node not in visited:
            dfs(node)

    # Deduplicate identical cycles.
    unique: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for cycle in cycles:
        key = tuple(cycle)
        if key in seen:
            continue
        seen.add(key)
        unique.append(cycle)
    return unique


def collect_missing_blocked_by_issue_numbers(
    items: list[dict[str, Any]],
    *,
    repository_id: str | None = None,
) -> list[int]:
    """Collect issue numbers targeted by 'blocked_by' edges that are absent from items.

    Only targets matching the given repository (if provided) are returned.
    Cross-repo or unparseable target IDs cannot be resolved by the repository
    lookup and will stay conservative in `resolve_live_blockers`.
    """
    known_work_ids = {item["work_id"] for item in items if isinstance(item, dict) and "work_id" in item}
    missing: set[int] = set()
    for item in items:
        if not isinstance(item, dict) or item.get("resource_kind") != "issue":
            continue
        for rel in item.get("relationships") or []:
            if not isinstance(rel, dict) or rel.get("type") != "blocked_by":
                continue
            target_id = rel.get("target_id")
            if not target_id or target_id in known_work_ids:
                continue
            parsed = parse_issue_work_id(target_id)
            if parsed is None:
                continue
            target_repo, number = parsed
            if repository_id is not None and target_repo != repository_id:
                continue
            missing.add(number)
    return sorted(missing)


def resolve_live_blockers(
    items: list[dict[str, Any]],
    target_lifecycle_by_id: dict[str | int, str] | None = None,
) -> None:
    """Demote ``blocked_by`` flags whose target issue is closed (#7177/#7185).

    A ``Depends on #N`` / ``blocked by #N`` reference — body-derived, or
    inferred from another issue's ``blocks`` via `invert_relationships` — is
    only a *live* blocker while the target issue is still open. Call this
    after `invert_relationships` (so inferred edges are covered) and before
    health/safe-next-action derivation, which reads `flags["has_blocker"]`.

    Targets not present in this projection (paginated out, cross-repo,
    private-only, etc.) cannot be confirmed closed unless resolved via
    `target_lifecycle_by_id`. Any target whose state cannot be confirmed
    closed conservatively still counts as a blocker — this function only
    ever narrows `has_blocker`, never widens it, and never touches the
    `relationships` list itself (the closed edge stays visible as evidence).
    """
    lifecycle_by_id: dict[str | int, str] = {
        item["work_id"]: str(item.get("lifecycle") or "").lower()
        for item in items
        if item.get("resource_kind") == "issue"
    }
    if target_lifecycle_by_id:
        for k, v in target_lifecycle_by_id.items():
            state = str(v or "").lower()
            lifecycle_by_id[k] = state
            if isinstance(k, int) or (isinstance(k, str) and k.isdigit()):
                lifecycle_by_id[str(k)] = state
                lifecycle_by_id[int(k)] = state

    for item in items:
        if item.get("resource_kind") != "issue":
            continue
        live = False
        for rel in item.get("relationships") or []:
            if rel.get("type") != "blocked_by":
                continue
            target_id = rel.get("target_id")
            if target_id and lifecycle_by_id.get(target_id) == "closed":
                continue
            parsed = parse_issue_work_id(target_id) if target_id else None
            if parsed and (
                lifecycle_by_id.get(parsed[1]) == "closed"
                or lifecycle_by_id.get(str(parsed[1])) == "closed"
            ):
                continue
            live = True
        item.setdefault("flags", {})["has_blocker"] = live


def annotate_cycles(items: list[dict[str, Any]], cycles: list[list[str]]) -> None:
    members = {node for cycle in cycles for node in cycle}
    for item in items:
        flags = item.setdefault("flags", {})
        if item["work_id"] in members:
            flags["dependency_cycle"] = True
            flags["cycle_ids"] = [
                c for c in cycles if item["work_id"] in c
            ]
        else:
            flags.setdefault("dependency_cycle", False)
