"""Ownership proof for a dispatch's own ``git worktree add`` (#8663).

Dispatch reserves a fresh worktree path with ``os.mkdir`` and records the
reservation as ``worktree_prep`` in its task record before git starts. The
record is later the only authority for removing what a failed or killed add
left behind, so it carries identities that a path string alone cannot give:

* ``dir_dev``/``dir_ino``: the directory this call created. A path removed
  and re-created, by anyone, is a new inode and never qualifies.
* ``git_admin_dir``: the admin directory git registered for the path, read
  from ``<path>/.git`` once git writes it. The current registration must
  point at that same admin directory, in both directions.
* ``git_pid``/``git_start`` and ``owner_pid``/``owner_start``: the add's and
  the dispatcher's process identities (pid plus ``/proc`` start time), so a
  later reader can prove either is gone without trusting a recycled pid.
* ``base_sha``: the commit the add checks out, for the completed-checkout
  guard (:func:`checkout_never_completed`).

Every check fails safe: an identity that cannot be read or compared means
"keep". Stdlib-only apart from sibling helpers, so dispatch, the reapers, the
reconcile sweep and admission can all import it cheaply.
"""

from __future__ import annotations

import os
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


def read_git_admin_dir(path: Path) -> str | None:
    """Return the admin directory ``<path>/.git`` points at, resolved, or ``None``."""
    try:
        text = (path / ".git").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    line = text.strip()
    if not line.startswith("gitdir:"):
        return None
    admin = Path(line.removeprefix("gitdir:").strip())
    if not admin.is_absolute():
        admin = path / admin
    try:
        return str(admin.resolve())
    except (OSError, RuntimeError):
        return None


def admin_dir_matches(prep: dict[str, Any], path: Path) -> bool:
    """True when git's current registration of ``path`` is the recorded admin directory.

    ``<path>/.git`` must point at the recorded admin directory and that admin
    directory's ``gitdir`` file must point back at ``<path>/.git``. An
    unrecorded admin directory never matches.
    """
    recorded = prep.get("git_admin_dir")
    if not isinstance(recorded, str) or not recorded:
        return False
    if read_git_admin_dir(path) != recorded:
        return False
    try:
        back = Path((Path(recorded) / "gitdir").read_text(encoding="utf-8").strip())
        return back.resolve() == (path / ".git").resolve()
    except (OSError, RuntimeError, UnicodeDecodeError):
        return False


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


def checkout_never_completed(path: Path, base_sha: object) -> tuple[bool, str]:
    """Decide from the tree itself whether the add's checkout never finished.

    Rule (fails safe: anything it cannot read or explain keeps the tree):

    * HEAD resolves to the recorded ``base_sha``: nothing was committed.
    * ``git status`` reports only deletions of tracked files and untracked or
      ignored files at paths HEAD tracks, each no larger than HEAD's blob.
      An interrupted checkout has no complete index, so the files it already
      wrote read as untracked copies of HEAD's content (the last one possibly
      truncated) and the rest as deleted. Any modification, addition, rename,
      conflict or type change, and any untracked or ignored file at a path
      HEAD does not track, is evidence of work and keeps the tree.

    Returns ``(True, why)`` only when every entry is explained.
    """
    if not isinstance(base_sha, str) or not base_sha:
        return False, "no recorded base commit"
    head = _git(["rev-parse", "--verify", "--quiet", "HEAD^{commit}"], cwd=path)
    if head is None or head.returncode != 0:
        return False, "HEAD unresolvable"
    if head.stdout.decode("utf-8", "replace").strip() != base_sha:
        return False, "HEAD moved off the recorded base commit"
    tree = _git(["ls-tree", "-r", "-l", "-z", "HEAD"], cwd=path)
    status = _git(
        [
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignored=traditional",
            "--no-renames",
            "--ignore-submodules=all",
        ],
        cwd=path,
    )
    if tree is None or tree.returncode != 0 or status is None or status.returncode != 0:
        return False, "git status or ls-tree failed"
    blob_sizes: dict[bytes, int] = {}
    for entry in tree.stdout.split(b"\0"):
        meta, sep, name = entry.partition(b"\t")
        fields = meta.split()
        if not sep or len(fields) != 4 or fields[1] != b"blob":
            continue
        try:
            blob_sizes[name] = int(fields[3])
        except ValueError:
            continue
    for entry in status.stdout.split(b"\0"):
        if not entry:
            continue
        code, name = entry[:2], entry[3:]
        if code in (b"D ", b" D", b"DD"):
            continue
        if code not in (b"??", b"!!"):
            return False, f"tracked change {code.decode('ascii', 'replace')!r} at {name.decode('utf-8', 'replace')}"
        size = blob_sizes.get(name.rstrip(b"/"))
        if size is None:
            return False, f"file HEAD does not track: {name.decode('utf-8', 'replace')}"
        try:
            written = os.lstat(path / os.fsdecode(name)).st_size
        except OSError:
            return False, f"unreadable file: {name.decode('utf-8', 'replace')}"
        if written > size:
            return False, f"file larger than HEAD's copy: {name.decode('utf-8', 'replace')}"
    return True, "HEAD is the recorded base and the tree holds only a partial checkout of it"


def removal_refusal(prep: dict[str, Any], path: Path) -> str | None:
    """Why the half-built worktree at ``path`` may not be removed on ``prep``'s authority.

    ``None`` means every identity holds: the directory is the one reserved,
    git's registration is the recorded admin directory, the recorded add is
    gone, and the tree holds only an unfinished checkout of the recorded base.
    The caller separately proves git still holds the ``initializing`` lock.
    """
    if prep.get("reserved_by_mkdir") is not True:
        return "no mkdir reservation recorded"
    if not identity_matches(prep, path):
        return "path no longer holds the directory this run reserved (device/inode differ)"
    if not admin_dir_matches(prep, path):
        return "git's registration of the path is not the admin directory this run's add created"
    if not git_gone(prep):
        return "the recorded git worktree add (or its process group) is not proven exited"
    completed, why = checkout_never_completed(path, prep.get("base_sha"))
    if not completed:
        return f"no proof the checkout never completed: {why}"
    return None


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
