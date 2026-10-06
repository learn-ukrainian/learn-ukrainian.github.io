"""Attribute unmanaged system-temp directories; preserve every unproven owner (#8755).

The opt-in unattributed-scratch class (#9737, operator retention decision
2026-10-06) also reaps hand-made top-level scratch that no task owns, once it
is proven quiet and unreferenced by every process and every unsettled task.
Every safety fact must be positively known at removal time: an uninspectable
process, an unreadable task record or a path a live task names preserves.

Consistency boundary (#9872): a proven candidate is first renamed into a
per-run quarantine directory, so no process can newly reach it by its old
path. The holder, task and write checks then re-run against the quarantined
entry; anything found or unknown renames it back.

Recoverable retention (#9887): a clean result keeps the entry in quarantine
instead of deleting it. Each step is recorded in the append-only ledger of
:mod:`scripts.hygiene.tmp_sweep_ledger`, the first record before the entry
leaves its path. ``restore <ledger-id>`` puts an entry back; the purge pass
at the start of a later run deletes it only once the window (7 days by
default) has passed and the same checks still hold.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import errno
import fcntl
import hashlib
import json
import math
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.scratch import DEFAULT_SCRATCH_ROOT, fallback_scratch_root, resolve_scratch_root
from scripts.common.task_scratch import TaskScratchError, mount_points
from scripts.common.task_store_paths import tasks_dir
from scripts.hygiene.retention_engine import plan_digest, reap_attributed_temp
from scripts.hygiene.tmp_sweep_ledger import (
    DEFAULT_DIGEST_LIMIT,
    DEFAULT_QUARANTINE_S,
    HELD_STATES,
    TERMINAL_STATES,
    Entry,
    Ledger,
    LedgerError,
    build_manifest,
    default_state_dir,
    digest_unverified,
    manifest_mismatches,
    new_id,
    new_run_id,
    parse_iso,
    surviving_mismatches,
    sync_directory,
    utc_iso,
    validate_state_dir,
)
from scripts.orchestration.tmp_leak_sweep import (
    _process_state,
    _process_vanished,
)
from scripts.orchestration.worktree_claims import _SUPERSEDED_RECORD_RE

REPO_ROOT = Path(__file__).resolve().parents[2]
# Unsettled deliverables (needs_finalize), blocked work and dry-run records are held.
REAPABLE_STATES = frozenset({"done", "failed", "timeout", "cancelled", "crashed", "rate_limited", "no_deliverable"})
HARNESS_NAMES = re.compile(r"^(?:claude|codex|gemini|agy|cursor|kimi|hermes|acpx)(?:[-_.]|$)")
# Never swept: dot-entries, harness/session sockets and systemd private trees.
EXCLUDED_NAMES = re.compile(r"^(?:\.|claude-|tmux-|ssh-|systemd-)")
SYSTEM_TEMP_AREAS = (Path("/tmp"), Path("/private/tmp"), Path("/var/tmp"))
# The sweep's own per-run holding directories. The leading dot already keeps
# them out of candidacy; recovery, not the main scan, reports their entries.
QUARANTINE_PREFIX = ".lu-tmp-sweep-quarantine-"
_RENAME_NOREPLACE = 1
# Manifest comparison outcomes that permit a purge; only "verified" proves byte identity.
MANIFEST_MATCHES = frozenset({"verified", "unverified_digest_skipped"})
_DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)


@dataclass(frozen=True)
class ScratchPolicy:
    """Unattributed-scratch thresholds (#9737); both default to 24 hours.

    ``min_age_s`` gates the top-level entry itself; ``quiet_s`` gates the
    newest write anywhere below it. Change time counts as a write, so an
    archive extracted recently with old preserved mtimes stays young.
    """

    min_age_s: float = 24 * 3600
    quiet_s: float = 24 * 3600

    def __post_init__(self) -> None:
        for value in (self.min_age_s, self.quiet_s):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("scratch thresholds must be finite and positive")


@dataclass(frozen=True)
class TaskInventory:
    """Current task records, paths named by unsettled tasks, and whether every record was read.

    ``complete`` is False when the task directory or any current record is
    unreadable, malformed or symlinked: such an inventory cannot prove that
    no task owns or references an entry, so it never authorizes removal.
    """

    records: dict[str, dict[str, Any]]
    references: frozenset[Path]
    complete: bool


def _absolute_paths(value: Any) -> Iterator[str]:
    """Yield every absolute-path string anywhere in a JSON value (iteratively)."""
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, str) and item.startswith("/"):
            yield item


def _reference_forms(value: str) -> set[Path]:
    """The lexical and resolved forms of a recorded path, so ``/tmp`` aliases still match."""
    lexical = Path(os.path.normpath(value))
    forms = {lexical}
    # A looping alias keeps only its lexical form.
    with contextlib.suppress(OSError, RuntimeError):
        forms.add(lexical.resolve())
    return forms


def load_tasks(root: Path) -> TaskInventory:
    """Read current task records and every absolute path an unsettled record names.

    Missing/invalid records never authorize removal: each shadows its task ID
    and marks the inventory incomplete. Superseded ``<task>.<stamp>.archived``
    runs are history and claim nothing. Every path value of a record whose
    status is not settled (``runtime_tmp_root``, ``worktree_path``, ``cwd``,
    environment and argument values) is a reference.
    """
    records: dict[str, dict[str, Any]] = {}
    references: set[Path] = set()
    try:
        with os.scandir(root) as entries:
            names = sorted(entry.name for entry in entries if entry.name.endswith(".json"))
    except OSError:
        return TaskInventory({}, frozenset(), False)
    complete = True
    for name in names:
        if _SUPERSEDED_RECORD_RE.search(name):
            continue
        stem = name.removesuffix(".json")
        path = root / name
        # Even an unreadable/malformed newer run shadows an older parent ID.
        records[stem] = {"status": None, "finished_at": None, "record_sha256": None}
        try:
            if path.is_symlink():
                raise ValueError("symlinked task record")
            raw = path.read_bytes()
            data = json.loads(raw)
            if not isinstance(data, dict) or data.get("task_id") != stem:
                raise ValueError("not a current task record")
        except (OSError, ValueError, RecursionError):
            complete = False
            continue
        records[stem] = {
            "status": data.get("status"),
            "finished_at": data.get("finished_at"),
            "record_sha256": hashlib.sha256(raw).hexdigest(),
        }
        if data.get("status") not in REAPABLE_STATES:
            for value in _absolute_paths(data):
                references.update(_reference_forms(value))
    return TaskInventory(records, frozenset(references), complete)


def task_referenced(path: Path, references: frozenset[Path]) -> bool:
    """True when an unsettled task names ``path``, something inside it, or its temp root."""
    return any(ref == path or path in ref.parents or ref == path.parent for ref in references)


def task_attribution(name: str, records: dict[str, dict[str, Any]]) -> list[str]:
    """Use complete task IDs with a suffix boundary, never issue/prefix guesses."""
    matches = [key for key in records if name == key or any(name.startswith(key + sep) for sep in ("-", ".", "_"))]
    # A specific run takes precedence over its earlier, shorter task ID.
    return sorted(matches, key=lambda key: (-len(key), key))[:1]


def process_snapshot(proc_root: Path = Path("/proc")) -> tuple[list[tuple[int, Path]], bool]:
    """Collect cwd, open-FD and mapped-file references for ALL users; unreadable live processes are unknown.

    A file mapped into memory stays reachable after its descriptor closes, so
    ``/proc/<pid>/maps`` counts as a reference too.
    The caller is included. Zombies and processes that vanish during inspection
    hold no references. No command lines, environment values or private paths
    are emitted in reports. A live process the kernel will not let us inspect
    (another user's, or a same-user non-dumpable one) could hold anything, so
    any such process makes the snapshot incomplete.
    """
    references: list[tuple[int, Path]] = []
    complete = True
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return [], False
    for entry in entries:
        if not entry.name.isdigit():
            continue
        state = _process_state(entry)
        if state in {"Z", "X"}:
            continue
        targets: list[str] = []
        try:
            if state is None:
                raise OSError("unknown process state")
            targets = [os.readlink(entry / "cwd")]
            for fd in (entry / "fd").iterdir():
                try:
                    targets.append(os.readlink(fd))
                except FileNotFoundError:
                    continue  # descriptor closed during the scan
            for line in (entry / "maps").read_text(encoding="utf-8", errors="surrogateescape").splitlines():
                fields = line.split(maxsplit=5)
                if len(fields) == 6:
                    targets.append(fields[5])
        except OSError:
            if not _process_vanished(entry):
                complete = False
        for target in targets:
            if target.startswith("/"):
                references.append((int(entry.name), Path(target.removesuffix(" (deleted)"))))
    return references, complete


def registered_worktrees(repo_root: Path) -> set[Path] | None:
    """Query the current repository; a failed Git probe is never clear."""
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain", "-z"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            timeout=15,
        )
        if result.returncode:
            return None
        return {
            Path(os.fsdecode(field[9:])).resolve()
            for field in result.stdout.split(b"\0")
            if field.startswith(b"worktree ")
        }
    except (OSError, subprocess.SubprocessError):
        return None


def tree_facts(path: Path) -> tuple[int, float, float, str | None]:
    """Allocated bytes, latest write and latest change; refuse Git metadata, foreign owners and mounts.

    Never follow symlinks or cross devices. In-tree Git metadata also protects
    worktrees registered with a repository other than this checkout. A file
    can be a bind-mount target, so every node is checked against the mounts.
    """
    allocated = 0
    newest = 0.0
    changed = 0.0
    reason = None
    try:
        mounts = mount_points()
        if mounts is None:
            return 0, 0, 0, "mount_probe_unknown"
        root_stat = path.lstat()
        device = root_stat.st_dev
        seen = set()
        pending = [path]
        while pending:
            node = pending.pop()
            info = node.lstat()
            newest = max(newest, info.st_mtime)
            changed = max(changed, info.st_mtime, info.st_ctime)
            identity = info.st_dev, info.st_ino
            if identity not in seen:
                allocated += info.st_blocks * 512
                seen.add(identity)
            if not stat.S_ISDIR(info.st_mode) and info.st_nlink > 1:
                reason = reason or "hardlinked_content"
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
                # Socket descriptors name kernel inodes, not filesystem paths;
                # a cwd/FD-path scan cannot prove such an endpoint unused.
                reason = reason or "special_file"
            if info.st_uid != os.geteuid():
                reason = reason or "foreign_tree_owner"
            if node.name == ".git":
                reason = reason or "git_metadata"
            if info.st_dev != device or str(node) in mounts:
                reason = reason or "mount_point"
                continue
            if stat.S_ISDIR(info.st_mode):
                pending.extend(node.iterdir())
    except OSError:
        return allocated, newest, changed, "tree_unknown"
    return allocated, newest, changed, reason


def protected_roots() -> set[Path]:
    """Exclude managed roots and their ancestors, independently of worker TMPDIR."""
    roots = {resolve_scratch_root(), DEFAULT_SCRATCH_ROOT, fallback_scratch_root()}
    for key in ("LU_RUNTIME_TMP_BASE_ROOT", "TMPDIR"):
        value = os.environ.get(key)
        if value:
            roots.add(Path(value))
    return {path.resolve() for path in roots}


def classify_path(
    path: Path,
    *,
    tasks: TaskInventory,
    references: list[tuple[int, Path]],
    process_complete: bool,
    worktrees: set[Path] | None,
    managed: set[Path],
    now: float,
    min_age_s: float,
    scratch: ScratchPolicy | None = None,
) -> dict[str, Any]:
    """Return a privacy-safe inventory row and the proof used by the apply recheck.

    Without ``scratch`` only directories attributed to a settled task can be
    reaped. With it, regular files are inventoried too, and an entry with no
    task attribution is reaped as ``unattributed_scratch`` when it is old,
    quiet throughout, and unreferenced by every process and unsettled task.
    Both classes require a complete process snapshot and task inventory.
    """
    records = tasks.records
    row: dict[str, Any] = {"name": path.name, "decision": "preserve", "bytes": None, "task": None, "live_pids": []}
    info = path.lstat()
    row["identity"] = [info.st_dev, info.st_ino, info.st_uid]
    row["kind"] = "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "other"
    resolved = path.resolve()
    if path.is_symlink() or not (row["kind"] == "directory" or (scratch and row["kind"] == "file")):
        row["reason"] = "symlink_or_not_directory"
        return row
    if any(resolved == root or resolved in root.parents or root in resolved.parents for root in managed):
        row["reason"] = "managed_scratch"
        return row
    if HARNESS_NAMES.match(path.name):
        row["reason"] = "harness_runtime"
        return row
    if EXCLUDED_NAMES.match(path.name):
        row["reason"] = "excluded_name"
        return row
    row["bytes"], newest, changed, tree_reason = tree_facts(path)
    row["newest_mtime"] = newest
    row["newest_change"] = changed
    row["age_hours"] = round(max(0, now - newest) / 3600, 2)
    matches = task_attribution(path.name, records)
    if matches:
        row["task"] = matches[0]
        row["task_record"] = records[matches[0]]
    row["live_pids"] = sorted({pid for pid, ref in references if ref == resolved or resolved in ref.parents})
    # Conservatively protect ancestors and descendants of registrations.
    if worktrees is None:
        reason = "git_registration_unknown"
    elif any(resolved == w or resolved in w.parents or w in resolved.parents for w in worktrees):
        reason = "registered_worktree"
    elif info.st_uid != os.geteuid():
        reason = "foreign_owner"
    elif tree_reason:
        reason = tree_reason
    elif row["live_pids"]:
        reason = "live_process"
    elif task_referenced(resolved, tasks.references):
        reason = "task_reference"
    elif not process_complete:
        reason = "liveness_unknown"
    elif not matches and scratch is None:
        reason = "unattributed"
    elif not matches:
        if now - max(info.st_mtime, info.st_ctime) < scratch.min_age_s:
            reason = "too_young"
        elif now - changed < scratch.quiet_s:
            reason = "recent_deep_write"
        elif not tasks.complete:
            reason = "task_inventory_unknown"
        else:
            reason = "unattributed_scratch"
            row["decision"] = "would_reap"
    elif records[matches[0]]["status"] not in REAPABLE_STATES:
        reason = "task_not_settled"
    elif now - newest < min_age_s:
        reason = "too_young"
    else:
        try:
            finished = datetime.fromisoformat(str(records[matches[0]]["finished_at"]).replace("Z", "+00:00"))
            if finished.tzinfo is None or not 0 < finished.timestamp() <= now:
                raise ValueError("invalid completion time")
        except ValueError:
            reason = "task_completion_unknown"
        else:
            if tasks.complete:
                reason = "dead_attributed_task"
                row["decision"] = "would_reap"
            else:
                reason = "task_inventory_unknown"
    row["reason"] = reason
    return row


def proof_digest(row: dict[str, Any]) -> str:
    """Bind identity, newest write, allocation and exact task bytes, excluding age."""
    return plan_digest({key: value for key, value in row.items() if key != "age_hours"})


def attribution_changed(row: dict[str, Any], records: dict[str, dict[str, Any]]) -> bool:
    """True when the task owning ``row`` (or its absence) no longer holds byte-for-byte."""
    expected = [row["task"]] if row["task"] else []
    if task_attribution(row["name"], records) != expected:
        return True
    return bool(row["task"]) and records.get(row["task"]) != row.get("task_record")


def top_level_contents(path: Path, info: os.stat_result) -> tuple[str | None, tuple[tuple[str, bytes], ...]]:
    """The top-level entry's content digest (regular files only) and extended attributes.

    The quarantine rename sets the entry's own ctime, so ctime cannot show a
    later change to it; these stand in for it. A write through a descriptor
    opened earlier, with size and mtime put back, still changes the bytes;
    the remaining ctime-only data change is an extended attribute. Directory
    contents are covered by their descendants' entries. Raises ``OSError``
    when the entry cannot be read or was replaced. Reading leaves atime alone.
    """
    if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)) or not hasattr(os, "listxattr"):
        raise OSError(errno.ENOTSUP, "top-level contents cannot be fingerprinted", str(path))
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | getattr(os, "O_NOATIME", 0)
    fd = os.open(path, flags | (os.O_DIRECTORY if stat.S_ISDIR(info.st_mode) else os.O_NONBLOCK))
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino, opened.st_mode) != (info.st_dev, info.st_ino, info.st_mode):
            raise OSError(errno.ESTALE, "entry replaced while fingerprinting", str(path))
        try:
            names = sorted(os.listxattr(fd))
        except OSError as error:
            if error.errno != errno.ENOTSUP:
                raise
            names = []  # the filesystem holds no extended attributes at all
        xattrs = tuple((name, os.getxattr(fd, name)) for name in names)
        if not stat.S_ISREG(opened.st_mode):
            return None, xattrs
        digest = hashlib.sha256()
        while chunk := os.read(fd, 1 << 20):
            digest.update(chunk)
        return digest.hexdigest(), xattrs
    finally:
        os.close(fd)


def tree_fingerprint(path: Path) -> dict[str, tuple[Any, ...]] | None:
    """Every node's identity, type, links, owner, size, mtime and ctime, keyed by relative path.

    This is the pre-rename snapshot of the write check. Any write, truncate,
    create, delete, rename or metadata change inside sets a node's ctime (and
    usually mtime and size) or changes the key set, so an unequal fingerprint
    means the tree changed after the snapshot. The top-level ctime is left out
    because the quarantine rename itself sets it; its mtime is kept and its
    contents (``top_level_contents``) replace the ctime. ``None`` when any
    node cannot be read. Never follows symlinks or crosses a device.
    """
    nodes: dict[str, tuple[Any, ...]] = {}
    try:
        device = path.lstat().st_dev
        pending = [(path, "")]
        while pending:
            node, relative = pending.pop()
            info = node.lstat()
            nodes[relative] = (
                info.st_dev,
                info.st_ino,
                info.st_mode,
                info.st_nlink,
                info.st_uid,
                info.st_size,
                info.st_mtime_ns,
                info.st_ctime_ns if relative else top_level_contents(node, info),
            )
            if stat.S_ISDIR(info.st_mode) and info.st_dev == device:
                pending.extend((child, f"{relative}/{child.name}") for child in node.iterdir())
    except OSError:
        return None
    return nodes


def rename_noreplace(src_dir_fd: int, src: str, dst_dir_fd: int, dst: str) -> None:
    """Atomically rename ``src`` to ``dst`` with ``renameat2(RENAME_NOREPLACE)``.

    An existing ``dst`` fails with ``EEXIST`` instead of being replaced, so a
    restore never overwrites an entry that took the original name meanwhile.
    """
    renameat2 = getattr(ctypes.CDLL(None, use_errno=True), "renameat2", None)
    if renameat2 is None:
        raise OSError(errno.ENOSYS, "renameat2 is unavailable", src)
    renameat2.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    if renameat2(src_dir_fd, os.fsencode(src), dst_dir_fd, os.fsencode(dst), _RENAME_NOREPLACE) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), src)


def _errno_name(error: OSError) -> str:
    return errno.errorcode.get(error.errno or 0, "unknown")


@dataclass(frozen=True)
class Quarantine:
    """This run's holding directory: owner-only, inside the temp root, locked while the run lives."""

    path: Path
    fd: int


def open_quarantine(root: Path, root_fd: int) -> Quarantine:
    """Create and lock a fresh per-run quarantine directory on the temp root's filesystem."""
    name = QUARANTINE_PREFIX + secrets.token_hex(8)
    os.mkdir(name, 0o700, dir_fd=root_fd)
    sync_directory(root_fd)
    fd = os.open(name, _DIR_FLAGS, dir_fd=root_fd)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        raise
    return Quarantine(root / name, fd)


def close_quarantine(quarantine: Quarantine, root_fd: int) -> None:
    """Remove the quarantine if empty; retained entries keep it until their purge or restore."""
    try:
        with contextlib.suppress(OSError):
            os.rmdir(quarantine.path.name, dir_fd=root_fd)
    finally:
        os.close(quarantine.fd)


def _bare_row(name: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "decision": "preserve", "reason": reason, "bytes": 0, "task": None, "live_pids": []} | extra


def _event(entry_id: str, run_id: str, event: str, **extra: Any) -> dict[str, Any]:
    """A follow-up ledger record for one entry, stamped now."""
    return {"event": event, "ledger_id": entry_id, "run_id": run_id, "at": utc_iso(time.time()), **extra}


def _identity_at(path: Path, identity: list[int]) -> bool:
    """True when ``path`` is the recorded inode; a missing path is False, other errors raise."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return [info.st_dev, info.st_ino] == list(identity[:2])


def _sync_rename(src_dir_fd: int, dst_dir_fd: int) -> None:
    """Persist a completed rename: sync its source directory, then its destination (``DurabilityError`` on failure)."""
    sync_directory(src_dir_fd)
    if os.path.samestat(os.fstat(src_dir_fd), os.fstat(dst_dir_fd)):
        return
    sync_directory(dst_dir_fd)


def _rename_path(src: Path, dst: Path) -> None:
    """``rename_noreplace`` between two absolute paths, through descriptors of their parent directories.

    A refused rename raises ``OSError``; a rename that happened but could not
    be synced raises ``DurabilityError``, so callers never record it as failed.
    """
    src_fd = os.open(src.parent, _DIR_FLAGS)
    try:
        dst_fd = os.open(dst.parent, _DIR_FLAGS)
        try:
            rename_noreplace(src_fd, src.name, dst_fd, dst.name)
            _sync_rename(src_fd, dst_fd)
        finally:
            os.close(dst_fd)
    finally:
        os.close(src_fd)


def _drop_empty_quarantine(location: Path) -> None:
    if location.parent.name.startswith(QUARANTINE_PREFIX):
        with contextlib.suppress(OSError):
            os.rmdir(location.parent)


def _entry_row(entry: Entry, decision: str, reason: str, **extra: Any) -> dict[str, Any]:
    return _bare_row(
        entry.original.name,
        reason,
        decision=decision,
        bytes=entry.intent.get("allocated_bytes") or 0,
        task=entry.intent.get("task"),
        kind=entry.intent.get("kind"),
        ledger_id=entry.ledger_id,
        quarantine=entry.location.parent.name,
        **extra,
    )


def verify_restored(entry: Entry, path: Path) -> dict[str, Any]:
    """Compare ``path`` with the entry's recorded manifest, at the digest limit it was recorded with.

    ``verification`` is ``verified`` only when every node matches and every
    file was hashed. Files above the digest limit match by size and mtime
    alone, which cannot prove their bytes: a matching tree that has any is
    ``unverified_digest_skipped``, listed in ``digest_unverified``, and
    ``verified`` stays False. Otherwise ``mismatch`` or ``unreadable``.
    """
    try:
        current = build_manifest(path, digest_limit=entry.intent["digest_limit_bytes"])
    except OSError as error:
        return {"verified": False, "verification": "unreadable", "verify_error": _errno_name(error)}
    recorded = entry.intent["manifest"]
    mismatches = manifest_mismatches(recorded, current["manifest"])
    unhashed = digest_unverified(recorded, mismatches)
    verification = "mismatch" if mismatches else "unverified_digest_skipped" if unhashed else "verified"
    return {
        "verified": verification == "verified",
        "verification": verification,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:20],
        "digest_unverified_count": len(unhashed),
        "digest_unverified": unhashed[:20],
    }


def reconcile_ledger(
    entries: dict[str, Entry], ledger: Ledger, run_id: str, *, apply: bool
) -> tuple[list[dict[str, Any]], int]:
    """Resolve every entry a crashed step left unconfirmed; delete nothing. Returns ``(rows, errors)``.

    Where the entry is decides: still in quarantine, back at its original
    path (the same inode), or gone. A ``quarantine`` record with no follow-up
    whose rename did happen was never re-verified after it, so the entry is
    renamed back (``returned``), as is a ``return_blocked`` one once its name
    is free. An interrupted restore either completed (``restored``, verified
    now) or did not (``restore_failed``). An interrupted purge whose entry is
    gone is ``purged``; one still present is left to the purge pass. A
    retained entry that vanished is ``missing``, or ``at_origin`` when its
    rename was lost. Dry runs only report.
    """
    rows: list[dict[str, Any]] = []
    errors = 0
    for entry in entries.values():
        if entry.state in TERMINAL_STATES:
            continue
        identity = entry.intent["identity"]
        try:
            held = _identity_at(entry.location, identity)
            at_origin = not held and _identity_at(entry.original, identity)
        except OSError:
            rows.append(_entry_row(entry, "preserve", "ledger_location_unknown"))
            errors += 1
            continue
        if held and entry.state in {"quarantined", "purging"}:
            continue  # the purge pass owns retained entries
        if not apply:
            rows.append(_entry_row(entry, "preserve", "ledger_unreconciled", state=entry.state))
            continue
        if not held:
            if entry.state == "restoring" and at_origin:
                ledger.append(
                    _event(
                        entry.ledger_id, run_id, "restored", reconciled=True, **verify_restored(entry, entry.original)
                    )
                )
                continue
            outcome = "purged" if entry.state == "purging" else "at_origin" if at_origin else "missing"
            ledger.append(_event(entry.ledger_id, run_id, "reconciled", outcome=outcome, prior_state=entry.state))
            rows.append(_entry_row(entry, "preserve", f"ledger_{outcome}"))
            continue
        if entry.state == "restoring":
            ledger.append(_event(entry.ledger_id, run_id, "restore_failed", reconciled=True))
            continue
        try:
            _rename_path(entry.location, entry.original)
        except OSError as error:
            if entry.state == "pending":
                ledger.append(
                    _event(entry.ledger_id, run_id, "reconciled", outcome="return_blocked", error=_errno_name(error))
                )
            rows.append(_entry_row(entry, "preserve", "restore_blocked", error=_errno_name(error)))
            errors += 1
            continue
        ledger.append(_event(entry.ledger_id, run_id, "reconciled", outcome="returned", prior_state=entry.state))
        _drop_empty_quarantine(entry.location)
    return rows, errors


def recover_quarantines(
    root: Path, root_fd: int, *, apply: bool, known: frozenset[Path] = frozenset()
) -> tuple[list[dict[str, Any]], int, int]:
    """Return every unledgered quarantined entry to its original name; delete nothing.

    ``known`` are the locations of entries the ledger retains; they stay. A
    quarantine still locked belongs to a live run and is skipped. Any other
    leftover (a run from before the ledger, or a lost ledger) has no record
    to re-verify against, so the boundary rule restores it; it then re-enters
    the normal pipeline as an ordinary candidate. When the original name is
    taken, the entry stays quarantined as ``restore_blocked``. Dry runs only
    report. Returns ``(rows, restored, errors)``.
    """
    rows: list[dict[str, Any]] = []
    restored = errors = 0
    for name in sorted(os.listdir(root_fd)):
        if not name.startswith(QUARANTINE_PREFIX):
            continue
        try:
            fd = os.open(name, _DIR_FLAGS, dir_fd=root_fd)
        except OSError:
            rows.append(_bare_row(name, "quarantine_unknown"))
            errors += 1
            continue
        try:
            if os.fstat(fd).st_uid != os.geteuid():
                rows.append(_bare_row(name, "quarantine_unknown"))
                errors += 1
                continue
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue  # a live run owns it
            for entry in sorted(os.listdir(fd)):
                if root / name / entry in known:
                    continue
                if not apply:
                    rows.append(_bare_row(entry, "quarantine_leftover", quarantine=name))
                    continue
                try:
                    rename_noreplace(fd, entry, root_fd, entry)
                except OSError as error:
                    rows.append(_bare_row(entry, "restore_blocked", quarantine=name, error=_errno_name(error)))
                    errors += 1
                    continue
                _sync_rename(fd, root_fd)
                restored += 1
            if apply:
                with contextlib.suppress(OSError):
                    os.rmdir(name, dir_fd=root_fd)
        finally:
            os.close(fd)
    return rows, restored, errors


def quarantined_problem(
    quarantined: Path, origin: Path, row: dict[str, Any], before: dict[str, tuple[Any, ...]], task_root: Path
) -> str | None:
    """Re-prove the renamed entry; return a preserve reason, or ``None`` when retaining it is safe.

    After the rename nothing can newly open the entry by its old path, so the
    order is fixed: tasks, then every process (cwd, FDs, maps), then the tree.
    A process holding the entry during the scan is found; one that no longer
    holds it can no longer write to it, so any write it made happened before
    the scan and shows in the fingerprint compared last.
    """
    inventory = load_tasks(task_root)
    if not inventory.complete:
        return "quarantine_task_inventory_unknown"
    if attribution_changed(row, inventory.records) or any(
        task_referenced(path, inventory.references) for path in (origin, quarantined)
    ):
        return "quarantine_task_reference"
    references, complete = process_snapshot()
    if any(ref == quarantined or quarantined in ref.parents for _, ref in references):
        return "quarantine_live_process"
    if not complete:
        return "quarantine_liveness_unknown"
    if tree_fingerprint(quarantined) != before:
        return "quarantine_write"
    return None


def quarantine_entry(
    path: Path,
    row: dict[str, Any],
    before: dict[str, tuple[Any, ...]],
    quarantine: Quarantine,
    *,
    root_fd: int,
    task_root: Path,
    ledger: Ledger,
    run_id: str,
    digest_limit: int,
) -> dict[str, Any]:
    """Ledger, rename, re-verify, then retain or return one proven candidate; return its final row.

    The ``quarantine`` record, with the manifest, is durable before the
    rename. Every outcome after it is appended too, so a crash at any point
    leaves a record the next run reconciles. A ledger failure raises
    ``LedgerError`` and stops the run.
    """
    name = path.name
    quarantined = quarantine.path / name
    try:
        facts = build_manifest(path, digest_limit=digest_limit)
    except OSError:
        return row | {"decision": "preserve", "reason": "manifest_unknown"}
    entry_id = new_id()
    ledger.append(
        {
            "event": "quarantine",
            "ledger_id": entry_id,
            "run_id": run_id,
            "at": utc_iso(time.time()),
            "original_path": str(path),
            "quarantine_path": str(quarantined),
            "owner_uid": row["identity"][2],
            "identity": row["identity"][:2],
            "kind": row["kind"],
            "reason": row["reason"],
            "task": row["task"],
            "allocated_bytes": row["bytes"],
            **facts,
        }
    )
    marks = {"ledger_id": entry_id, "quarantine": quarantine.path.name}
    try:
        rename_noreplace(root_fd, name, quarantine.fd, name)
    except OSError as error:
        ledger.append(_event(entry_id, run_id, "quarantine_failed", error=_errno_name(error)))
        return row | marks | {"decision": "preserve", "reason": "quarantine_failed", "error": _errno_name(error)}
    # Durable before anything is recorded about it; a failed sync stops the run with the entry pending.
    _sync_rename(root_fd, quarantine.fd)
    reason = quarantined_problem(quarantined, path, row, before, task_root)
    if reason is None:
        ledger.append(_event(entry_id, run_id, "quarantined"))
        return row | marks | {"decision": "quarantined"}
    try:
        rename_noreplace(quarantine.fd, name, root_fd, name)
    except OSError as error:
        ledger.append(_event(entry_id, run_id, "return_blocked", found=reason, error=_errno_name(error)))
        return (
            row
            | marks
            | {"decision": "preserve", "reason": "restore_blocked", "found": reason, "error": _errno_name(error)}
        )
    _sync_rename(quarantine.fd, root_fd)
    ledger.append(_event(entry_id, run_id, "returned", found=reason))
    return row | marks | {"decision": "preserve", "reason": reason}


def purge_problem(entry: Entry, task_root: Path) -> str | None:
    """Re-check a retained entry past its window; return a keep reason, or ``None`` when deletion is safe.

    The same predicates as the quarantine boundary, against the quarantined
    location: a complete task inventory naming neither path, a complete
    process scan with no holder, the tree's safety facts, then the write
    check: no change after the entry was confirmed and a manifest equal to
    the recorded one. An interrupted purge (``purging``) may have lost part
    of its tree, so ``purge_retry_problem`` checks what survives instead.
    """
    location = entry.location
    inventory = load_tasks(task_root)
    if not inventory.complete:
        return "purge_task_inventory_unknown"
    if any(task_referenced(path, inventory.references) for path in (entry.original, location)):
        return "purge_task_reference"
    references, complete = process_snapshot()
    if any(ref == location or location in ref.parents for _, ref in references):
        return "purge_live_process"
    if not complete:
        return "purge_liveness_unknown"
    _allocated, _newest, changed, tree_reason = tree_facts(location)
    if tree_reason:
        return f"purge_{tree_reason}"
    confirmed = entry.confirmed_at
    if confirmed is None:
        return "purge_recent_write"
    if entry.state == "purging":
        return purge_retry_problem(entry, confirmed)
    if changed > confirmed:
        return "purge_recent_write"
    # Size, mtime and the ctime check above stand in for files above the digest limit.
    if verify_restored(entry, location)["verification"] not in MANIFEST_MATCHES:
        return "purge_manifest_changed"
    return None


def purge_retry_problem(entry: Entry, confirmed: float) -> str | None:
    """Re-prove what an interrupted purge left; ``purge_retry_changed`` when anything survives that it did not record.

    Every surviving node must be in the recorded manifest, equal to it and
    unchanged since the ``quarantined`` record (``surviving_mismatches``); a
    node may be missing, because the interrupted deletion removed it. A new,
    changed or rewritten node, or a tree that cannot be read, keeps the whole
    entry.
    """
    try:
        current = build_manifest(entry.location, digest_limit=entry.intent["digest_limit_bytes"], ctime=True)
    except OSError:
        return "purge_retry_changed"
    if surviving_mismatches(entry.intent["manifest"], current["manifest"], changed_by=confirmed):
        return "purge_retry_changed"
    return None


def purge_quarantine(
    entries: dict[str, Entry],
    ledger: Ledger,
    run_id: str,
    *,
    now: float,
    quarantine_s: float,
    task_root: Path,
    repo_root: Path,
    apply: bool,
) -> tuple[list[dict[str, Any]], int]:
    """Delete retained entries past the window that pass ``purge_problem``; returns ``(rows, errors)``.

    Each deletion is bracketed by a ``purge`` record before it and a
    ``purged`` record after it, written once the quarantine directory is
    synced. Entries inside the window get no row.
    """
    rows: list[dict[str, Any]] = []
    errors = 0
    for entry in sorted(entries.values(), key=lambda item: item.quarantined_at):
        if entry.state not in {"quarantined", "purging"} or now < entry.quarantined_at + quarantine_s:
            continue
        identity = entry.intent["identity"]
        try:
            if not _identity_at(entry.location, identity):
                continue  # reconciliation reports it
        except OSError:
            continue
        reason = purge_problem(entry, task_root)
        if reason:
            rows.append(_entry_row(entry, "preserve", reason))
            # A half-deleted entry whose survivors changed needs a person: restore it or remove it by hand.
            errors += reason == "purge_retry_changed"
            continue
        if not apply:
            rows.append(_entry_row(entry, "would_purge", "quarantine_expired"))
            continue
        ledger.append(_event(entry.ledger_id, run_id, "purge"))
        try:
            reap_attributed_temp(
                entry.location,
                repo_root=repo_root,
                temp_root=entry.location.parent,
                expected_dev=identity[0],
                expected_ino=identity[1],
            )
            if os.path.lexists(entry.location):
                raise OSError("common reaper left residue")
        except (OSError, ValueError, TaskScratchError) as error:
            detail = _errno_name(error) if isinstance(error, OSError) else type(error).__name__
            ledger.append(_event(entry.ledger_id, run_id, "purge_failed", error=detail))
            rows.append(_entry_row(entry, "preserve", "purge_refused", error=detail))
            errors += 1
            continue
        sync_directory(entry.location.parent)
        ledger.append(_event(entry.ledger_id, run_id, "purged"))
        _drop_empty_quarantine(entry.location)
        rows.append(_entry_row(entry, "purged", "quarantine_expired"))
    return rows, errors


def _quarantine_totals(entries: dict[str, Entry], root: Path) -> dict[str, int]:
    held = [entry for entry in entries.values() if entry.state in HELD_STATES and entry.original.parent == root]
    return {
        "quarantine_held_entries": len(held),
        "quarantine_held_bytes": sum(entry.intent.get("allocated_bytes") or 0 for entry in held),
    }


def sweep(
    *,
    temp_root: Path = Path("/tmp"),
    task_root: Path | None = None,
    repo_root: Path = REPO_ROOT,
    min_age_s: float = 12 * 3600,
    scratch: ScratchPolicy | None = None,
    apply: bool = False,
    state_dir: Path | None = None,
    quarantine_s: float = DEFAULT_QUARANTINE_S,
    digest_limit: int = DEFAULT_DIGEST_LIMIT,
) -> dict[str, Any]:
    """Inventory top-level unmanaged entries; on ``apply``, purge expired quarantine, then quarantine proven ones.

    Apply runs hold the ledger lock throughout and, in order, reconcile
    crashed steps, restore unledgered quarantine leftovers, purge expired
    entries, and quarantine newly proven candidates. Dry runs report the
    same passes without changing anything.
    """
    if not math.isfinite(min_age_s) or min_age_s <= 0:
        raise ValueError("minimum age must be finite and positive")
    if not math.isfinite(quarantine_s) or quarantine_s <= 0 or digest_limit < 0:
        raise ValueError("quarantine window must be finite and positive, digest limit non-negative")
    if (
        temp_root.is_symlink()
        or not temp_root.is_dir()
        or temp_root.resolve() in {Path("/"), Path.home().resolve(), repo_root.resolve()}
    ):
        raise ValueError("temp root must be a real temporary directory")
    root = temp_root.resolve()
    allowed_areas = {*SYSTEM_TEMP_AREAS, *protected_roots()}
    if not any(root == area.resolve() or area.resolve() in root.parents for area in allowed_areas):
        raise ValueError("temp root is outside system temp and configured scratch areas")
    if scratch is not None and not any(
        root == area.resolve() or area.resolve() in root.parents for area in SYSTEM_TEMP_AREAS
    ):
        raise ValueError("unattributed scratch runs only within the system temp area")
    ledger = Ledger(validate_state_dir(state_dir or default_state_dir(), forbidden=(root, repo_root)))
    tasks = task_root if task_root is not None else tasks_dir()
    run_id = new_run_id(time.time())
    with ledger.exclusive(wait=True) if apply else contextlib.nullcontext():
        return _sweep_locked(
            root,
            tasks=tasks,
            repo_root=repo_root,
            min_age_s=min_age_s,
            scratch=scratch,
            apply=apply,
            ledger=ledger,
            run_id=run_id,
            quarantine_s=quarantine_s,
            digest_limit=digest_limit,
        )


def _sweep_locked(
    root: Path,
    *,
    tasks: Path,
    repo_root: Path,
    min_age_s: float,
    scratch: ScratchPolicy | None,
    apply: bool,
    ledger: Ledger,
    run_id: str,
    quarantine_s: float,
    digest_limit: int,
) -> dict[str, Any]:
    root_fd = os.open(root, _DIR_FLAGS)
    quarantine: Quarantine | None = None
    try:
        entries, malformed = ledger.entries()
        local = {key: entry for key, entry in entries.items() if entry.original.parent == root}
        # Reconcile, restore unledgered leftovers and purge first, so every probe below sees the result.
        rows, errors = reconcile_ledger(local, ledger, run_id, apply=apply)
        if apply:
            entries, malformed = ledger.entries()
            local = {key: entry for key, entry in entries.items() if entry.original.parent == root}
        known = frozenset(entry.location for entry in local.values() if entry.state in HELD_STATES)
        recovered, restored, recover_errors = recover_quarantines(root, root_fd, apply=apply, known=known)
        rows += recovered
        errors += recover_errors
        purged, purge_errors = purge_quarantine(
            local,
            ledger,
            run_id,
            now=time.time(),
            quarantine_s=quarantine_s,
            task_root=tasks,
            repo_root=repo_root,
            apply=apply,
        )
        rows += purged
        errors += purge_errors
        inventory = load_tasks(tasks)
        references, complete = process_snapshot()
        worktrees = registered_worktrees(repo_root)
        managed = protected_roots()
        for path in sorted(root.iterdir()):
            if path.name.startswith(QUARANTINE_PREFIX):
                continue
            try:
                if not (path.is_symlink() or path.is_dir() or (scratch is not None and path.is_file())):
                    continue
                row = classify_path(
                    path,
                    tasks=inventory,
                    references=references,
                    process_complete=complete,
                    worktrees=worktrees,
                    managed=managed,
                    now=time.time(),
                    min_age_s=min_age_s,
                    scratch=scratch,
                )
                if apply and row["decision"] == "would_reap":
                    # The pre-rename snapshot is taken before the fresh proof, so
                    # any write after it differs at the post-rename comparison.
                    before = tree_fingerprint(path)
                    fresh_refs, fresh_complete = process_snapshot()
                    fresh = classify_path(
                        path,
                        tasks=load_tasks(tasks),
                        references=fresh_refs,
                        process_complete=fresh_complete,
                        worktrees=registered_worktrees(repo_root),
                        managed=protected_roots(),
                        now=time.time(),
                        min_age_s=min_age_s,
                        scratch=scratch,
                    )
                    if before is None or fresh["decision"] != "would_reap" or proof_digest(fresh) != proof_digest(row):
                        row = fresh | {"decision": "preserve", "reason": "proof_changed"}
                    else:
                        quarantine = quarantine or open_quarantine(root, root_fd)
                        row = quarantine_entry(
                            path,
                            row,
                            before,
                            quarantine,
                            root_fd=root_fd,
                            task_root=tasks,
                            ledger=ledger,
                            run_id=run_id,
                            digest_limit=digest_limit,
                        )
                        if row["reason"] == "restore_blocked":
                            errors += 1
                rows.append(row)
            except (OSError, ValueError, TaskScratchError):
                errors += 1
                rows.append(_bare_row(path.name, "scan_or_reap_error"))
    finally:
        if quarantine is not None:
            close_quarantine(quarantine, root_fd)
        os.close(root_fd)
    if apply:
        entries, malformed = ledger.entries()
    free = shutil.disk_usage(root).free
    reclaimable = sum(row["bytes"] for row in rows if row["decision"] == "would_reap")
    purgeable = sum(row["bytes"] for row in rows if row["decision"] == "would_purge")
    quarantined = [row for row in rows if row["decision"] == "quarantined"]
    purged_rows = [row for row in rows if row["decision"] == "purged"]
    report = {
        "schema": "tmp-sweep.v2",
        "mode": "apply" if apply else "dry-run",
        "run_id": run_id,
        "min_age_hours": min_age_s / 3600,
        "scratch_policy": None
        if scratch is None
        else {"min_age_hours": scratch.min_age_s / 3600, "quiet_hours": scratch.quiet_s / 3600},
        "quarantine_days": quarantine_s / 86400,
        "ledger_path": str(ledger.path),
        "ledger_malformed_lines": malformed,
        "rows": rows,
        "directories": sum(1 for row in rows if row.get("kind") != "file"),
        "files": sum(1 for row in rows if row.get("kind") == "file"),
        "errors": errors,
        "quarantine_restored": restored,
        "process_probe_complete": complete,
        "task_inventory_complete": inventory.complete,
        "quarantined_entries": len(quarantined),
        "bytes_quarantined": sum(row["bytes"] for row in quarantined),
        **_quarantine_totals(entries, root),
        "purgeable_entries": sum(1 for row in rows if row["decision"] == "would_purge"),
        "purged_entries": len(purged_rows),
        "bytes_reclaimable": reclaimable,
        "bytes_purgeable": purgeable,
        "bytes_reclaimed": sum(row["bytes"] for row in purged_rows),
        "free_bytes": free,
        "projected_free_bytes": free + purgeable,
    }
    report["digest"] = plan_digest(report)
    return report


def summarize(report: dict[str, Any]) -> dict[str, Any]:
    """Counts and byte totals only: no entry names, safe for logs and public reports.

    The ledger path is shown relative to the home directory (``~/...``).
    """
    summary = {key: value for key, value in report.items() if key != "rows"}
    home = str(Path.home())
    if summary["ledger_path"].startswith(home + "/"):
        summary["ledger_path"] = "~" + summary["ledger_path"][len(home) :]
    summary["by_decision"] = dict(sorted(Counter(row["decision"] for row in report["rows"]).items()))
    summary["by_reason"] = dict(sorted(Counter(row["reason"] for row in report["rows"]).items()))
    summary["bytes_by_reason"] = {
        reason: sum(row["bytes"] or 0 for row in report["rows"] if row["reason"] == reason)
        for reason in summary["by_reason"]
    }
    return summary


def restore(ledger: Ledger, entry_id: str) -> dict[str, Any]:
    """Rename one retained entry back to its original path, never replacing anything, and verify it.

    Raises ``KeyError`` for an unknown ledger id and ``LedgerError`` while a
    sweep holds the ledger. The ``restore`` record precedes the rename; the
    ``restored`` record, written once both directories are synced, carries
    the manifest verification. An unknown id is refused before the lock, so
    it never creates the ledger directory. A ``purging`` entry (a purge that
    stopped part-way) can be restored too: what survives comes back, and the
    verification lists what is missing.
    """
    if entry_id not in ledger.entries()[0]:
        raise KeyError(entry_id)
    with ledger.exclusive(wait=False):
        entries, _ = ledger.entries()
        entry = entries[entry_id]
        result: dict[str, Any] = {"ledger_id": entry_id, "original_path": str(entry.original), "restored": False}
        if entry.state not in {"pending", "quarantined", "return_blocked", "purging"}:
            return result | {"reason": f"state_{entry.state}"}
        if not _identity_at(entry.location, entry.intent["identity"]):
            return result | {"reason": "quarantine_location_missing"}
        if os.path.lexists(entry.original):
            return result | {"reason": "original_path_exists"}
        run_id = new_run_id(time.time())
        ledger.append(_event(entry_id, run_id, "restore"))
        try:
            _rename_path(entry.location, entry.original)
        except OSError as error:
            ledger.append(_event(entry_id, run_id, "restore_failed", error=_errno_name(error)))
            reason = "original_path_exists" if error.errno == errno.EEXIST else "rename_refused"
            return result | {"reason": reason, "error": _errno_name(error)}
        verification = verify_restored(entry, entry.original)
        ledger.append(_event(entry_id, run_id, "restored", **verification))
        _drop_empty_quarantine(entry.location)
        return result | {"restored": True} | verification


def _since(value: str, *, end: bool = False) -> float:
    """An ISO date or datetime as epoch seconds (UTC when no zone); a bare ``--until`` date covers that whole day."""
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    if end and "T" not in value and " " not in value:
        return moment.timestamp() + 86400
    return moment.timestamp()


def ledger_rows(
    ledger: Ledger,
    *,
    path: str | None = None,
    since: float | None = None,
    until: float | None = None,
    run_id: str | None = None,
    entry_id: str | None = None,
    manifest: bool = False,
) -> list[dict[str, Any]]:
    """Ledger records matching every given filter, in file order; each carries its entry's original path."""
    records, _ = ledger.read()
    origins = {r["ledger_id"]: r.get("original_path", "") for r in records if r["event"] == "quarantine"}
    selected = []
    for record in records:
        origin = origins.get(record["ledger_id"], "")
        try:
            at = parse_iso(record["at"])
        except (KeyError, TypeError, ValueError):
            at = None
        if (path and path not in origin) or (run_id and record.get("run_id") != run_id):
            continue
        if (entry_id and record["ledger_id"] != entry_id) or (since is not None and (at is None or at < since)):
            continue
        if until is not None and (at is None or at >= until):
            continue
        shown = {"original_path": origin} | record
        if not manifest:
            shown.pop("manifest", None)
        selected.append(shown)
    return selected


def quarantine_rows(ledger: Ledger, *, now: float, quarantine_s: float) -> list[dict[str, Any]]:
    """Every entry the ledger holds in quarantine: state, age, size, purge date and presence."""
    entries, _ = ledger.entries()
    rows = []
    for entry in sorted(entries.values(), key=lambda item: item.quarantined_at):
        if entry.state not in HELD_STATES:
            continue
        try:
            present = _identity_at(entry.location, entry.intent["identity"])
        except OSError:
            present = None
        rows.append(
            {
                "ledger_id": entry.ledger_id,
                "state": entry.state,
                "original_path": str(entry.original),
                "quarantine_path": str(entry.location),
                "quarantined_at": entry.intent["at"],
                "age_days": round((now - entry.quarantined_at) / 86400, 2),
                "purge_after": utc_iso(entry.quarantined_at + quarantine_s),
                "allocated_bytes": entry.intent.get("allocated_bytes"),
                "file_count": entry.intent.get("file_count"),
                "present": present,
            }
        )
    return rows


def _cell(value: Any) -> str:
    """Plain text as is; a string with a pipe or unprintable characters (a path, say) JSON-quoted."""
    if isinstance(value, str) and (not value.isprintable() or "|" in value):
        return json.dumps(value, ensure_ascii=True).replace("|", "\\|")
    return str(value)


def _state_dir_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--state-dir",
        type=Path,
        help=(
            "Ledger directory (default $XDG_STATE_HOME/learn-ukrainian/tmp-sweep, else "
            "~/.local/state/learn-ukrainian/tmp-sweep; never under the temp root or the repository)."
        ),
    )


def _quarantine_days_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--quarantine-days",
        type=float,
        default=DEFAULT_QUARANTINE_S / 86400,
        help="Retention window before a quarantined entry may be purged (positive days; default 7; example 14).",
    )


def build_ledger_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.hygiene.tmp_sweep",
        description=(
            "Inspect the temp sweep's deletion ledger and quarantine, or restore a quarantined entry.\n"
            "Use to find what the sweep removed and bring it back within the window; "
            "run the sweep itself without a subcommand."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep ledger --path my-scratch --since 2026-10-01\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep quarantine --json\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep restore 3f9c2a7b1d04\n"
            "Outputs: stdout table or JSON; restore renames one entry back and appends ledger records.\n"
            "Exit codes: 0 success; 1 restore refused, failed or different, or ledger unavailable; "
            "2 invalid arguments or unknown ledger id; 3 restored, but files above the digest limit "
            "matched by size and mtime only (unverified).\n"
            "Related: #9887; docs/runbooks/tmp-retention.md; scripts.hygiene.tmp_sweep_ledger."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    ledger = commands.add_parser(
        "ledger",
        help="List ledger records, filtered by path, date or run.",
        description=(
            "List ledger records in file order; every filter given must match.\n"
            "Use to find what the sweep moved, returned, purged or restored; read-only, it never changes "
            "the ledger or the quarantine (use `restore` for that)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example: .venv/bin/python -m scripts.hygiene.tmp_sweep ledger --run-id 20261006T053012Z-a1b2c3 --json\n"
            "Outputs: stdout table or JSON records (manifests only with --manifest). Exit codes: 0; 1 ledger unreadable.\n"
            "Related: #9887; docs/runbooks/tmp-retention.md (Deletion ledger and quarantine); "
            "scripts.hygiene.tmp_sweep_ledger."
        ),
    )
    ledger.add_argument("--path", help="Substring of the original path (example: hand-made-scratch).")
    ledger.add_argument("--since", help="Records at or after this UTC date or datetime (example 2026-10-01).")
    ledger.add_argument(
        "--until", help="Records before this UTC datetime; a bare date includes that whole day (example 2026-10-06)."
    )
    ledger.add_argument("--run-id", help="Records of one sweep or restore run (example 20261006T053012Z-a1b2c3).")
    ledger.add_argument("--ledger-id", help="Records of one entry (example 3f9c2a7b1d04).")
    ledger.add_argument("--manifest", action="store_true", help="Include file manifests in JSON (default off).")
    ledger.add_argument("--json", action="store_true", help="Print JSON instead of a table (default table).")
    _state_dir_argument(ledger)
    quarantine = commands.add_parser(
        "quarantine",
        help="List entries held in quarantine, with age and size.",
        description=(
            "List every entry the ledger holds in quarantine, oldest first, with its purge date.\n"
            "Use to see what is still recoverable and when it may be purged; read-only, it neither purges "
            "nor restores (the sweep's --apply purges, `restore` restores)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example: .venv/bin/python -m scripts.hygiene.tmp_sweep quarantine --quarantine-days 7\n"
            "Outputs: stdout table or JSON. Exit codes: 0; 1 ledger unreadable.\n"
            "Related: #9887; docs/runbooks/tmp-retention.md (Purge); scripts.hygiene.tmp_sweep_ledger."
        ),
    )
    quarantine.add_argument("--json", action="store_true", help="Print JSON instead of a table (default table).")
    _quarantine_days_argument(quarantine)
    _state_dir_argument(quarantine)
    restore_parser = commands.add_parser(
        "restore",
        help="Rename one quarantined entry back to its original path.",
        description=(
            "Rename a quarantined entry back atomically, never replacing an existing path, "
            "then verify it against its recorded manifest.\n"
            "Use for an entry still held in quarantine (see `quarantine`); not for purged entries, "
            "which are gone, or for anything the sweep never moved."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example: .venv/bin/python -m scripts.hygiene.tmp_sweep restore 3f9c2a7b1d04\n"
            "Outputs: stdout JSON result with `verification` (verified, unverified_digest_skipped, mismatch "
            "or unreadable); ledger records restore and restored (or restore_failed).\n"
            "Exit codes: 0 restored and byte-verified; 1 refused, failed, restored but different, or a sweep "
            "holds the ledger; 2 unknown ledger id; 3 restored, but files above the digest limit matched "
            "by size and mtime only (listed in digest_unverified).\n"
            "Related: #9887; docs/runbooks/tmp-retention.md (Restore); scripts.hygiene.tmp_sweep_ledger."
        ),
    )
    restore_parser.add_argument("ledger_id", help="Ledger id from `ledger` or `quarantine` (example 3f9c2a7b1d04).")
    _state_dir_argument(restore_parser)
    return parser


def ledger_main(argv: list[str]) -> int:
    parser = build_ledger_parser()
    args = parser.parse_args(argv)
    ledger = Ledger((args.state_dir or default_state_dir()).expanduser())
    try:
        if args.command == "restore":
            try:
                result = restore(ledger, args.ledger_id)
            except KeyError:
                parser.error(f"unknown ledger id {args.ledger_id!r}")
            print(json.dumps(result, sort_keys=True, indent=2))
            if not result["restored"]:
                return 1
            return {"verified": 0, "unverified_digest_skipped": 3}.get(result.get("verification", ""), 1)
        if args.command == "quarantine":
            if not math.isfinite(args.quarantine_days) or args.quarantine_days <= 0:
                parser.error("--quarantine-days must be finite and positive")
            rows = quarantine_rows(ledger, now=time.time(), quarantine_s=args.quarantine_days * 86400)
            columns = ("ledger_id", "state", "age_days", "allocated_bytes", "purge_after", "present", "original_path")
        else:
            try:
                since = _since(args.since) if args.since else None
                until = _since(args.until, end=True) if args.until else None
            except ValueError:
                parser.error("--since/--until take an ISO date or datetime")
            rows = ledger_rows(
                ledger,
                path=args.path,
                since=since,
                until=until,
                run_id=args.run_id,
                entry_id=args.ledger_id,
                manifest=args.manifest,
            )
            columns = ("at", "event", "ledger_id", "run_id", "original_path", "reason", "outcome", "found", "error")
    except LedgerError as error:
        print(f"ledger unavailable or not durable: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(rows, sort_keys=True, indent=2))
        return 0
    print("| " + " | ".join(columns) + " |")
    print("|" + "---|" * len(columns))
    for row in rows:
        print("| " + " | ".join(_cell(row.get(column, "")) for column in columns) + " |")
    return 0


SUBCOMMANDS = frozenset({"ledger", "quarantine", "restore"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Attribute unmanaged top-level temp entries; quarantine proven ones recoverably and purge expired ones.\n"
            "Use for legacy task residue and, with --unattributed-scratch, quiet hand-made scratch; "
            "never for managed scratch or harness state. Subcommands ledger, quarantine and restore "
            "inspect and undo removals (see `tmp_sweep ledger --help`)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep --json\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --summary\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --apply --summary\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep restore <ledger-id>\n"
            "Outputs: stdout inventory (or --summary counts) with ledger location, quarantine and purge totals; "
            "with --apply, appends to the ledger, moves proven entries into quarantine and deletes only "
            "expired, re-verified quarantined entries.\n"
            "Exit codes: 0 inventory complete; 1 scan/quarantine/purge errors or ledger unavailable; "
            "2 invalid arguments.\n"
            "Related: #8755, #9737, #9887; docs/runbooks/tmp-retention.md; scripts.hygiene.retention_engine; "
            "scripts.hygiene.tmp_sweep_ledger; packaging/systemd/learn-ukrainian-tmp-sweep.*."
        ),
    )
    parser.add_argument(
        "--temp-root",
        type=Path,
        default=Path("/tmp"),
        help="System temp area to inventory (default /tmp; example /private/tmp).",
    )
    parser.add_argument(
        "--task-root",
        type=Path,
        help="Task-record directory (default shared batch_state/tasks; example fixture/tasks).",
    )
    parser.add_argument(
        "--min-age-hours",
        type=float,
        default=12,
        help="Task-attributed class: minimum latest-write age (positive hours; default 12; example 24).",
    )
    parser.add_argument(
        "--unattributed-scratch",
        action="store_true",
        help=(
            "Also reap agent-owned top-level files and directories with no task owner once they pass "
            "the scratch age, quiet and liveness gates (default off; #9737)."
        ),
    )
    parser.add_argument(
        "--scratch-age-hours",
        type=float,
        default=24,
        help="Scratch class: minimum age of the top-level entry itself (positive hours; default 24; example 48).",
    )
    parser.add_argument(
        "--scratch-quiet-hours",
        type=float,
        default=24,
        help="Scratch class: no write or change anywhere inside for this long (positive hours; default 24).",
    )
    _quarantine_days_argument(parser)
    parser.add_argument(
        "--digest-limit-mib",
        type=float,
        default=DEFAULT_DIGEST_LIMIT / (1 << 20),
        help=(
            "Manifest SHA-256 only for regular files up to this size (MiB; default 64; larger files are "
            "recorded by size and mtime and reported unverified on restore)."
        ),
    )
    _state_dir_argument(parser)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Purge expired quarantine, then recheck proofs and quarantine proven entries (default dry-run).",
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--json", action="store_true", help="Print machine-readable inventory (default Markdown table)."
    )
    output.add_argument(
        "--summary",
        action="store_true",
        help="Print JSON counts and byte totals only, without entry names (default off).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in SUBCOMMANDS:
        return ledger_main(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        scratch = (
            ScratchPolicy(min_age_s=args.scratch_age_hours * 3600, quiet_s=args.scratch_quiet_hours * 3600)
            if args.unattributed_scratch
            else None
        )
        if not math.isfinite(args.digest_limit_mib) or args.digest_limit_mib < 0:
            raise ValueError("digest limit must be finite and non-negative")
        report = sweep(
            temp_root=args.temp_root,
            task_root=args.task_root,
            min_age_s=args.min_age_hours * 3600,
            scratch=scratch,
            apply=args.apply,
            state_dir=args.state_dir,
            quarantine_s=args.quarantine_days * 86400,
            digest_limit=int(args.digest_limit_mib * (1 << 20)),
        )
    except LedgerError as error:
        # The step in progress stays unconfirmed in the ledger, and the next run reconciles it.
        print(f"ledger unavailable or not durable, run stopped: {error}", file=sys.stderr)
        return 1
    except (ValueError, OSError):
        parser.error("invalid or unreadable temporary/task area; no deletion authorized")
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    elif args.summary:
        print(json.dumps(summarize(report), sort_keys=True, indent=2))
    else:
        print("| Entry | Allocated bytes | Task / live PID attribution | Decision | Reason |")
        print("|---|---:|---|---|---|")
        for row in report["rows"]:
            name = json.dumps(row["name"], ensure_ascii=True).replace("|", "\\|")
            owner = row["task"] or ("live process" if row["live_pids"] else "unknown")
            print(f"| {name} | {row['bytes']} | {owner} | {row['decision']} | {row['reason']} |")
        print(
            f"mode={report['mode']} directories={report['directories']} files={report['files']} errors={report['errors']}"
        )
        print(
            f"quarantined={report['quarantined_entries']} quarantine_held={report['quarantine_held_entries']} "
            f"purgeable={report['purgeable_entries']} purged={report['purged_entries']} ledger={report['ledger_path']}"
        )
        print(
            f"bytes_reclaimable={report['bytes_reclaimable']} bytes_reclaimed={report['bytes_reclaimed']} free_bytes={report['free_bytes']} projected_free_bytes={report['projected_free_bytes']}"
        )
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
