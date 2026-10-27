"""Read-only checkout guard for v2 dispatch: harness init, snapshots and mutation diff.

Mechanical port of the ``scripts/delegate.py`` ``_read_only_*`` family (C-2188,
delegate retirement unit D4). A read-only task initializes its provider harness
first, then snapshots the checkout and the other tasks' terminal results; after
the provider exits it snapshots again, and any attributable change fails the
task. Function bodies are copied unchanged except where they named delegate's
task store, which now resolves through the v2 record location.
"""

import contextlib
import errno
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any

from scripts.common.task_store_paths import tasks_dir

DEFAULT_GIT_TIMEOUT_S: float = 30.0
_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX = ".snapshots"
# A sibling result is attributable only while its task is finished (delegate.py _TERMINAL_STATUSES).
_TERMINAL_STATUSES = frozenset(
    {"done", "failed", "timeout", "rate_limited", "crashed", "cancelled", "dry_run", "needs_finalize", "no_deliverable"}
)


def _state_path(task_id: str) -> Path:
    return tasks_dir() / f"{task_id}.json"


def _read_only_snapshot_dir_for(task_id: str) -> Path:
    state_path = _state_path(task_id)
    return state_path.parent / f"{state_path.stem}{_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX}"


_READ_ONLY_SNAPSHOT_DIGEST_NAME = "digest.json"
_READ_ONLY_SNAPSHOT_RETENTION_DIGEST = "digest"
_READ_ONLY_SNAPSHOT_RETENTION_FULL = "full"


def _read_only_snapshot_sidecar_path(task_id: str, phase: str) -> Path:
    return _read_only_snapshot_dir_for(task_id) / f"read_only_checkout_{phase}.json"


def _write_read_only_snapshot_sidecar(
    task_id: str,
    phase: str,
    snapshot: dict[str, str] | None,
) -> None:
    """Persist a read-only checkout snapshot beside the task record."""
    path = _read_only_snapshot_sidecar_path(task_id, phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_text(
        json.dumps(snapshot if snapshot is not None else {}, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _canonical_snapshot_bytes(snapshot: dict[str, str] | None) -> bytes:
    """Bytes written for a phase sidecar: compact JSON, empty object when missing."""
    payload = snapshot if isinstance(snapshot, dict) else {}
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _snapshot_digest_phase(snapshot: dict[str, str] | None) -> dict[str, Any]:
    raw = _canonical_snapshot_bytes(snapshot)
    payload = snapshot if isinstance(snapshot, dict) else {}
    return {"sha256": hashlib.sha256(raw).hexdigest(), "entries": len(payload)}


def read_only_snapshot_digest(
    pre: dict[str, str] | None,
    post: dict[str, str] | None,
) -> dict[str, Any]:
    """Content digest of the two canonical checkout snapshots."""
    return {"pre": _snapshot_digest_phase(pre), "post": _snapshot_digest_phase(post)}


def read_only_snapshot_keep_full(
    mutation_paths: list[str] | None,
    snapshot_error: str | None,
) -> bool:
    """Full sidecars stay only for a recorded mutation or a snapshot error."""
    return bool(mutation_paths) or snapshot_error is not None


def _read_only_phase_paths(snapshot_dir: Path) -> list[Path]:
    return [snapshot_dir / f"read_only_checkout_{phase}.json" for phase in ("pre", "post")]


def stage_read_only_snapshot_digest(
    snapshot_dir: Path,
    pre: dict[str, str] | None,
    post: dict[str, str] | None,
) -> int:
    """Write ``digest.json`` and leave the phase files in place.

    Returns the bytes a later discard would reclaim. Writing the digest first
    means a crash before the task record is published still leaves the full
    sidecars on disk.
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    before = 0
    for path in _read_only_phase_paths(snapshot_dir):
        try:
            info = path.lstat()
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode):
            before += info.st_size
    digest = read_only_snapshot_digest(pre, post)
    digest_path = snapshot_dir / _READ_ONLY_SNAPSHOT_DIGEST_NAME
    raw = json.dumps(digest, separators=(",", ":")).encode("utf-8")
    tmp = digest_path.with_suffix(f".json.tmp.{os.getpid()}")
    tmp.write_bytes(raw)
    os.replace(tmp, digest_path)
    return before - len(raw)


def discard_read_only_snapshot_phases(snapshot_dir: Path) -> None:
    """Unlink regular phase files. Symlinks are left in place."""
    for path in _read_only_phase_paths(snapshot_dir):
        try:
            info = path.lstat()
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode):
            path.unlink()


def _read_state_json(path: Path) -> dict[str, Any] | None:
    """Read a state file without hydrating read-only snapshot sidecars."""
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


_GIT_ENV_DENYLIST = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_COMMON_DIR",
}


def _sanitized_git_env() -> dict[str, str]:
    """Select the explicit repository and refuse interactive credential prompts."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENV_DENYLIST and not key.startswith("PRE_COMMIT")
    }
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _format_process_failure(proc: subprocess.CompletedProcess[str]) -> str:
    detail = (proc.stderr or proc.stdout or "").strip()
    if detail:
        return detail.splitlines()[-1]
    return f"exit {proc.returncode}"


# Top-level checkout dirs the read-only snapshot never records. Other lanes'
# dispatch worktrees live under ``.worktrees/`` (layout A): concurrent activity
# there — including writes inside a sandbox that already existed at pre-snapshot
# time — is never this task's mutation, and it false-failed cleanly-successful
# read-only dispatches (#7124). The guard diffs only what the task could own.
_READ_ONLY_SNAPSHOT_EXCLUDED_TOP_LEVEL_DIRS = frozenset({".worktrees"})
# The workspace guard file the AGY adapter installs and AGY executes (#10727).
_READ_ONLY_AGY_HOOK_PATH = ".agents/hooks.json"
_READ_ONLY_AGY_HOOK_SNAPSHOT_ERROR = "agy hook snapshot failed:"
# Snapshot errors that withhold content evidence Git status cannot provide.
# A read-only task with one never settles ``done``.
_READ_ONLY_FAIL_CLOSED_SNAPSHOT_ERRORS = (
    "linked database snapshot failed:",
    _READ_ONLY_AGY_HOOK_SNAPSHOT_ERROR,
    "opencode snapshot failed:",
)


def _read_only_snapshot_error_fails_closed(error: str | None) -> bool:
    """Return whether a snapshot error must fail the read-only task."""
    return (error or "").startswith(_READ_ONLY_FAIL_CLOSED_SNAPSHOT_ERRORS)


def _is_read_only_snapshot_excluded_path(path: str) -> bool:
    """Return whether a checkout-relative path is outside the snapshot scope."""
    normalized = _normalize_read_only_relpath(path)
    top_level = normalized.split("/", 1)[0]
    return top_level in _READ_ONLY_SNAPSHOT_EXCLUDED_TOP_LEVEL_DIRS


def _read_only_checkout_snapshot(cwd: Path, *, agy_hook: bool = False) -> tuple[dict[str, str] | None, str | None]:
    """Capture Git state and linked database contents for a read-only worker.

    The snapshot includes ignored files because a writeful legacy audit can
    create ignored cache entries that ordinary ``git status`` deliberately
    hides.  It is diagnostic only: this guard reports leaked paths and never
    removes them, since a pre-existing user file cannot be attributed safely.

    Paths under ``.worktrees/`` are excluded entirely (#7124): they belong to
    concurrent dispatch lanes, not to the task being guarded.
    Provisioned DB links retain their Git status when the primary target is
    written (#9421). Fingerprint their link text, resolved path, and contents,
    including SQLite's persistent journal/WAL at the resolved target, so a
    write followed by retargeting to an older copy cannot settle ``done``.
    The ignored AGY guard file keeps its status through a valid-to-valid
    rewrite, so with ``agy_hook`` its bytes are fingerprinted the same way
    and an acquisition failure fails the snapshot (#10727). Only AGY
    executes that guard; other agents keep the snapshot without it.
    """
    commands = (
        (
            "status",
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        ),
        (
            "ignored",
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"],
        ),
    )
    outputs: dict[str, str] = {}
    for label, command in commands:
        try:
            proc = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                env=_sanitized_git_env(),
                timeout=DEFAULT_GIT_TIMEOUT_S,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return None, f"{label} snapshot could not start: {type(exc).__name__}: {exc}"
        if proc.returncode != 0:
            return None, f"{label} snapshot failed: {_format_process_failure(proc)}"
        outputs[label] = proc.stdout or ""

    entries: dict[str, str] = {}
    status_records = outputs["status"].split("\0")
    index = 0
    while index < len(status_records):
        record = status_records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4 or record[2] != " ":
            return None, "status snapshot returned an unparseable porcelain record"
        state, path = record[:2], record[3:]
        # Porcelain v1 emits the pre-rename/pre-copy path as a second NUL item.
        # Consume it even for excluded paths so the record stream stays aligned.
        rename_source: str | None = None
        if "R" in state or "C" in state:
            if index >= len(status_records) or not status_records[index]:
                return None, "status snapshot returned an incomplete rename/copy record"
            rename_source = status_records[index]
            index += 1
        # Filter the rename/copy source and destination independently
        # (#7147): ``git mv tracked.txt .worktrees/lane/tracked.txt`` must still
        # surface the tracked source deletion even though the destination is
        # out of snapshot scope.
        if not _is_read_only_snapshot_excluded_path(path):
            entries[path] = state
        if rename_source is not None and not _is_read_only_snapshot_excluded_path(rename_source):
            entries[rename_source] = f"{state}:source"
    # ``git status`` without ``--ignored`` omits ignored paths entirely. The
    # second status invocation makes those paths observable as ``!!`` while
    # retaining porcelain's tracked/untracked classification for the first
    # invocation. Do not let the second invocation overwrite real statuses.
    for record in outputs["ignored"].split("\0"):
        if len(record) < 4 or record[:2] != "!!" or record[2] != " ":
            continue
        path = record[3:]
        if not _is_read_only_snapshot_excluded_path(path):
            entries[path] = "!!"
    # Initialization precedes the baseline. Hash its output as well as tracked
    # plugins so an ignored-to-ignored rewrite after that baseline still trips.
    try:
        for path, fingerprint in _read_only_opencode_fingerprints(cwd).items():
            entries[path] = entries.get(path, "!!") + ":" + fingerprint
    except OSError as exc:
        return None, f"opencode snapshot failed: {type(exc).__name__}"
    # Discover database links directly so every provisioned link is covered
    # without duplicating the provisioning paths in another scope.
    try:
        with os.scandir(cwd / "data") as data_entries:
            database_paths = sorted(Path(entry.path) for entry in data_entries if entry.name.endswith(".db"))
    except FileNotFoundError:
        database_paths = []
    except OSError as exc:
        return None, f"linked database snapshot failed: data: {type(exc).__name__}"
    for link in database_paths:
        if not link.is_symlink():
            continue
        relative_path = link.relative_to(cwd).as_posix()
        try:
            link_text = os.readlink(link)
            target = link.resolve(strict=True)
            fingerprints = []
            for suffix in ("", "-journal", "-wal"):
                database_file = Path(f"{target}{suffix}")
                try:
                    with database_file.open("rb") as handle:
                        digest = hashlib.file_digest(handle, "sha256").hexdigest()
                except FileNotFoundError:
                    if not suffix:
                        raise
                    digest = None
                fingerprints.append(digest)
        except (OSError, RuntimeError) as exc:
            return None, f"linked database snapshot failed: {relative_path}: {type(exc).__name__}"
        entries[relative_path] = (
            entries.get(relative_path, "!!")
            + ":"
            + json.dumps({"link_text": link_text, "resolved_path": str(target), "contents": fingerprints})
        )
    if not agy_hook:
        return entries, None
    hook_fingerprint, hook_error = _read_only_agy_hook_fingerprint(cwd)
    if hook_error is not None:
        return None, hook_error
    if hook_fingerprint is not None:
        entries[_READ_ONLY_AGY_HOOK_PATH] = (
            entries.get(_READ_ONLY_AGY_HOOK_PATH, "!!") + ":" + json.dumps(hook_fingerprint)
        )
    return entries, None


def _read_only_opencode_fingerprints(cwd: Path) -> dict[str, str]:
    """Hash the exact OpenCode tree without traversing symlinks (#11347).

    Directory descriptors and no-follow opens keep a replaced directory from
    redirecting the walk outside the checkout. Links record their text, never
    grant a directory exemption, and never cause an external tree to be read.
    """
    fingerprints: dict[str, str] = {}

    def visit(parent_fd: int, name: str, relative: str) -> None:
        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        value: list[Any] = [info.st_mode]
        if stat.S_ISLNK(info.st_mode):
            value.append(os.readlink(name, dir_fd=parent_fd))
        elif stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode):
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
            if stat.S_ISDIR(info.st_mode):
                flags |= os.O_DIRECTORY
            fd = os.open(name, flags, dir_fd=parent_fd)
            try:
                acquired = os.fstat(fd)
                if (acquired.st_dev, acquired.st_ino, acquired.st_mode) != (info.st_dev, info.st_ino, info.st_mode):
                    raise OSError("OpenCode entry changed during snapshot")
                if stat.S_ISDIR(info.st_mode):
                    for child in sorted(os.listdir(fd)):
                        visit(fd, child, f"{relative}/{child}")
                else:
                    with os.fdopen(os.dup(fd), "rb") as handle:
                        value.append(hashlib.file_digest(handle, "sha256").hexdigest())
                after = os.fstat(fd)
                if (info.st_mtime_ns, info.st_ctime_ns, info.st_size) != (
                    after.st_mtime_ns,
                    after.st_ctime_ns,
                    after.st_size,
                ):
                    raise OSError("OpenCode entry changed during snapshot")
            finally:
                os.close(fd)
        fingerprints[relative] = json.dumps(value)

    root_fd = os.open(cwd, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        try:
            os.stat(".opencode", dir_fd=root_fd, follow_symlinks=False)
        except FileNotFoundError:
            return fingerprints
        visit(root_fd, ".opencode", ".opencode")
    finally:
        os.close(root_fd)
    return fingerprints


def _provision_agy_read_only_guard(cwd: Path) -> None:
    """Install AGY's workspace guard before the read-only baseline (#10727).

    The adapter installs a missing guard while it builds the invocation, after
    the pre-snapshot, so the harness's own file read as a provider mutation.
    Only an absent file is provisioned, through the installer's dispatch
    containment; an existing file, valid or not, is never touched. A failure
    here is left to the adapter's provider-time check, which stays
    authoritative and refuses before any provider subprocess.
    """
    from scripts.agent_runtime.agy_hook_config import install_worktree_guard

    if os.path.lexists(cwd / _READ_ONLY_AGY_HOOK_PATH):
        return
    with contextlib.suppress(OSError, ValueError):
        install_worktree_guard(cwd)


class _AgyHookChangedDuringSnapshot(Exception):
    """The AGY guard changed while the snapshot was reading it."""


def _read_only_agy_hook_fingerprint(cwd: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Fingerprint the AGY guard the adapter validates, through accepted links.

    The adapter follows symlinks anywhere on the way to the guard and
    validates the bytes they lead to, so the record holds every link crossed
    (#10748), the effective file's real path and type, and its bytes
    (#10727). Only a hook missing at the first ``lstat`` is absent:
    ``(None, None)``, and Git status still reports a new ``.agents`` entry. A
    hook or link target lost, made unreadable or changed after that
    observation is an acquisition error, never absence, and the snapshot then
    fails closed. Nothing but a regular effective file is opened, so a FIFO
    or device cannot block the snapshot.
    """
    path = cwd / _READ_ONLY_AGY_HOOK_PATH
    try:
        path.lstat()
    except (FileNotFoundError, NotADirectoryError):
        return None, None
    except OSError as exc:
        return None, f"{_READ_ONLY_AGY_HOOK_SNAPSHOT_ERROR} {_READ_ONLY_AGY_HOOK_PATH}: {type(exc).__name__}"
    try:
        identity, inode = _read_only_agy_hook_identity(cwd)
        digest = _read_only_agy_hook_digest(identity, inode)
        # Re-observe: the links and target read above describe the hashed bytes.
        if _read_only_agy_hook_identity(cwd) != (identity, inode):
            raise _AgyHookChangedDuringSnapshot
    except OSError as exc:
        return None, f"{_READ_ONLY_AGY_HOOK_SNAPSHOT_ERROR} {_READ_ONLY_AGY_HOOK_PATH}: {type(exc).__name__}"
    except _AgyHookChangedDuringSnapshot:
        return None, f"{_READ_ONLY_AGY_HOOK_SNAPSHOT_ERROR} {_READ_ONLY_AGY_HOOK_PATH}: changed during snapshot"
    return {**identity, "sha256": digest}, None


# Linux MAXSYMLINKS: the kernel refuses a path that crosses more links (ELOOP).
_READ_ONLY_AGY_HOOK_MAX_LINKS = 40


def _read_only_agy_hook_identity(cwd: Path) -> tuple[dict[str, Any], tuple[int, int]]:
    """Return every link to the guard and its effective target without reading it.

    The guard path is resolved one component at a time, as the kernel does,
    and each symlink crossed is recorded with its real path and link text.
    ``os.path.realpath`` would collapse them, so a rewired middle link that
    keeps the effective file would go unseen (#10748 F1). Every error
    propagates: the caller has already observed the hook, so a link target
    that is missing, looping or not a directory cannot be acquired and is
    never recorded as a clean baseline (#10748 F2). A hook that leads nowhere
    from the start fails here too, and the adapter still refuses it as a
    missing file. The ``(st_dev, st_ino)`` of the target binds the later read
    to this observation.

    A procfs link (``/proc/<pid>/fd/<n>``, ``cwd``, ``root``, ``exe``) is a
    magic link: the kernel jumps to the file or directory it names, and its
    text, such as ``/memfd:guard (deleted)``, need not be a path at all. Such
    a link is followed by the kernel instead of walked and records the
    identity it leads to; the rest of the guard path is resolved through it.
    """
    links: list[dict[str, Any]] = []
    procfs = _procfs_devices()
    resolved = os.path.realpath(cwd)
    # Whether ``resolved`` crosses a procfs link, so that only the kernel can resolve it.
    through_procfs = False
    pending = _READ_ONLY_AGY_HOOK_PATH.split("/")[::-1]
    while pending:
        name = pending.pop()
        if name in ("", ".", ".."):
            # Like the kernel, refuse to step through or out of a non-directory.
            if not stat.S_ISDIR(_read_only_agy_hook_stat(resolved, through_procfs).st_mode):
                raise NotADirectoryError(errno.ENOTDIR, os.strerror(errno.ENOTDIR), resolved)
            if name == "..":
                resolved = os.path.join(resolved, name) if through_procfs else os.path.dirname(resolved)
            continue
        candidate = os.path.join(resolved, name)
        info = os.lstat(candidate)
        if not stat.S_ISLNK(info.st_mode):
            resolved = candidate
            continue
        if len(links) == _READ_ONLY_AGY_HOOK_MAX_LINKS:
            raise OSError(errno.ELOOP, os.strerror(errno.ELOOP), candidate)
        link_text = os.readlink(candidate)
        link: dict[str, Any] = {"path": candidate, "link_text": link_text, "file_type": stat.S_IFLNK}
        links.append(link)
        if info.st_dev in procfs:
            # A procfs link that can no longer be followed, such as a closed descriptor, raises here.
            target = os.stat(candidate)
            link["target"] = {
                "device": target.st_dev,
                "inode": target.st_ino,
                "file_type": stat.S_IFMT(target.st_mode),
            }
            resolved, through_procfs = candidate, True
            continue
        if link_text.startswith("/"):
            resolved, through_procfs = "/", False
        pending.extend(link_text.split("/")[::-1])
    info = _read_only_agy_hook_stat(resolved, through_procfs)
    identity = {"links": links, "target": {"path": resolved, "file_type": stat.S_IFMT(info.st_mode)}}
    return identity, (info.st_dev, info.st_ino)


def _read_only_agy_hook_stat(path: str, through_procfs: bool) -> os.stat_result:
    """Stat a walked path; through a procfs link, the entry the kernel jumps to."""
    return os.stat(path) if through_procfs else os.lstat(path)


def _procfs_devices() -> frozenset[int]:
    """Return the device of every procfs mount, whose links are magic links.

    Without a readable mount table no link counts as a magic link, so a
    procfs link is walked by its text and fails closed where that is no path.
    """
    try:
        with open("/proc/self/mountinfo", encoding="utf-8", errors="surrogateescape") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return frozenset()
    devices = set()
    for line in lines:
        # Mount points escape their spaces, so " - " only separates the filesystem type.
        mount, _, filesystem = line.partition(" - ")
        fields = mount.split()
        if filesystem.split(" ", 1)[0] == "proc" and len(fields) > 2:
            major, _, minor = fields[2].partition(":")
            devices.add(os.makedev(int(major), int(minor)))
    return frozenset(devices)


def _read_only_agy_hook_digest(identity: dict[str, Any], inode: tuple[int, int]) -> str | None:
    """Hash the effective guard bytes when the observed target is a regular file."""
    target = identity["target"]
    if target["file_type"] != stat.S_IFREG:
        return None
    last_link = identity["links"][-1] if identity["links"] else None
    if last_link is not None and last_link["path"] == target["path"] and "target" in last_link:
        fd = _read_only_agy_hook_open_procfs_target(target["path"], inode)
    else:
        fd = os.open(Path(target["path"]), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != inode:
            raise _AgyHookChangedDuringSnapshot
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _read_only_agy_hook_open_procfs_target(path: str, inode: tuple[int, int]) -> int:
    """Open the regular file a procfs link names for reading, never what replaced it.

    The descriptor behind the link can change after the walk observed it, and
    following the link would then open that, a device for one. ``O_PATH``
    pins the entry without opening it, and only the observed regular file is
    reopened for reading through the pin.
    """
    pinned = os.open(path, os.O_PATH | os.O_CLOEXEC)
    try:
        info = os.fstat(pinned)
        if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != inode:
            raise _AgyHookChangedDuringSnapshot
        return os.open(f"/proc/self/fd/{pinned}", os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    finally:
        os.close(pinned)


def _read_only_task_record_snapshot(
    task_id: str,
    baseline: dict[str, tuple[str, str | None]] | None = None,
) -> tuple[dict[str, tuple[str, str | None]] | None, str | None]:
    """Fingerprint results of tasks already terminal when the review starts.

    A sibling task owns its live record and may finish during a review. Only
    changes to a pre-existing terminal result are attributable here. A new
    run_nonce means ``--force-new`` replaced the hot record, not that the old
    result was edited.
    """
    own_stem = _state_path(task_id).stem
    snapshot: dict[str, tuple[str, str | None]] = {}
    try:
        paths = (
            list(tasks_dir().glob("*.result"))
            if baseline is None
            else [tasks_dir() / Path(name).name for name in baseline]
        )
    except OSError as exc:
        return None, f"task record snapshot failed: {type(exc).__name__}: {exc}"
    for path in paths:
        if path.stem == own_stem:
            continue
        state = _read_state_json(path.with_suffix(".json"))
        if baseline is None and (state is None or state.get("status") not in _TERMINAL_STATUSES):
            continue
        name = f"batch_state/tasks/{path.name}"
        nonce = state.get("run_nonce") if state else None
        if baseline is not None and nonce != baseline[name][1]:
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            # The task may have been archived or reaped during the scan.
            continue
        snapshot[name] = (digest, nonce)
    return snapshot, None


# Harness-owned Entire residue under the checkout (ADR-018 capture). These paths
# are gitignored and appear in the read-only snapshot because the guard includes
# ignored files (#4840). Treating them as task mutations false-fails healthy
# read-only dispatches at repo root and inside dispatch worktrees (#6803).
# Keep this list precise: committed ``.entire/`` config (settings, allowlist,
# private-recall) must still fail the guard when a worker edits it.
# Force-added tracked files under these prefixes are NOT exempt: exemption
# requires an ignored/untracked porcelain status at snapshot time (#6803 r2).
_READ_ONLY_RUNTIME_TELEMETRY_PREFIXES = (
    ".entire/metadata",
    ".entire/logs",
    ".entire/tmp",
    ".entire/redactors/local",
)
_READ_ONLY_RUNTIME_TELEMETRY_FILES = frozenset({".entire/settings.local.json"})
# Gitignored-by-default dirs a worker's own tooling writes (#6860). Observed
# false-fails: ``.agent/sessions/*.json``, fleet-comms sqlite ``-shm/-wal``,
# ``.pytest_cache/``, ``.pytest_breadcrumbs/``. Siblings are the same class
# (harness/session/cache residue). Membership is load-bearing (#8516 AC-02):
# an ignored ``!!`` path escapes the mutation guard ONLY through this
# classification, or when it is ignored and full-matches the existing
# ``SITE_BUILD_OUTPUT_PATTERNS`` list (#11193). Task-authored leak targets
# like ``.cache/`` (#4840), root-level ``/*.py`` scratch, and ``/scratch/``
# deliberately stay OUT and now fail the task. Deploy-target dirs
# (``.claude``, ``.codex``, ``.gemini``,
# ``.cursor``, ``.agents``) are not in this set: they hold tracked,
# harness-executed content, so an untracked new file there (e.g.
# ``.claude/hooks/``) must still fail a read-only task in its own worktree.
# Tracked files under these names still fail via porcelain status.
_READ_ONLY_RUNTIME_STATE_DIR_NAMES = frozenset(
    {
        ".agent",
        ".antigravitycli",
        ".deploy-state",
        ".pytest_breadcrumbs",
        ".pytest_cache",
        ".runtime",
        ".ruff_cache",
        "__pycache__",
        "batch_state",
    }
)
_READ_ONLY_RUNTIME_STATE_SUFFIXES = (
    ".db-journal",
    ".db-shm",
    ".db-wal",
    ".sqlite-journal",
    ".sqlite-shm",
    ".sqlite-wal",
    ".sqlite3-journal",
    ".sqlite3-shm",
    ".sqlite3-wal",
)
_READ_ONLY_PACKAGE_BUILD_PREFIXES = (
    "packages/v4-runtime/build",
    "packages/v4-runtime/src/learn_ukrainian_v4_runtime.egg-info",
)
_READ_ONLY_UNTRACKED_OR_IGNORED_STATUSES = frozenset({"??", "!!"})
# Dispatch sandboxes live at ``.worktrees/dispatch/<agent>/<task>/`` (layout A).
# Concurrent ``git worktree add`` under that prefix must not false-fail a
# read-only task that is scanning the shared primary checkout (#6938).
_READ_ONLY_DISPATCH_SANDBOX_PREFIX = (".worktrees", "dispatch")
_READ_ONLY_DISPATCH_SANDBOX_ROOT_PARTS = 4  # .worktrees / dispatch / agent / task


def _normalize_read_only_relpath(path: str) -> str:
    """Normalize a checkout-relative path for read-only guard matching."""
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.rstrip("/")


def _is_read_only_runtime_telemetry_path(path: str) -> bool:
    """Return whether a path is harness Entire telemetry, not a task mutation."""
    normalized = _normalize_read_only_relpath(path)
    if normalized in _READ_ONLY_RUNTIME_TELEMETRY_FILES:
        return True
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in _READ_ONLY_RUNTIME_TELEMETRY_PREFIXES
    )


def _is_read_only_delegate_snapshot_sidecar_path(path: str) -> bool:
    """Return whether *path* is a delegate-owned read-only snapshot sidecar."""
    normalized = _normalize_read_only_relpath(path)
    if not normalized.endswith(".json"):
        return False
    parts = normalized.split("/")
    if len(parts) < 2:
        return False
    if not parts[-2].endswith(f"{_READ_ONLY_CHECKOUT_SNAPSHOT_SUFFIX}"):
        return False
    name = parts[-1]
    if name == _READ_ONLY_SNAPSHOT_DIGEST_NAME:
        return True
    return name.startswith("read_only_checkout_") and name.endswith(".json")


def _is_read_only_runtime_state_path(path: str) -> bool:
    """Return whether a path is harness/tooling runtime state, not repo content.

    Covers Entire telemetry (#6803) plus the gitignored runtime dirs and sqlite
    sidecars that false-failed successful read-only tasks (#6860). Since #8516
    AC-02 an ignored ``!!`` status alone does not escape the mutation guard.
    Task-authored ignored leaks outside this classification (the
    review-a3-api-ui ``/*.py`` + ``/scratch/`` scratch class; ``.cache/``
    residue from #4840/#7253) fail the task like any other mutation. The other
    narrow escape is an ignored path that full-matches the existing
    ``SITE_BUILD_OUTPUT_PATTERNS`` list (#11193), not ``!!`` by itself.
    """
    if _is_read_only_delegate_snapshot_sidecar_path(path):
        return True
    if _is_read_only_runtime_telemetry_path(path):
        return True
    normalized = _normalize_read_only_relpath(path)
    # The shared broker watcher can append while a review runs (#10025).
    # Exempt its log only; other ignored MCP files remain mutation targets.
    if normalized == ".mcp/servers/message-broker/watcher.log":
        return True
    # `pip`/setuptools can regenerate these Git-ignored package outputs while
    # a reviewer runs tests. They are build residue, not review edits (#9213).
    if _is_read_only_package_build_path(normalized):
        return True
    parts = tuple(part for part in normalized.split("/") if part and part != ".")
    if any(part in _READ_ONLY_RUNTIME_STATE_DIR_NAMES for part in parts):
        return True
    return any(normalized.endswith(suffix) for suffix in _READ_ONLY_RUNTIME_STATE_SUFFIXES)


def _is_read_only_package_build_path(path: str) -> bool:
    normalized = _normalize_read_only_relpath(path)
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/") for prefix in _READ_ONLY_PACKAGE_BUILD_PREFIXES
    )


def _read_only_dispatch_sandbox_root(path: str) -> str | None:
    """Return ``.worktrees/dispatch/<agent>/<task>`` when *path* is under one.

    Paths outside the dispatch sandbox layout (including other ``.worktrees/``
    entries) return ``None`` so the guard still sees them as ordinary mutations.
    """
    normalized = _normalize_read_only_relpath(path)
    parts = tuple(part for part in normalized.split("/") if part and part != ".")
    if len(parts) < _READ_ONLY_DISPATCH_SANDBOX_ROOT_PARTS:
        return None
    if parts[:2] != _READ_ONLY_DISPATCH_SANDBOX_PREFIX:
        return None
    return "/".join(parts[:_READ_ONLY_DISPATCH_SANDBOX_ROOT_PARTS])


def _read_only_dispatch_sandbox_roots(snapshot: dict[str, str]) -> frozenset[str]:
    """Collect dispatch sandbox roots visible in a read-only checkout snapshot."""
    return frozenset(root for path in snapshot if (root := _read_only_dispatch_sandbox_root(path)) is not None)


def _is_read_only_new_sibling_dispatch_sandbox_path(path: str, *, before_roots: frozenset[str]) -> bool:
    """Return whether *path* belongs to a sibling sandbox absent from *before*.

    Only newly appeared ``.worktrees/dispatch/<agent>/<task>/`` trees are
    exempt (#6938). A write under a sandbox root that already appeared in the
    pre-snapshot still counts as a mutation when the root checkout can see it.
    """
    root = _read_only_dispatch_sandbox_root(path)
    if root is None:
        return False
    return root not in before_roots


def _is_read_only_untracked_or_ignored_status(state: str | None) -> bool:
    """Return whether a porcelain status is ignored/untracked (not git-tracked).

    Absent entries are treated as non-tracked for the exemption gate: a clean
    tracked file is invisible in the snapshot until it mutates, and the
    post-mutation status then fails this check.
    """
    if state is None:
        return True
    return state[:2] in _READ_ONLY_UNTRACKED_OR_IGNORED_STATUSES


def _is_read_only_runtime_state_exemption(
    path: str,
    *,
    before_state: str | None,
    after_state: str | None,
) -> bool:
    """Exempt harness runtime state only when it is not tracked at snapshot time."""
    normalized = _normalize_read_only_relpath(path)
    if normalized == ".opencode" or normalized.startswith(".opencode/"):
        # Its install is in the baseline. Later writes, even cache-shaped
        # names inside dependencies, belong to the worker (#11347).
        return False
    if not _is_read_only_runtime_state_path(path):
        return False
    if _is_read_only_package_build_path(path):
        # The package exemption is for Git-ignored build products only. An
        # ordinary untracked scratch file under this tree is still a leak.
        return (
            before_state in (None, "!!")
            and after_state in (None, "!!")
            and (before_state == "!!" or after_state == "!!")
        )
    return _is_read_only_untracked_or_ignored_status(before_state) and _is_read_only_untracked_or_ignored_status(
        after_state
    )


def _is_read_only_ignored_status(state: str | None) -> bool:
    """Return whether a snapshot status is Git's ignored ``!!`` marker."""
    return state is not None and state[:2] == "!!"


def _is_read_only_ignored_mutation(*, before_state: str | None, after_state: str | None) -> bool:
    """Return whether a changed path is ignored in its observable final state.

    A deleted ignored file disappears from both porcelain snapshots, so its
    pre-snapshot ``!!`` marker is also sufficient to classify that delta as an
    ignored mutation. A path that becomes ordinary untracked ``??`` remains a
    real mutation and is intentionally not classified as ignored.
    """
    if after_state is not None:
        return _is_read_only_ignored_status(after_state)
    return _is_read_only_ignored_status(before_state)


def _read_only_ignored_mutation_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return changed ignored paths the guard deliberately tolerates as noise.

    Diagnostic companion to :func:`_read_only_mutation_paths` (#8516): an
    ignored ``!!`` status alone no longer exempts a path, so this list holds
    exactly the ignored deltas that were ALSO recognized as harness/runtime
    state — the build-noise class a read-only dispatch legitimately cannot
    own (``.pytest_cache/``, ``batch_state/``, ``.entire/`` telemetry, …).
    """
    before_roots = _read_only_dispatch_sandbox_roots(before)
    return sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
        and _is_read_only_ignored_mutation(
            before_state=before.get(path),
            after_state=after.get(path),
        )
        and _is_read_only_runtime_state_exemption(
            path,
            before_state=before.get(path),
            after_state=after.get(path),
        )
        and not _is_read_only_new_sibling_dispatch_sandbox_path(path, before_roots=before_roots)
    )


def _is_read_only_ignored_site_build_output(
    path: str,
    *,
    before_state: str | None,
    after_state: str | None,
) -> bool:
    """Exempt an ignored path that full-matches ``SITE_BUILD_OUTPUT_PATTERNS``.

    ``site/astro.config.mjs`` creates
    ``site/public/audio/pronunciation/manifest.json`` when it is absent, and
    ``.gitignore`` ignores that directory (#11193). The match calls the
    existing pattern list and does not add patterns. A tracked status on
    either side, including a force-added file, is not exempt. An ignored
    ``!!`` path outside the list is not exempt (#8516).
    """
    if not _is_read_only_ignored_mutation(before_state=before_state, after_state=after_state):
        return False
    # ``after`` is already ignored or absent. A tracked or force-added
    # ``before`` (`` M``, ``A ``) must still trip, even when ``after`` is ``!!``.
    if before_state is not None and not _is_read_only_ignored_status(before_state):
        return False
    # Imported at use so the supervisor's import closure stays within scripts.dispatcher and scripts.common.
    from scripts.fleet.regenerable_output import SITE_BUILD_OUTPUT_PATTERNS

    normalized = _normalize_read_only_relpath(path)
    return any(re.fullmatch(pattern, normalized) for pattern in SITE_BUILD_OUTPUT_PATTERNS)


def _read_only_mutation_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return exact paths whose observable Git state changed during a review.

    A changed path is exempt only when it is recognized harness/runtime noise
    (:func:`_is_read_only_runtime_state_exemption`: gitignored tooling residue
    such as ``.pytest_cache/`` or ``batch_state/``), a newly appeared
    sibling dispatch sandbox under ``.worktrees/dispatch/<agent>/<task>/``
    (#6938 defense in depth; since #7124 the snapshot itself already drops
    every ``.worktrees/`` path), or an ignored path that full-matches the
    existing ``SITE_BUILD_OUTPUT_PATTERNS`` list (#11193). Tracked paths,
    including ones that match that list, and force-added files still trip
    the guard.

    #8516 AC-02: an ignored ``!!`` status BY ITSELF no longer exempts a path.
    The review-a3-api-ui leak showed why: the agy worker wrote its scratch
    files at the checkout root and under ``scratch/``, where ``.gitignore``
    (``/*.py``, ``/scratch/``) marked them ``!!``, and the guard filed them
    as diagnostic-only "ignored mutations" while the task settled ``done``.
    Now any other new, modified, or deleted path — tracked, untracked, or
    ignored — fails the task and is named. Matching the site-build list does
    not widen that rule: the path must be ignored, and an ignored path
    outside the list still fails.
    """
    before_roots = _read_only_dispatch_sandbox_roots(before)
    return sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
        and not _is_read_only_runtime_state_exemption(
            path,
            before_state=before.get(path),
            after_state=after.get(path),
        )
        and not _is_read_only_new_sibling_dispatch_sandbox_path(path, before_roots=before_roots)
        and not _is_read_only_ignored_site_build_output(
            path,
            before_state=before.get(path),
            after_state=after.get(path),
        )
    )


class ReadOnlyGuard:
    """One read-only task's guard lifecycle, in the order ``delegate._run_worker`` used.

    :meth:`begin` mirrors delegate.py:12251-12269 and runs before the provider is
    built; :meth:`finish` mirrors delegate.py:12689-12741 and runs after the
    provider exited, whatever its outcome. The public causes are the ones
    delegate.py:13093-13135 published; the paths stay in the record fields.
    """

    def __init__(self, task_id: str, agent: str, model: str, cwd: Path) -> None:
        self.task_id, self.agent, self.model, self.cwd = task_id, agent, model, cwd
        # Only AGY executes the workspace guard file, so only AGY snapshots it (#10727).
        self.snapshot_options: dict[str, bool] = {"agy_hook": True} if agent == "agy" else {}
        self.pre: dict[str, str] | None = None
        self.records_pre: dict[str, tuple[str, str | None]] | None = None
        self.records_error: str | None = None
        self.snapshot_error: str | None = None

    def begin(self, hard_timeout: float) -> None:
        """Initialize the harness, then take the baseline; a ValueError refuses the provider."""
        if self.agent == "opencode":
            from scripts.agent_runtime.adapters.deepseek import initialize_opencode_dependencies

            # v2's ``opencode`` provider is delegate's ``deepseek`` route (cli.ALIASES).
            initialize_opencode_dependencies(
                self.cwd,
                agent="deepseek",
                model=self.model,
                timeout=min(hard_timeout, 120) if hard_timeout > 0 else 120,
            )
        if self.agent == "agy":
            _provision_agy_read_only_guard(self.cwd)
        self.pre, self.snapshot_error = _read_only_checkout_snapshot(self.cwd, **self.snapshot_options)
        self.records_pre, self.records_error = _read_only_task_record_snapshot(self.task_id)
        if self.snapshot_error is None:
            self.snapshot_error = self.records_error
        _write_read_only_snapshot_sidecar(self.task_id, "pre", self.pre)

    def finish(self) -> tuple[dict[str, Any], str | None, Path | None]:
        """Return the record fields, the public failure cause or None, and phases to discard."""
        post, post_error = _read_only_checkout_snapshot(self.cwd, **self.snapshot_options)
        records_post, records_error = _read_only_task_record_snapshot(self.task_id, self.records_pre)
        if self.records_error is None:
            self.records_error = records_error
        if post_error is None:
            post_error = records_error
        _write_read_only_snapshot_sidecar(self.task_id, "post", post)
        if self.snapshot_error is None and post_error is not None:
            self.snapshot_error = post_error
        mutations: list[str] = []
        ignored: list[str] = []
        if self.pre is not None and post is not None:
            ignored = _read_only_ignored_mutation_paths(self.pre, post)
            mutations = _read_only_mutation_paths(self.pre, post)
        if self.records_pre is not None and records_post is not None:
            mutations = sorted(
                set(mutations)
                | {path for path, fingerprint in records_post.items() if fingerprint[0] != self.records_pre[path][0]}
            )
        fields: dict[str, Any] = {
            "read_only_checkout_snapshot_error": self.snapshot_error,
            "read_only_ignored_mutation_paths": ignored,
            "read_only_mutation_paths": mutations,
        }
        discard = None
        if read_only_snapshot_keep_full(mutations, self.snapshot_error):
            fields["read_only_snapshot_retention"] = _READ_ONLY_SNAPSHOT_RETENTION_FULL
        else:
            discard = _read_only_snapshot_dir_for(self.task_id)
            stage_read_only_snapshot_digest(discard, self.pre, post)
            fields["read_only_snapshot_retention"] = _READ_ONLY_SNAPSHOT_RETENTION_DIGEST
        causes = []
        if mutations:
            causes.append(f"read_only_checkout_mutation, count {len(mutations)}")
        if self.records_error:
            causes.append("task_records_snapshot_failed")
        elif _read_only_snapshot_error_fails_closed(self.snapshot_error):
            causes.append("read_only_checkout_snapshot_failed")
        return fields, "; ".join(causes) or None, discard
