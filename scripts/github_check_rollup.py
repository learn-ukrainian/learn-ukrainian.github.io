"""Collapse a GitHub status-check rollup to the latest run of each check.

Check-run identity includes the head, app, workflow ID and check name when
REST provenance is available, or the workflow name for existing projections.
A non-Actions app with no workflow uses its app identity. A status context is
``context``. A partial identity is kept in full: dropping it would hide a
real failure when two workflows share a job name.

``github-actions`` without a workflow name stays partial on purpose. Every
Actions job shares that app slug, so using it would collapse different
workflows that reuse a job name.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit


def project_check_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve REST check provenance when building a status-check rollup."""
    projected = []
    for row in rows:
        app = row["app"] if isinstance(row.get("app"), dict) else {}
        projected.append({
            **row, "__typename": "CheckRun", "status": str(row.get("status") or "").upper(),
            "conclusion": str(row.get("conclusion") or "").upper(),
            "startedAt": row.get("started_at"), "completedAt": row.get("completed_at"),
            "appSlug": app.get("slug"), "appId": app.get("id"),
        })
    return projected


def bind_workflow_runs(
    rows: list[dict[str, Any]], head: str, repo: str, get_run: Callable[[int], object]
) -> list[dict[str, Any]] | None:
    """Attach workflow identity through exact-head, exact-suite Actions run reads.

    A details URL is only a locator. The fetched run must bind its ID, suite
    and head to the check before its workflow can identify a supersession.
    Missing identity stays partial; failed or conflicting proof is unknown.
    """
    cache = {}
    bound = []
    for row in rows:
        if not isinstance(row, dict) or row.get("head_sha") != head:
            return None
        item = dict(row)
        app = row.get("app")
        if not isinstance(app, dict):
            app = {}
        if app.get("id") == 15368 and app.get("slug") == "github-actions":
            url = urlsplit(str(row.get("details_url") or ""))
            prefix = f"/{repo}/actions/runs/"
            suffix = url.path.removeprefix(prefix).split("/")
            if url.netloc == "github.com" and url.path.startswith(prefix) and suffix[0].isdigit():
                run_id = int(suffix[0])
                if run_id not in cache:
                    cache[run_id] = get_run(run_id)
                run = cache[run_id]
                suite = row.get("check_suite")
                if (not isinstance(run, dict) or run.get("id") != run_id
                        or run.get("head_sha") != head or not isinstance(suite, dict)
                        or type(suite.get("id")) is not int or run.get("check_suite_id") != suite["id"]
                        or type(run.get("workflow_id")) is not int or run["workflow_id"] <= 0):
                    return None
                item["workflowId"] = run["workflow_id"]
                item["workflowName"] = run.get("name")
        bound.append(item)
    return bound


def rollup_identity(entry: dict[str, Any]) -> tuple[str, ...] | None:
    """Stable identity, or ``None`` when the row must not be collapsed."""
    name = entry.get("name")
    if isinstance(name, str) and name.strip():
        app = entry.get("appSlug")
        head = str(entry.get("head_sha") or "")
        workflow_id = entry.get("workflowId")
        if type(workflow_id) is int and workflow_id > 0:
            return ("check", head, str(app or ""), str(entry.get("appId") or ""), str(workflow_id), name.strip())
        workflow = entry.get("workflowName")
        if isinstance(workflow, str) and workflow.strip():
            return ("check", head, str(app or ""), str(entry.get("appId") or ""), "workflow", workflow.strip(), name.strip())
        if isinstance(app, str) and app.strip() and app != "github-actions":
            return ("check", head, "app", app.strip(), str(entry.get("appId") or ""), name.strip())
        return None
    context = entry.get("context")
    if isinstance(context, str) and context.strip():
        return ("status", context.strip())
    return None


def rollup_timestamp(entry: dict[str, Any]) -> datetime | None:
    """Latest-run key.

    Check runs use ``startedAt``, then ``completedAt``. Status contexts projected
    from commit statuses carry ``updatedAt`` and ``createdAt`` instead, so those
    fields are the fallback only for a status identity.
    """
    fields = ["startedAt", "completedAt"]
    identity = rollup_identity(entry)
    if identity is not None and identity[0] == "status":
        fields.extend(("updatedAt", "createdAt"))
    for field in fields:
        raw = entry.get(field)
        if not isinstance(raw, str) or not raw.strip():
            continue
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
    return None


def collapse_status_rollup(rollup: list[Any]) -> list[Any]:
    """One row per check identity, the latest by start time.

    Missing identity, a missing timestamp anywhere in the group, or a tie at
    the latest timestamp keeps every row in that group. A newer success must
    not erase an older failure unless the timestamps say which run won.
    """
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    order: list[tuple[str, ...]] = []
    kept: list[Any] = []
    for entry in rollup:
        if not isinstance(entry, dict):
            kept.append(entry)
            continue
        # Cancelled runs can leave an unexpanded matrix parent, not a real check.
        if "${{" in str(entry.get("name") or ""):
            continue
        identity = rollup_identity(entry)
        if identity is None:
            kept.append(entry)
            continue
        if identity not in grouped:
            grouped[identity] = []
            order.append(identity)
        grouped[identity].append(entry)
    for identity in order:
        group = grouped[identity]
        stamps = [rollup_timestamp(entry) for entry in group]
        if any(stamp is None for stamp in stamps):
            kept.extend(group)
            continue
        latest = max(stamp for stamp in stamps if stamp is not None)
        kept.extend(entry for entry, stamp in zip(group, stamps, strict=True) if stamp == latest)
    return kept


def group_collapsed_by_name(rollup: list[Any]) -> tuple[dict[str, list[dict[str, Any]]], list[Any]]:
    """Collapse, then keep every surviving row under its check name.

    The dict maps ``name`` or ``context`` to every row the collapse kept for
    that label, including timestamp ties and rows with no workflow. The list
    holds surviving values that are not named check dicts. Callers must fail
    a name when any of its rows is red or pending; list order is not a winner.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    other: list[Any] = []
    for entry in collapse_status_rollup(list(rollup)):
        if not isinstance(entry, dict):
            other.append(entry)
            continue
        raw = entry.get("name") or entry.get("context")
        name = raw.strip() if isinstance(raw, str) else ""
        if not name:
            other.append(entry)
            continue
        if name not in grouped:
            order.append(name)
            grouped[name] = []
        grouped[name].append(entry)
    return {name: grouped[name] for name in order}, other
