"""Fail-open projection of canonical, terminal ACP receipts.

ACP commits its own lifecycle first. This module runs only after that terminal
commit and writes to the disposable context-link projection; projection
failure can never change ACP state or its returned result.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .model import LinkKind, SchemaError, isoformat_z, parse_timestamp, utc_now
from .paths import projection_path
from .resolvers import ResolutionError, resolve_acp_conversation
from .store import AdmitOutcome, ContextLinkStore

ENV_DISABLED = "ENTIRE_CONTEXT_DISABLED"
MAX_RECONCILE_ROWS = 500


def _disabled() -> bool:
    return os.environ.get(ENV_DISABLED, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def project_terminal_acp_receipt(
    *,
    conversation_id: str,
    acp_root: Path,
    repo_root: Path,
    db_path: Path | None = None,
    actor: str = "acp-runtime",
) -> dict[str, Any]:
    """Project one exact terminal receipt idempotently after ACP completion."""
    if _disabled():
        return {"outcome": "skipped", "reason": "projection_disabled"}
    store = ContextLinkStore(projection_path(repo_root, db_path))
    try:
        resolution = resolve_acp_conversation(
            conversation_id,
            acp_root=Path(acp_root),
        )
    except ResolutionError as exc:
        _tombstone_exact(store, conversation_id, reason=exc.reason, actor=actor)
        _record_sync(
            store,
            operation="live",
            outcome="failed",
            reason=exc.reason,
            examined=1,
            skipped=1,
        )
        return {"outcome": "skipped", "reason": exc.reason}
    try:
        result = store.admit(resolution.link, resolution.verification, actor=actor)
        successful = result.outcome in {
            AdmitOutcome.PROMOTED,
            AdmitOutcome.ALREADY_PROMOTED,
        }
        tombstoned = (
            _tombstone_exact(
                store,
                conversation_id,
                reason="digest_mismatch",
                actor=actor,
                keep_locator=resolution.link.locator_id,
            )
            if successful
            else 0
        )
        _record_sync(
            store,
            operation="live",
            outcome="succeeded" if successful else "failed",
            reason="" if successful else (result.reason or result.outcome.value),
            source_latest_at=str(resolution.link.facets.get("event_ts") or "") or None,
            examined=1,
            changed=int(result.outcome is AdmitOutcome.PROMOTED) + tombstoned,
        )
    except (OSError, sqlite3.Error, KeyError, TypeError, ValueError):
        return {"outcome": "skipped", "reason": "projection_unavailable"}
    return {**result.to_dict(), "tombstoned": tombstoned}


def _terminal_complete_ids(
    acp_root: Path,
    *,
    limit: int,
    attempt: int = 0,
) -> tuple[list[str], bool, str | None]:
    db_path = Path(acp_root).expanduser().resolve() / "comms.sqlite3"
    if not db_path.is_file():
        raise ResolutionError("source_missing")
    capped = max(0, min(int(limit), MAX_RECONCILE_ROWS))
    with sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True) as connection:
        where_latest_complete = (
            " FROM acp_conversation_events AS event"
            " WHERE event.sequence = ("
            "SELECT MAX(latest.sequence) FROM acp_conversation_events AS latest"
            " WHERE latest.conversation_id = event.conversation_id"
            ") AND event.state = 'COMPLETE'"
        )
        total = int(connection.execute("SELECT COUNT(*)" + where_latest_complete).fetchone()[0])
        visible: list[tuple[Any, ...]] = []
        if capped and total:
            offset = (max(0, int(attempt)) * capped) % total
            visible = connection.execute(
                "SELECT event.conversation_id, event.created_at"
                + where_latest_complete
                + " ORDER BY event.conversation_id LIMIT ? OFFSET ?",
                (capped, offset),
            ).fetchall()
            if len(visible) < min(capped, total):
                visible.extend(
                    connection.execute(
                        "SELECT event.conversation_id, event.created_at"
                        + where_latest_complete
                        + " ORDER BY event.conversation_id LIMIT ?",
                        (min(capped, total) - len(visible),),
                    ).fetchall()
                )
    timestamps: list[datetime] = []
    for row in visible:
        try:
            timestamps.append(parse_timestamp(str(row[1])))
        except (SchemaError, TypeError, ValueError):
            continue
    source_latest_at = isoformat_z(max(timestamps)) if timestamps else None
    return [str(row[0]) for row in visible], total > capped, source_latest_at


def _fair_window(
    source_ids: list[str],
    projected_ids: list[str],
    *,
    limit: int,
    attempt: int,
) -> list[str]:
    """Interleave rotating source/projection pages without starving either."""
    if limit <= 0:
        return []
    lanes = (source_ids, projected_ids) if attempt % 2 == 0 else (projected_ids, source_ids)
    selected: list[str] = []
    seen: set[str] = set()
    for index in range(max(map(len, lanes), default=0)):
        for lane in lanes:
            if index >= len(lane) or lane[index] in seen:
                continue
            seen.add(lane[index])
            selected.append(lane[index])
            if len(selected) == limit:
                return selected
    return selected


def _tombstone_exact(
    store: ContextLinkStore,
    conversation_id: str,
    *,
    reason: str,
    actor: str,
    keep_locator: str | None = None,
) -> int:
    """Tombstone stale locators for one canonical ACP identity."""
    try:
        links, _truncated = store.promoted_for_canonical(
            LinkKind.ACP_CONVERSATION,
            conversation_id,
        )
    except sqlite3.Error:
        return 0
    changed = 0
    for link in links:
        locator_id = str(link["locator_id"])
        if locator_id == keep_locator:
            continue
        changed += int(store.tombstone(locator_id, reason=reason, actor=actor))
    return changed


def _record_sync(
    store: ContextLinkStore,
    *,
    operation: str,
    outcome: str,
    reason: str = "",
    source_latest_at: str | None = None,
    examined: int = 0,
    changed: int = 0,
    skipped: int = 0,
    truncated: bool = False,
    limit: int = 0,
    dangling: int = 0,
) -> None:
    """Best-effort observability; telemetry never changes projection results."""
    try:
        store.record_projection_sync(
            source_kind=LinkKind.ACP_CONVERSATION,
            operation=operation,
            outcome=outcome,
            reason=reason,
            source_latest_at=source_latest_at,
            examined=examined,
            changed=changed,
            skipped=skipped,
            truncated=truncated,
            limit=limit,
            dangling=dangling,
            now=utc_now(),
        )
    except (OSError, sqlite3.Error, SchemaError, KeyError, TypeError, ValueError):
        return


def reconcile_terminal_acp_receipts(
    *,
    acp_root: Path,
    repo_root: Path,
    db_path: Path | None = None,
    limit: int = MAX_RECONCILE_ROWS,
    actor: str = "acp-reconcile",
) -> dict[str, Any]:
    """Recover any terminal ACP receipts missed by the post-commit callback."""
    if _disabled():
        return {"outcome": "skipped", "reason": "projection_disabled"}
    capped = max(0, min(int(limit), MAX_RECONCILE_ROWS))
    store = ContextLinkStore(projection_path(repo_root, db_path))
    prior_attempts = 0
    if store.db_path.is_file():
        try:
            prior_attempts = int(store.status()["projection_health"]["acp"]["attempts"])
        except (sqlite3.Error, KeyError, TypeError, ValueError):
            return {"outcome": "skipped", "reason": "projection_unavailable"}
    page_attempt = prior_attempts if capped > 1 else prior_attempts // 2
    try:
        complete_ids, source_truncated, source_latest_at = _terminal_complete_ids(
            acp_root,
            limit=capped,
            attempt=page_attempt,
        )
    except ResolutionError as exc:
        if store.db_path.is_file():
            _record_sync(store, operation="reconcile", outcome="failed", reason=exc.reason, limit=capped)
        return {"outcome": "skipped", "reason": exc.reason}
    except sqlite3.Error:
        if store.db_path.is_file():
            _record_sync(store, operation="reconcile", outcome="failed", reason="source_unreadable", limit=capped)
        return {"outcome": "skipped", "reason": "source_unreadable"}
    try:
        existing, projection_truncated = (
            store.promoted_for_kind(
                LinkKind.ACP_CONVERSATION,
                limit=capped,
                attempt=page_attempt,
            )
            if store.db_path.is_file()
            else ([], False)
        )
    except (sqlite3.Error, KeyError, TypeError, ValueError):
        return {"outcome": "skipped", "reason": "projection_unavailable"}
    existing_by_id: dict[str, list[dict[str, Any]]] = {}
    for link in existing:
        existing_by_id.setdefault(str(link["canonical_id"]), []).append(link)
    projected_ids = sorted(existing_by_id)
    conversation_ids = _fair_window(
        complete_ids,
        projected_ids,
        limit=capped,
        attempt=prior_attempts,
    )
    truncated = source_truncated or projection_truncated or (
        len(set(complete_ids) | set(projected_ids)) > capped
    )
    counts = {
        AdmitOutcome.PROMOTED.value: 0,
        AdmitOutcome.ALREADY_PROMOTED.value: 0,
        "tombstoned": 0,
        "skipped": 0,
    }
    reasons: dict[str, int] = {}
    for conversation_id in conversation_ids:
        try:
            resolution = resolve_acp_conversation(conversation_id, acp_root=Path(acp_root))
        except ResolutionError as exc:
            changed = _tombstone_exact(store, conversation_id, reason=exc.reason, actor=actor)
            counts["tombstoned"] += changed
            if not changed:
                counts["skipped"] += 1
            reasons[exc.reason] = reasons.get(exc.reason, 0) + 1
            continue
        try:
            admitted = store.admit(resolution.link, resolution.verification, actor=actor)
            counts[admitted.outcome.value] = counts.get(admitted.outcome.value, 0) + 1
            stale = _tombstone_exact(
                store,
                conversation_id,
                reason="digest_mismatch",
                actor=actor,
                keep_locator=resolution.link.locator_id,
            )
            counts["tombstoned"] += stale
            if stale:
                reasons["digest_mismatch"] = reasons.get("digest_mismatch", 0) + stale
        except (OSError, sqlite3.Error, SchemaError, KeyError, TypeError, ValueError):
            counts["skipped"] += 1
            reasons["projection_unavailable"] = reasons.get("projection_unavailable", 0) + 1
    changed = counts[AdmitOutcome.PROMOTED.value] + counts["tombstoned"]
    dangling = reasons.get("projection_unavailable", 0)
    _record_sync(
        store,
        operation="reconcile",
        outcome="succeeded",
        source_latest_at=source_latest_at,
        examined=len(conversation_ids),
        changed=changed,
        skipped=counts["skipped"],
        truncated=truncated,
        limit=capped,
        dangling=dangling,
    )
    lag_seconds = 0 if source_latest_at is not None and not truncated and dangling == 0 else None
    return {
        "outcome": "reconciled",
        "examined": len(conversation_ids),
        "counts": counts,
        "reasons": dict(sorted(reasons.items())),
        "truncated": truncated,
        "limit": capped,
        "source_latest_at": source_latest_at,
        "lag_seconds": lag_seconds,
    }
