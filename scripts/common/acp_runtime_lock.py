"""Owner identity for ACP runtime worktree locks (#8344).

``acp_execution_cwd`` locks every runtime worktree it creates. A killed ask
never unwinds, so the lock reason carries the owner's pid and process start
time: any later process can then prove the owner is dead (pid absent, or the
pid was recycled and now reports a different start time) without the owner's
cooperation. Hosts without ``/proc`` degrade to "unknown owner" — never to
"dead".
"""

from __future__ import annotations

import os
import re
from pathlib import Path

LOCK_REASON_PREFIX = "active ACP execution "

_OWNER_RE = re.compile(r"\(owner pid=(\d+) start=(\d+|unknown)\)\s*$")

_PROC_ROOT = Path("/proc")


def process_start_time(pid: int) -> int | None:
    """Return the process start time (field 22 of ``/proc/<pid>/stat``).

    ``None`` whenever the start time cannot be determined — non-Linux hosts,
    a missing process, or an unreadable stat. Callers must treat ``None`` as
    "unknown", never as "dead".
    """
    try:
        stat_text = (_PROC_ROOT / str(pid) / "stat").read_text(encoding="utf-8")
    except OSError:
        return None
    # comm (field 2) is parenthesized and may contain spaces; fields after the
    # final ")" start at state (field 3), so starttime (field 22) is index 19.
    end = stat_text.rfind(")")
    if end < 0:
        return None
    fields = stat_text[end + 2 :].split()
    if len(fields) <= 19:
        return None
    try:
        return int(fields[19])
    except ValueError:
        return None


def build_lock_reason(
    label: str,
    *,
    pid: int | None = None,
    start_time: int | None = None,
) -> str:
    """Return the lock reason, preserving the human-readable prefix.

    Anything that greps for ``active ACP execution <label>`` keeps matching;
    the owner identity is appended in parentheses.
    """
    owner_pid = os.getpid() if pid is None else pid
    start = process_start_time(owner_pid) if start_time is None else start_time
    start_text = str(start) if start is not None else "unknown"
    return f"{LOCK_REASON_PREFIX}{label} (owner pid={owner_pid} start={start_text})"


def parse_lock_owner(reason: str | None) -> tuple[int | None, int | None] | None:
    """Parse an ACP lock reason into ``(pid, start_time)``.

    Returns ``None`` when the reason is not an ACP execution lock,
    ``(None, None)`` for a legacy lock without owner information, and
    ``(pid, start)`` otherwise (``start`` is ``None`` when it was recorded as
    unknown).
    """
    if reason is None or not reason.startswith(LOCK_REASON_PREFIX):
        return None
    match = _OWNER_RE.search(reason)
    if match is None:
        return (None, None)
    start_text = match.group(2)
    return (int(match.group(1)), None if start_text == "unknown" else int(start_text))


def owner_alive(pid: int | None, start_time: int | None) -> bool | None:
    """Decide whether a recorded lock owner is alive.

    ``True`` = alive, ``False`` = provably dead (pid absent, or pid recycled
    with a different start time), ``None`` = unknown. Legacy locks (no pid),
    unknown start times, unreadable stats, and hosts without ``/proc`` all
    yield ``None`` so callers fail closed.
    """
    if pid is None or pid <= 0:
        return None
    if not _PROC_ROOT.is_dir():
        return None
    if not (_PROC_ROOT / str(pid)).is_dir():
        return False
    if start_time is None:
        return None
    current_start = process_start_time(pid)
    if current_start is None:
        return None
    return current_start == start_time
