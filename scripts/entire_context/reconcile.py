"""Fail-open projection of canonical, terminal ACP receipts.

ACP commits its own lifecycle first. This module runs only after that terminal
commit and writes to the disposable context-link projection; projection
failure can never change ACP state or its returned result.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

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
    try:
        resolution = resolve_acp_conversation(
            conversation_id,
            acp_root=Path(acp_root),
        )
        result = ContextLinkStore(
            projection_path(repo_root, db_path)
        ).admit(resolution.link, resolution.verification, actor=actor)
    except ResolutionError as exc:
        return {"outcome": "skipped", "reason": exc.reason}
    except (OSError, sqlite3.Error, KeyError, TypeError, ValueError):
        return {"outcome": "skipped", "reason": "projection_unavailable"}
    return result.to_dict()


def _terminal_complete_ids(acp_root: Path, *, limit: int) -> list[str]:
    db_path = Path(acp_root).expanduser().resolve() / "comms.sqlite3"
    if not db_path.is_file():
        return []
    capped = max(0, min(int(limit), MAX_RECONCILE_ROWS))
    with sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True) as connection:
        rows = connection.execute(
            "SELECT event.conversation_id FROM acp_conversation_events AS event"
            " WHERE event.sequence = ("
            "SELECT MAX(latest.sequence) FROM acp_conversation_events AS latest"
            " WHERE latest.conversation_id = event.conversation_id"
            ") AND event.state = 'COMPLETE'"
            " ORDER BY event.conversation_id LIMIT ?",
            (capped,),
        ).fetchall()
    return [str(row[0]) for row in rows]


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
    try:
        conversation_ids = _terminal_complete_ids(acp_root, limit=limit)
    except sqlite3.Error:
        return {"outcome": "skipped", "reason": "source_unreadable"}
    counts = {
        AdmitOutcome.PROMOTED.value: 0,
        AdmitOutcome.ALREADY_PROMOTED.value: 0,
        "skipped": 0,
    }
    reasons: dict[str, int] = {}
    for conversation_id in conversation_ids:
        result = project_terminal_acp_receipt(
            conversation_id=conversation_id,
            acp_root=acp_root,
            repo_root=repo_root,
            db_path=db_path,
            actor=actor,
        )
        outcome = str(result["outcome"])
        counts[outcome] = counts.get(outcome, 0) + 1
        reason = str(result.get("reason") or "")
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "outcome": "reconciled",
        "examined": len(conversation_ids),
        "counts": counts,
        "reasons": dict(sorted(reasons.items())),
    }
