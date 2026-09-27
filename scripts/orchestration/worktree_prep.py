"""Reservation record and leftover evidence for dispatch's ``git worktree add`` (#8663).

Dispatch reserves a fresh worktree path with ``os.mkdir`` and records the
reservation as ``worktree_prep`` in its task record before git starts. The
record authorizes no removal of a registered worktree: nothing removes one
automatically. It serves three narrower purposes:

* ``dir_dev``/``dir_ino``: the directory this call created, reported as
  ``reserved_directory_intact``. Dispatch never removes the reservation,
  not even an empty one (``reserved_dir_left`` records that it stayed).
* ``owner_pid``/``owner_start`` (the dispatcher) and ``git_pid``/``git_start``
  (the add), as pid plus ``/proc`` start time: a provisional ``spawning``
  record whose dispatcher is provably gone is marked ``crashed``
  (:func:`is_orphaned_prep_record`), and liveness is reported as evidence.
* ``base_sha``: the commit the add checks out, reported beside HEAD.

A worktree a stopped add left registered under git's ``initializing`` lock is
classified :data:`LEFTOVER_KIND` and reported with :func:`leftover_evidence`
and :func:`verify_first_command` for a human or driver to act on.

Stdlib-only apart from sibling helpers, so dispatch, the reapers, the
reconcile sweep and admission can all import it cheaply.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from scripts.common.acp_runtime_lock import owner_alive, process_start_time
from scripts.common.git_context import sanitized_git_env

# The lock reason git writes while ``git worktree add`` is still checking out
# and removes once the add finishes. Dispatch runs the add in the C locale, so
# git does not translate it.
INITIALIZING_LOCK_REASON = "initializing"
ORPHANED_PREP_REASON = "dispatch_died_during_worktree_prep"
# ``needs_attention`` kind of a registered worktree a stopped add left behind.
LEFTOVER_KIND = "initializing_leftover"
_ACTIVE_STATUSES = ("running", "spawning")
_GIT_TIMEOUT_S = 60


def process_identity(pid: int) -> dict[str, int | None]:
    """Return ``{"pid", "start"}`` for ``pid``; ``start`` is ``None`` when unreadable."""
    return {"pid": pid, "start": process_start_time(pid)}


def process_gone(pid: object, start: object) -> bool:
    """True only on proof the process ``(pid, start)`` no longer runs.

    Proof is a missing ``/proc/<pid>``, or the pid now reporting a different
    start time (recycled). An unrecorded pid, a start time that could not be
    read when it was recorded or cannot be read now, or a host without
    ``/proc`` is never proof.
    """
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if not isinstance(start, int) or isinstance(start, bool):
        return False
    return owner_alive(pid, start) is False


def _process_group_empty(pgid: int) -> bool:
    """True when no process remains in group ``pgid`` (the add's checkout child included)."""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return True
    except (PermissionError, OSError):
        return False
    return False


def git_gone(prep: dict[str, Any]) -> bool:
    """True only on proof the recorded ``git worktree add`` and its process group are gone.

    The add runs in its own session, so its pid is also its process group:
    a checkout child that outlived its parent still keeps the group alive.
    """
    pid = prep.get("git_pid")
    return process_gone(pid, prep.get("git_start")) and _process_group_empty(pid)  # type: ignore[arg-type]


def owner_gone(prep: dict[str, Any]) -> bool:
    """True only on proof the dispatcher that wrote ``prep`` is gone."""
    return process_gone(prep.get("owner_pid"), prep.get("owner_start"))


def directory_identity(path: Path) -> tuple[int, int] | None:
    """Return ``(st_dev, st_ino)`` of the directory at ``path``, or ``None``."""
    try:
        st = os.lstat(path)
    except OSError:
        return None
    return (st.st_dev, st.st_ino)


def identity_matches(prep: dict[str, Any], path: Path) -> bool:
    """True when ``path`` still holds the very directory the reservation created."""
    dev, ino = prep.get("dir_dev"), prep.get("dir_ino")
    if not isinstance(dev, int) or not isinstance(ino, int):
        return False
    return directory_identity(path) == (dev, ino)


def _git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[bytes] | None:
    env = sanitized_git_env()
    env["LC_ALL"] = "C"
    try:
        return subprocess.run(
            ["git", "--no-optional-locks", *args],
            cwd=cwd,
            capture_output=True,
            check=False,
            timeout=_GIT_TIMEOUT_S,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _status_summary(path: Path) -> dict[str, Any] | None:
    """Count ``git status`` entries in ``path`` by kind, with a few sample paths."""
    status = _git(
        ["status", "--porcelain=v1", "-z", "--untracked-files=normal", "--no-renames", "--ignore-submodules=all"],
        cwd=path,
    )
    if status is None or status.returncode != 0:
        return None
    counts = {"deleted": 0, "untracked": 0, "changed": 0}
    sample: list[str] = []
    for entry in status.stdout.split(b"\0"):
        if not entry:
            continue
        code, name = entry[:2], entry[3:].decode("utf-8", "replace")
        if code == b"??":
            counts["untracked"] += 1
        elif code in (b"D ", b" D", b"DD"):
            counts["deleted"] += 1
        else:
            counts["changed"] += 1
        if len(sample) < 5:
            sample.append(f"{code.decode('ascii', 'replace')} {name}")
    return {**counts, "sample": sample}


def leftover_evidence(prep: dict[str, Any], path: Path) -> dict[str, Any]:
    """Facts a human needs before removing the worktree a stopped add left at ``path``.

    Read-only: reservation identity, whether the add and its dispatcher are
    proven gone, HEAD against the recorded base commit, and a ``git status``
    summary. A value that cannot be read is ``None``, never a guess.
    """
    head_proc = _git(["rev-parse", "--verify", "--quiet", "HEAD^{commit}"], cwd=path)
    head = head_proc.stdout.decode("utf-8", "replace").strip() if head_proc and head_proc.returncode == 0 else None
    base_sha = prep.get("base_sha") if isinstance(prep.get("base_sha"), str) else None
    return {
        "reserved_at": prep.get("reserved_at"),
        "run_nonce": prep.get("run_nonce"),
        "reserved_directory_intact": identity_matches(prep, path),
        "git_pid": prep.get("git_pid"),
        "git_add_exited": git_gone(prep),
        "dispatcher_pid": prep.get("owner_pid"),
        "dispatcher_exited": owner_gone(prep),
        "base_sha": base_sha,
        "head": head,
        "head_is_base": None if head is None or base_sha is None else head == base_sha,
        "status": _status_summary(path),
    }


def verify_first_command(repo_root: Path, path: Path) -> str:
    """The removal a human may run after checking the evidence; never run automatically."""
    repo, target = shlex.quote(str(repo_root)), shlex.quote(str(path))
    return f"verify first: git -C {repo} worktree unlock {target} && git -C {repo} worktree remove --force {target}"


def is_orphaned_prep_record(record: dict[str, Any]) -> bool:
    """True for a provisional ``worktree_prep`` record whose dispatcher is provably gone.

    The provisional record says ``spawning`` with ``pid: null`` while dispatch
    runs ``git worktree add``; if the dispatcher dies before writing a
    terminal record, nothing else ever will. Such a record must stop counting
    as active and is marked ``crashed`` with reason
    :data:`ORPHANED_PREP_REASON`.
    """
    prep = record.get("worktree_prep")
    return (
        record.get("status") in _ACTIVE_STATUSES
        and "pid" in record
        and record["pid"] is None
        and isinstance(prep, dict)
        and isinstance(record.get("run_nonce"), str)
        and prep.get("run_nonce") == record.get("run_nonce")
        and owner_gone(prep)
    )
