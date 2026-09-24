"""Collapse a GitHub status-check rollup to the latest run of each check.

Check-run identity is ``(workflowName, name)``. A non-Actions app with no
workflow (``appSlug``) uses ``(appSlug, name)``. A status context is
``context``. A partial identity is kept in full: dropping it would hide a
real failure when two workflows share a job name.

``github-actions`` without a workflow name stays partial on purpose. Every
Actions job shares that app slug, so using it would collapse different
workflows that reuse a job name.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def rollup_identity(entry: dict[str, Any]) -> tuple[str, ...] | None:
    """Stable identity, or ``None`` when the row must not be collapsed."""
    name = entry.get("name")
    if isinstance(name, str) and name.strip():
        workflow = entry.get("workflowName")
        if isinstance(workflow, str) and workflow.strip():
            return ("check", workflow.strip(), name.strip())
        app = entry.get("appSlug")
        if isinstance(app, str) and app.strip():
            return ("check", app.strip(), name.strip())
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
