"""Issues map API router — grouped open issues with supersede metadata.

Mounted at /api/issues in main.py.

Endpoints:
    GET /api/issues/map         Open issues grouped by label category

Why this exists (Codex-6 / #1313): ``/api/orient.issues`` returns a
flat list of 10. `/api/state/issues` is about curriculum content
issues. Neither answers "what's my infra/pipeline/wiki queue look
like, and what's been superseded?" This endpoint shells out to ``gh
issue list`` with a rich JSON selection, buckets by label category,
and extracts ``superseded-by: #N`` / ``merged-in: PR #N`` hints from
issue bodies when present.

Read-only. Single 5-second ``gh`` call. Degrades gracefully to
``{"categories": {}, "error": "..."}`` when ``gh`` is unavailable.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from typing import Any

from fastapi import APIRouter, Query

from .config import PROJECT_ROOT

router = APIRouter(tags=["issues"])

# Categories driven by label prefixes we use in this repo. Anything
# not matching lands in "other" so new label schemes don't silently
# fall off the map.
_CATEGORY_ORDER: tuple[str, ...] = (
    "infrastructure",
    "pipeline",
    "content",
    "wiki",
    "agent",
    "priority:high",
    "other",
)

_SUPERSEDED_RE = re.compile(
    # ``superseded-by`` / ``supersedes`` / ``closes`` / ``replaces`` /
    # ``obsoletes``. Catches both the "this issue is-superseded-by X"
    # and "this issue supersedes X" phrasings (the latter flagged by
    # Codex on #1312 pre-merge as a regex gap).
    r"(?:superseded[- ]?by|supersedes|closes|replaces|obsoletes)"
    r"\s*:?\s*(?:standalone\s+)?#(\d+)",
    re.IGNORECASE,
)
_MERGED_IN_RE = re.compile(
    r"(?:merged[- ]?in|landed[- ]?in|shipped[- ]?in|fixed[- ]?in)\s*:?\s*(?:PR\s*)?#(\d+)",
    re.IGNORECASE,
)


def _run_gh(args: list[str], timeout_s: float = 5.0) -> tuple[int, str, str]:
    """Bounded ``gh`` call that never raises — see ``site_router._run``."""
    try:
        proc = subprocess.run(
            args,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"TimeoutExpired after {exc.timeout}s"
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return 127, "", f"{type(exc).__name__}: {exc}"


def _categorize(labels: list[str | None]) -> str:
    """Pick the most specific category a label set falls into.

    Order matters — we return the first match in ``_CATEGORY_ORDER``
    so an issue labeled both ``priority:high`` and ``infrastructure``
    bucketises as ``infrastructure`` (the domain label wins).
    """
    label_names = {str(lbl).lower() for lbl in labels if lbl}
    for cat in _CATEGORY_ORDER:
        if cat == "other":
            continue
        if cat in label_names:
            return cat
        # Allow label prefixes: "priority:high" matches "priority:high";
        # "agent:codex" matches "agent".
        if any(name.startswith(cat + ":") for name in label_names):
            return cat
    return "other"


def _extract_supersede_hint(body: str | None) -> dict[str, Any]:
    """Pull ``superseded-by: #N`` and ``merged-in: PR #N`` hints from body."""
    if not body:
        return {}
    out: dict[str, Any] = {}
    m = _SUPERSEDED_RE.search(body)
    if m:
        out["superseded_by"] = int(m.group(1))
    m = _MERGED_IN_RE.search(body)
    if m:
        out["merged_in_pr"] = int(m.group(1))
    return out


def _fetch_issues(limit: int) -> dict[str, Any]:
    code, stdout, stderr = _run_gh(
        [
            "gh", "issue", "list",
            "--state", "open",
            "--limit", str(limit),
            "--json", "number,title,labels,body,createdAt,updatedAt,assignees,url",
        ],
    )
    if code != 0:
        return {
            "categories": {},
            "count": 0,
            "error": stderr.strip() or "gh issue list failed",
        }

    try:
        payload = json.loads(stdout or "[]")
    except json.JSONDecodeError as exc:
        return {"categories": {}, "count": 0, "error": f"invalid gh json: {exc}"}

    categories: dict[str, list[dict[str, Any]]] = {cat: [] for cat in _CATEGORY_ORDER}
    for item in payload:
        labels_raw = item.get("labels") or []
        label_names = [
            lbl.get("name") for lbl in labels_raw
            if isinstance(lbl, dict) and lbl.get("name")
        ]
        assignees = [
            a.get("login") for a in (item.get("assignees") or [])
            if isinstance(a, dict) and a.get("login")
        ]
        cat = _categorize(label_names)
        compact = {
            "number": item.get("number"),
            "title": item.get("title"),
            "labels": label_names,
            "assignees": assignees,
            "created_at": item.get("createdAt"),
            "updated_at": item.get("updatedAt"),
            "url": item.get("url"),
        }
        compact.update(_extract_supersede_hint(item.get("body")))
        categories[cat].append(compact)

    # Drop empty buckets from the response for readability.
    categories = {k: v for k, v in categories.items() if v}

    return {
        "count": sum(len(v) for v in categories.values()),
        "categories": categories,
        "category_order": list(_CATEGORY_ORDER),
    }


@router.get("/map")
async def issues_map(
    limit: int = Query(50, ge=1, le=200, description="Upper bound on issues to scan."),
):
    """Open issues grouped by category with superseded-by / merged-in hints.

    Returns ``{count, categories, category_order}``. Each issue entry
    carries its number, title, labels, assignees, timestamps, URL, and
    (when present in the body) ``superseded_by`` / ``merged_in_pr``
    integer references.

    Reviewer Codex-6 / #1313: makes queue management less manual.
    """
    return await asyncio.to_thread(_fetch_issues, limit)
