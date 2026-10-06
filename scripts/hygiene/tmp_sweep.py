"""Attribute unmanaged system-temp directories; preserve every unproven owner (#8755).

The opt-in unattributed-scratch class (#9737, operator retention decision
2026-10-06) also reaps hand-made top-level scratch that no task owns, once it
is proven quiet and unreferenced by every process and every unsettled task.
Every safety fact must be positively known at removal time: an uninspectable
process, an unreadable task record or a path a live task names preserves.

Consistency boundary (#9872): a proven candidate is first renamed into a
per-run quarantine directory, so no process can newly reach it by its old
path. The holder, task and write checks then re-run against the quarantined
entry; anything found or unknown renames it back, and only a clean result
removes it.
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
import time
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.common.scratch import DEFAULT_SCRATCH_ROOT, fallback_scratch_root, resolve_scratch_root
from scripts.common.task_scratch import TaskScratchError, mount_points
from scripts.common.task_store_paths import tasks_dir
from scripts.hygiene.retention_engine import plan_digest, reap_attributed_temp
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
    fd = os.open(name, _DIR_FLAGS, dir_fd=root_fd)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        raise
    return Quarantine(root / name, fd)


def close_quarantine(quarantine: Quarantine, root_fd: int) -> None:
    """Remove the quarantine if empty; an entry kept as ``restore_blocked`` keeps it for recovery."""
    try:
        with contextlib.suppress(OSError):
            os.rmdir(quarantine.path.name, dir_fd=root_fd)
    finally:
        os.close(quarantine.fd)


def _bare_row(name: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "decision": "preserve", "reason": reason, "bytes": 0, "task": None, "live_pids": []} | extra


def recover_quarantines(root: Path, root_fd: int, *, apply: bool) -> tuple[list[dict[str, Any]], int, int]:
    """Return every crashed run's quarantined entry to its original name; delete nothing.

    A quarantine still locked belongs to a live run and is skipped. A leftover
    entry's pre-rename snapshot died with its run, so its write check is
    unknown and the boundary rule restores it; it then re-enters the normal
    pipeline as an ordinary candidate. When the original name is taken, the
    entry stays quarantined as ``restore_blocked``. Dry runs only report.
    Returns ``(rows, restored, errors)``.
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
                if not apply:
                    rows.append(_bare_row(entry, "quarantine_leftover", quarantine=name))
                    continue
                try:
                    rename_noreplace(fd, entry, root_fd, entry)
                    restored += 1
                except OSError as error:
                    rows.append(_bare_row(entry, "restore_blocked", quarantine=name, error=_errno_name(error)))
                    errors += 1
            if apply:
                with contextlib.suppress(OSError):
                    os.rmdir(name, dir_fd=root_fd)
        finally:
            os.close(fd)
    return rows, restored, errors


def quarantined_problem(
    quarantined: Path, origin: Path, row: dict[str, Any], before: dict[str, tuple[Any, ...]], task_root: Path
) -> str | None:
    """Re-prove the renamed entry; return a preserve reason, or ``None`` when removal is safe.

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


def quarantine_and_reap(
    path: Path,
    row: dict[str, Any],
    before: dict[str, tuple[Any, ...]],
    quarantine: Quarantine,
    *,
    root_fd: int,
    task_root: Path,
    repo_root: Path,
) -> dict[str, Any]:
    """Rename, re-verify, then restore or remove one proven candidate; return its final row."""
    name = path.name
    quarantined = quarantine.path / name
    try:
        rename_noreplace(root_fd, name, quarantine.fd, name)
    except OSError as error:
        return row | {"decision": "preserve", "reason": "quarantine_failed", "error": _errno_name(error)}
    reason = quarantined_problem(quarantined, path, row, before, task_root)
    if reason is None:
        try:
            reap_attributed_temp(
                quarantined,
                repo_root=repo_root,
                temp_root=quarantine.path,
                expected_dev=row["identity"][0],
                expected_ino=row["identity"][1],
            )
        except (OSError, ValueError, TaskScratchError):
            reason = "reap_refused"
        else:
            if quarantined.exists() or quarantined.is_symlink():
                raise OSError("common reaper left residue")
            return row | {"decision": "reaped"}
    try:
        rename_noreplace(quarantine.fd, name, root_fd, name)
    except OSError as error:
        return row | {
            "decision": "preserve",
            "reason": "restore_blocked",
            "found": reason,
            "quarantine": quarantine.path.name,
            "error": _errno_name(error),
        }
    return row | {"decision": "preserve", "reason": reason}


def sweep(
    *,
    temp_root: Path = Path("/tmp"),
    task_root: Path | None = None,
    repo_root: Path = REPO_ROOT,
    min_age_s: float = 12 * 3600,
    scratch: ScratchPolicy | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    """Inventory top-level unmanaged entries; quarantine, re-verify and reap proven ones on ``apply``."""
    if not math.isfinite(min_age_s) or min_age_s <= 0:
        raise ValueError("minimum age must be finite and positive")
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
    tasks = task_root if task_root is not None else tasks_dir()
    root_fd = os.open(root, _DIR_FLAGS)
    quarantine: Quarantine | None = None
    reclaimed = 0
    try:
        # Restore crash leftovers first, so every probe below sees them at their original names.
        rows, restored, errors = recover_quarantines(root, root_fd, apply=apply)
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
                        row = quarantine_and_reap(
                            path, row, before, quarantine, root_fd=root_fd, task_root=tasks, repo_root=repo_root
                        )
                        if row["decision"] == "reaped":
                            reclaimed += row["bytes"]
                        elif row["reason"] in {"restore_blocked", "reap_refused"}:
                            errors += 1
                rows.append(row)
            except (OSError, ValueError, TaskScratchError):
                errors += 1
                rows.append(_bare_row(path.name, "scan_or_reap_error"))
    finally:
        if quarantine is not None:
            close_quarantine(quarantine, root_fd)
        os.close(root_fd)
    free = shutil.disk_usage(root).free
    reclaimable = sum(row["bytes"] for row in rows if row["decision"] == "would_reap")
    report = {
        "schema": "tmp-sweep.v1",
        "mode": "apply" if apply else "dry-run",
        "min_age_hours": min_age_s / 3600,
        "scratch_policy": None
        if scratch is None
        else {"min_age_hours": scratch.min_age_s / 3600, "quiet_hours": scratch.quiet_s / 3600},
        "rows": rows,
        "directories": sum(1 for row in rows if row.get("kind") != "file"),
        "files": sum(1 for row in rows if row.get("kind") == "file"),
        "errors": errors,
        "quarantine_restored": restored,
        "process_probe_complete": complete,
        "task_inventory_complete": inventory.complete,
        "bytes_reclaimable": reclaimable,
        "bytes_reclaimed": reclaimed,
        "free_bytes": free,
        "projected_free_bytes": free + reclaimable,
    }
    report["digest"] = plan_digest(report)
    return report


def summarize(report: dict[str, Any]) -> dict[str, Any]:
    """Counts and byte totals only: no entry names, safe for logs and public reports."""
    summary = {key: value for key, value in report.items() if key != "rows"}
    summary["by_decision"] = dict(sorted(Counter(row["decision"] for row in report["rows"]).items()))
    summary["by_reason"] = dict(sorted(Counter(row["reason"] for row in report["rows"]).items()))
    summary["bytes_by_reason"] = {
        reason: sum(row["bytes"] or 0 for row in report["rows"] if row["reason"] == reason)
        for reason in summary["by_reason"]
    }
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Attribute and safely reap unmanaged top-level temp entries.\n"
            "Use for legacy task residue and, with --unattributed-scratch, quiet hand-made scratch; "
            "never for managed scratch or harness state."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep --json\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --summary\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --apply --summary\n"
            "Outputs: stdout inventory (or --summary counts) and allocation/headroom totals; "
            "deletion only with --apply.\n"
            "Exit codes: 0 inventory complete; 1 scan/reap errors; 2 invalid arguments.\n"
            "Related: #8755, #9737; docs/runbooks/tmp-retention.md; scripts.hygiene.retention_engine; "
            "packaging/systemd/learn-ukrainian-tmp-sweep.*."
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
    parser.add_argument(
        "--apply", action="store_true", help="Recheck proofs and call the common reaper (default dry-run)."
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
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        scratch = (
            ScratchPolicy(min_age_s=args.scratch_age_hours * 3600, quiet_s=args.scratch_quiet_hours * 3600)
            if args.unattributed_scratch
            else None
        )
        report = sweep(
            temp_root=args.temp_root,
            task_root=args.task_root,
            min_age_s=args.min_age_hours * 3600,
            scratch=scratch,
            apply=args.apply,
        )
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
            f"bytes_reclaimable={report['bytes_reclaimable']} bytes_reclaimed={report['bytes_reclaimed']} free_bytes={report['free_bytes']} projected_free_bytes={report['projected_free_bytes']}"
        )
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
