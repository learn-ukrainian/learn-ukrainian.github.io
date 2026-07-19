"""Large ask-reply sidecar storage (#5392).

Bridge consumers historically could not tell a short model reply from a body
that transport/store truncated. This module:

1. Always persists the full reply body to a gitignored file sidecar when the
   body exceeds the inline threshold (or looks truncated mid-stream).
2. Returns an **inline** message body that is either the full content (small)
   or a head excerpt plus an explicit ``TRUNCATED`` footer with path + sha256
   + byte count so readers fail loudly and can open the sidecar.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

from ._config import REPO_ROOT

# Default: keep small reviews fully inline; large coding deliverables go to disk.
DEFAULT_INLINE_MAX_BYTES = 12 * 1024
# How much of the head to keep in the SQLite ``messages.content`` row.
DEFAULT_INLINE_HEAD_BYTES = 4 * 1024

_SIDECAR_ROOT = REPO_ROOT / "batch_state" / "asks"

# Heuristics for "model hit a hard stop mid-deliverable".
_TRUNCATION_TAIL_RE = re.compile(
    r"(?:"
    r"complete unified diff:\s*$"
    r"|```\s*$"
    r"|Now the complete\b"
    r"|here is the (?:full|complete)\b[^\n]{0,40}:\s*$"
    r")",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True, slots=True)
class ReplySidecarResult:
    """Result of maybe writing a reply sidecar."""

    content: str
    """Body to store in the messages table (full or excerpt+footer)."""

    sidecar_path: str | None
    """Repo-relative path to the full body, if written."""

    full_bytes: int
    full_sha256: str
    truncated: bool


def _inline_max_bytes() -> int:
    raw = os.environ.get("AB_REPLY_INLINE_MAX_BYTES", "").strip()
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return DEFAULT_INLINE_MAX_BYTES


def _inline_head_bytes() -> int:
    raw = os.environ.get("AB_REPLY_INLINE_HEAD_BYTES", "").strip()
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return DEFAULT_INLINE_HEAD_BYTES


def looks_truncated(content: str) -> bool:
    """Return True when the body ends in a mid-deliverable pattern."""
    tail = content.rstrip()[-400:] if content else ""
    if not tail:
        return False
    if _TRUNCATION_TAIL_RE.search(tail):
        return True
    # Unclosed fenced code block is a strong signal of length death.
    return tail.count("```") % 2 == 1


def _safe_task_segment(task_id: str | None) -> str:
    if not task_id:
        return "no-task"
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", task_id.strip())[:80]
    return cleaned or "no-task"


def write_reply_sidecar(
    content: str,
    *,
    task_id: str | None,
    from_llm: str,
    msg_type: str = "response",
) -> Path:
    """Write the full reply body and return the absolute path."""
    raw = content.encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    task_seg = _safe_task_segment(task_id)
    agent_seg = re.sub(r"[^A-Za-z0-9._-]+", "-", (from_llm or "agent"))[:40] or "agent"
    directory = _SIDECAR_ROOT / task_seg
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"reply-{agent_seg}-{digest[:16]}.md"
    # Idempotent: same body → same path; rewrite is fine.
    path.write_bytes(raw)
    # Touch a tiny pointer for humans grepping the task dir.
    pointer = directory / f"latest-{agent_seg}.path"
    with contextlib.suppress(OSError):
        pointer.write_text(path.name + "\n", encoding="utf-8")
    return path


def maybe_sidecare_response(
    content: str,
    *,
    task_id: str | None,
    from_llm: str,
    msg_type: str,
) -> ReplySidecarResult:
    """Return content + optional sidecar metadata for a bridge message.

    Only ``response`` (and ``error``) messages are candidates — asks themselves
    stay fully inline so process-ask always loads the complete request.
    """
    full = content if content is not None else ""
    raw = full.encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    full_bytes = len(raw)

    if msg_type not in {"response", "error"}:
        return ReplySidecarResult(
            content=full,
            sidecar_path=None,
            full_bytes=full_bytes,
            full_sha256=digest,
            truncated=False,
        )

    force = looks_truncated(full)
    if full_bytes <= _inline_max_bytes() and not force:
        return ReplySidecarResult(
            content=full,
            sidecar_path=None,
            full_bytes=full_bytes,
            full_sha256=digest,
            truncated=False,
        )

    path = write_reply_sidecar(full, task_id=task_id, from_llm=from_llm, msg_type=msg_type)
    try:
        rel = path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        rel = str(path)

    head_limit = _inline_head_bytes()
    # Cut on a UTF-8-safe boundary.
    head = full
    if full_bytes > head_limit:
        head = full.encode("utf-8")[:head_limit].decode("utf-8", errors="ignore")
        # Prefer ending at a line boundary for readability.
        nl = head.rfind("\n")
        if nl > head_limit // 2:
            head = head[: nl + 1]

    reason = "heuristic mid-deliverable end" if force and full_bytes <= _inline_max_bytes() else "size"
    footer = (
        f"\n\n---\n"
        f"TRUNCATED: full reply offloaded to sidecar (reason={reason}).\n"
        f"path: {rel}\n"
        f"sha256: {digest}\n"
        f"bytes: {full_bytes}\n"
        f"Read the sidecar for the complete body; do not treat this excerpt as complete.\n"
    )
    return ReplySidecarResult(
        content=head + footer,
        sidecar_path=rel,
        full_bytes=full_bytes,
        full_sha256=digest,
        truncated=True,
    )
