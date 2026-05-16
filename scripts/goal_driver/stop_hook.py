"""Stop-hook entrypoint for the /goal driver.

Reads Claude Code's Stop-hook JSON payload on stdin, finds the last
status line emitted in the transcript, and emits ``additionalContext``
for the next turn:

* GOAL_STATUS + any in-flight dispatch in ``/api/delegate/active`` →
  next turn is reminded "active dispatch detected" so it does NOT
  increment ``no_progress`` (issue #1933 item 2).
* GOAL_WAIT signal=... → annotation pointing the next turn at the
  watcher (issue #1933 item 1).
* GOAL_DONE / GOAL_ABORT → no extra context (terminal). State-file
  cleanup ships in commit 3 of this PR.

The hook NEVER blocks Stop. /goal's native predicate enforcement is
unchanged; this hook only annotates state so the agent's own counters
stay honest under async work.

Output: a single JSON object on stdout iff there is something useful
to tell the next turn; empty stdout otherwise. Always exits 0 — a hook
crash must never be the reason a /goal run cannot stop.

Tested via ``tests/test_goal_driver_stop_hook.py``.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from scripts.goal_driver.status_lines import (
    STATUS_KIND,
    WAIT_KIND,
    StatusLine,
    find_last_status_line,
)

MONITOR_API = os.environ.get("MONITOR_API_URL", "http://localhost:8765")
DELEGATE_ACTIVE_PATH = "/api/delegate/active"
TRANSCRIPT_TAIL_BYTES = 64 * 1024  # last 64KB is plenty for the most recent turn
DELEGATE_HTTP_TIMEOUT_S = 2.0


def main(stdin: str | None = None) -> int:
    """Hook entry. ``stdin`` is provided in tests; production reads sys.stdin."""
    payload_text = stdin if stdin is not None else sys.stdin.read()
    try:
        payload = json.loads(payload_text) if payload_text.strip() else {}
    except json.JSONDecodeError:
        return 0  # malformed input — never block Stop

    transcript_path = _resolve_transcript_path(payload)
    if transcript_path is None or not transcript_path.exists():
        return 0

    last = _last_status_from_transcript(transcript_path)
    if last is None:
        return 0

    annotation = _build_annotation(last)
    if annotation:
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "Stop",
                    "additionalContext": annotation,
                }
            },
            sys.stdout,
        )
    return 0


def _resolve_transcript_path(payload: dict[str, Any]) -> Path | None:
    """Find the JSONL transcript for this session.

    Claude Code 2.1.x passes ``transcript_path`` directly on most hooks;
    earlier wire versions only carried ``session_id``. Support both so
    the hook keeps working across upgrades.
    """
    direct = payload.get("transcript_path")
    if isinstance(direct, str) and direct:
        return Path(direct)

    session_id = payload.get("session_id")
    project_dir = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR")
    if not (isinstance(session_id, str) and session_id and isinstance(project_dir, str)):
        return None
    project_slug = project_dir.replace("/", "-")
    candidate = Path.home() / ".claude" / "projects" / project_slug / f"{session_id}.jsonl"
    return candidate if candidate.exists() else None


def _last_status_from_transcript(transcript_path: Path) -> StatusLine | None:
    """Scan the assistant text in the last ~64KB of the transcript."""
    try:
        with transcript_path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - TRANSCRIPT_TAIL_BYTES))
            tail = handle.read().decode("utf-8", errors="replace")
    except OSError:
        return None

    assistant_chunks: list[str] = []
    for line in tail.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        text = _extract_assistant_text(event)
        if text:
            assistant_chunks.append(text)

    if not assistant_chunks:
        return None
    return find_last_status_line("\n".join(assistant_chunks))


def _extract_assistant_text(event: dict[str, Any]) -> str:
    """Best-effort plain-text extraction from one transcript line."""
    role = event.get("role") or (event.get("message") or {}).get("role")
    if role != "assistant":
        return ""
    message = event.get("message") if isinstance(event.get("message"), dict) else event
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                value = block.get("text")
                if isinstance(value, str):
                    parts.append(value)
        return "\n".join(parts)
    return ""


def _build_annotation(last: StatusLine) -> str:
    """Compose the ``additionalContext`` payload for the next turn."""
    if last.kind == WAIT_KIND:
        signal = last.signal or "<unspecified>"
        reason = last.fields.get("reason", "")
        suffix = f' — reason: "{reason}"' if reason else ""
        eta = last.fields.get("eta_s")
        eta_suffix = f" (ETA {eta}s)" if eta else ""
        return (
            f"GOAL_WAIT recognized — suspended on signal {signal}{eta_suffix}{suffix}. "
            "Resume this turn when the watcher fires; do NOT increment no_progress."
        )

    if last.kind == STATUS_KIND:
        active = _query_active_dispatches()
        if active is None or active.get("total", 0) == 0:
            return ""
        task_ids = ", ".join(
            str(task.get("task_id", "?"))
            for task in (active.get("tasks") or [])[:5]
        ) or "(none returned)"
        return (
            f"Active dispatch detected — /api/delegate/active reports "
            f"{active['total']} in-flight task(s) [{task_ids}]. This counts as "
            "active progress; do NOT increment no_progress this turn even if "
            "the predicate did not advance."
        )

    return ""


def _query_active_dispatches() -> dict[str, Any] | None:
    """Call the Monitor API; return None on any failure (no exceptions escape)."""
    url = f"{MONITOR_API.rstrip('/')}{DELEGATE_ACTIVE_PATH}"
    try:
        with urllib.request.urlopen(url, timeout=DELEGATE_HTTP_TIMEOUT_S) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        parsed = json.loads(body)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    return parsed if isinstance(parsed, dict) else None


if __name__ == "__main__":
    raise SystemExit(main())
