"""Gemini CLI session history parser.

Gemini CLI persists every conversation to disk at::

    ~/.gemini/tmp/{project}/chats/session-{ISO-timestamp}-{shortid}.json

Each session file contains the full transcript for a single Gemini CLI
invocation — the exact prompt we sent and the exact response we received,
after all template substitutions. This is the ground truth for debugging
"why did the writer ignore the checklist" questions that would otherwise
require guessing + rebuilding.

Schema (observed 2026-04):

.. code-block:: json

    {
      "sessionId": "37d98b12-...",
      "projectHash": "ad818000...",
      "startTime": "2026-04-10T21:23:18.297Z",
      "lastUpdated": "2026-04-10T21:29:42.001Z",
      "messages": [
        {
          "id": "...",
          "timestamp": "2026-04-10T21:23:18.312Z",
          "type": "user",       // "user" | "gemini" | "info"
          "content": [{"text": "# Section-by-Section ..."}]
        },
        ...
      ],
      "kind": "..."
    }

Note: the issue #1174 originally described the schema as
``{"role", "parts": [{"text"}]}`` but the real CLI format uses
``type`` + ``content`` (a list of text-part dicts). This module works
with the real schema.

Issue: #1174
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Root where Gemini CLI persists all session transcripts.
GEMINI_CHATS_ROOT = Path.home() / ".gemini" / "tmp"


@dataclass(frozen=True)
class SessionMessage:
    """One message in a Gemini session transcript."""
    type: str           # "user" | "gemini" | "info"
    text: str           # Joined text from all content parts
    timestamp: str      # ISO timestamp string (may be empty)


@dataclass(frozen=True)
class Session:
    """Parsed Gemini session transcript."""
    path: Path
    session_id: str
    start_time: datetime | None
    last_updated: datetime | None
    messages: list[SessionMessage]

    @property
    def user_messages(self) -> list[SessionMessage]:
        return [m for m in self.messages if m.type == "user"]

    @property
    def gemini_messages(self) -> list[SessionMessage]:
        return [m for m in self.messages if m.type == "gemini"]


def _parse_iso(ts: str | None) -> datetime | None:
    """Best-effort ISO-8601 parse. Handles trailing 'Z' suffix."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _extract_text(content: Any) -> str:
    """Flatten a message's content field to a single text string.

    Handles the observed shape::

        content: [{"text": "..."}, {"text": "..."}]

    And defensive fallbacks for scalar strings and dict content.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return str(content.get("text", ""))
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    parts.append(str(text))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content)


def parse_session(path: Path) -> Session:
    """Parse a Gemini session JSON file.

    Args:
        path: Path to ``session-YYYY-MM-DDTHH-MM-{id}.json``.

    Returns:
        A ``Session`` dataclass. If the file is malformed or empty, the
        returned Session has empty ``messages`` and ``None`` timestamps —
        callers should check ``session.messages`` before using the data.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
    """
    raw_text = path.read_text("utf-8")
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return Session(
            path=path, session_id="", start_time=None,
            last_updated=None, messages=[],
        )

    messages: list[SessionMessage] = []
    for m in data.get("messages", []) or []:
        if not isinstance(m, dict):
            continue
        messages.append(
            SessionMessage(
                type=str(m.get("type", "")),
                text=_extract_text(m.get("content")),
                timestamp=str(m.get("timestamp", "")),
            )
        )

    return Session(
        path=path,
        session_id=str(data.get("sessionId", "")),
        start_time=_parse_iso(data.get("startTime")),
        last_updated=_parse_iso(data.get("lastUpdated")),
        messages=messages,
    )


def extract_prompt_and_response(session: Session) -> tuple[str, str]:
    """Return the first user prompt and the first Gemini response.

    Returns:
        ``(prompt, response)`` where either may be an empty string if the
        corresponding message type is absent (e.g. prompt-only sessions
        that never reached the model).
    """
    prompt = ""
    response = ""
    for m in session.messages:
        if m.type == "user" and not prompt:
            prompt = m.text
        elif m.type == "gemini" and not response:
            response = m.text
        if prompt and response:
            break
    return prompt, response


def list_sessions(project: str = "learn-ukrainian") -> list[Path]:
    """Return all session JSON files for ``project``, newest first.

    Empty list if the directory doesn't exist — callers should handle
    this gracefully (Gemini CLI may not have been run yet in this
    environment).
    """
    chats_dir = GEMINI_CHATS_ROOT / project / "chats"
    if not chats_dir.is_dir():
        return []
    files = [p for p in chats_dir.glob("session-*.json") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def find_latest_session(project: str = "learn-ukrainian") -> Path | None:
    """Return the most recently-modified session file, or None."""
    files = list_sessions(project)
    return files[0] if files else None


def find_session_near_time(
    target: datetime,
    *,
    project: str = "learn-ukrainian",
    max_drift_s: float = 300.0,
) -> Path | None:
    """Find the session whose ``startTime`` is closest to ``target``.

    Used to correlate a dispatch (which knows its wall-clock time) to
    the Gemini session file created by that call. Sessions whose start
    time is more than ``max_drift_s`` seconds away from target are
    rejected — if no match is within the window, returns None.

    The default 300s window generously covers: subprocess spawn lag,
    gemini-cli warmup, system clock jitter, and the gap between
    ``dispatch_agent`` taking its timestamp and Gemini CLI writing
    ``startTime`` into the session file.

    Args:
        target: The dispatch wall-clock timestamp to match against.
            Must be timezone-aware — pass ``datetime.now(UTC)`` from
            the caller; this function does not assume a zone.
        project: Gemini CLI project name (directory under
            ``~/.gemini/tmp/``).
        max_drift_s: Maximum allowed drift in seconds.

    Returns:
        Path to the closest matching session, or None if no session is
        within the window.
    """
    candidates: list[tuple[float, Path]] = []
    for path in list_sessions(project):
        try:
            session = parse_session(path)
        except OSError:
            continue
        if session.start_time is None:
            continue
        # Only compare timezone-aware-vs-timezone-aware. If either side
        # is naive we skip to avoid a TypeError.
        if target.tzinfo is None or session.start_time.tzinfo is None:
            continue
        drift = abs((session.start_time - target).total_seconds())
        if drift <= max_drift_s:
            candidates.append((drift, path))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def gemini_chats_dir_for_project(project: str = "learn-ukrainian") -> Path:
    """Return the chats directory for a project (may not exist)."""
    return GEMINI_CHATS_ROOT / project / "chats"
