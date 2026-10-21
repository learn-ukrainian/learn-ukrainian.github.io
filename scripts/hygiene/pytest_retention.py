"""Delete inactive pytest scratch without an ownership record (#11297).

Within the managed pytest namespaces only (``pytest-runs/runs`` and the
legacy ``pytest-runs/task-scratch``), a run folder is deleted once its newest
change anywhere inside (write or inode change, so freshly extracted files
with old mtimes stay young) is more than two hours old and no live process
holds it through its working directory, an open descriptor, a mapped file,
its command line or its environment. Ownership metadata, completion state,
retention counts and the seven-day quarantine play no part (the operator's
retention decision for #11297); a held run lock still preserves. A process
that cannot be inspected makes liveness unknown, and unknown preserves.

Deletion reuses the sweep's primitives: an atomic no-replace rename into a
locked holding directory, a holder and tree-fingerprint recheck of both the
original and the renamed path, then the descriptor-safe common remover. A
failed recheck renames the folder back; a crash leaves it in an unlocked
holding directory, which the next run's recovery returns to its name.
"""

from __future__ import annotations

import errno
import fcntl
import os
import stat
from collections import Counter
from collections.abc import Iterable
from contextlib import ExitStack, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.common import task_scratch as ownership
from scripts.common.pytest_scratch import NAMESPACE, RUNS_DIRNAME
from scripts.common.scratch import ScratchScanRootError, scratch_scan_roots
from scripts.hygiene import tmp_sweep as sweep
from scripts.hygiene.tmp_sweep_ledger import Ledger
from scripts.orchestration.tmp_leak_sweep import _process_state, _process_vanished

INACTIVE_S = 2 * 3600
PROC_ROOT = Path("/proc")


def _open_private(path: Path, stack: ExitStack, *, private: bool = True) -> int:
    """Open every component without following aliases, then require a private owner."""
    fd = os.open(path.anchor, sweep._DIR_FLAGS)
    stack.callback(os.close, fd)
    for part in path.parts[1:]:
        fd = os.open(part, sweep._DIR_FLAGS, dir_fd=fd)
        stack.callback(os.close, fd)
    info = os.fstat(fd)
    if private and (info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise ValueError("namespace_untrusted")
    return fd


def _same(path: Path, fd: int) -> bool:
    try:
        return path.absolute() == path.resolve(strict=True) and os.path.samestat(path.lstat(), os.fstat(fd))
    except OSError:
        return False


@dataclass
class Holders:
    """One pass over every process: path references and raw argv/environment, never emitted.

    ``complete`` is False when any live process could not be fully read.
    ``unreadable`` counts those processes for the privacy-safe report.
    """

    paths: list[tuple[int, str, str]] = field(default_factory=list)
    texts: list[tuple[int, str, bytes]] = field(default_factory=list)
    cwds: dict[int, str] = field(default_factory=dict)
    complete: bool = True
    unreadable: int = 0

    def holding(self, paths: Iterable[Path]) -> tuple[list[int], list[str]]:
        """PIDs and channels that reach any of ``paths`` or a path below it."""
        found: set[tuple[int, str]] = set()
        for path in paths:
            needle = str(path)
            prefix = needle + "/"
            encoded = os.fsencode(needle)
            parent, name = str(path.parent), os.fsencode(path.name)
            for pid, channel, target in self.paths:
                if target == needle or target.startswith(prefix):
                    found.add((pid, channel))
            for pid, channel, blob in self.texts:
                # A relative argument or value counts when the process sits in the parent.
                if encoded in blob or (self.cwds.get(pid) == parent and _names_relative(blob, name)):
                    found.add((pid, channel))
        return sorted({pid for pid, _ in found}), sorted({channel for _, channel in found})


def _names_relative(blob: bytes, name: bytes) -> bool:
    """True when an argument or ``VAR=value`` value is ``name``, ``./name`` or a path below it."""
    for token in blob.split(b"\0"):
        for value in {token, token.partition(b"=")[2]}:
            value = value.removeprefix(b"./")
            if value == name or value.startswith(name + b"/"):
                return True
    return False


def holder_snapshot(own_fds: frozenset[int] = frozenset()) -> Holders:
    """Read cwd, descriptors, maps, argv and environment of every process.

    The caller is inspected like any other process, except for the
    descriptors in ``own_fds``: the sweep's own inspection handles (a held
    run lock) are not external holders, while its working directory,
    arguments, environment and every other descriptor still count. Zombies
    and processes that exit during the scan hold nothing; any other read
    failure leaves the snapshot incomplete.
    """
    holders = Holders()
    try:
        entries = [name for name in os.listdir(PROC_ROOT) if name.isdigit()]
    except OSError:
        holders.complete = False
        return holders
    me = os.getpid()
    for name in entries:
        entry = PROC_ROOT / name
        pid = int(name)
        state = _process_state(entry)
        if state in {"Z", "X"}:
            continue
        found: list[tuple[int, str, str]] = []
        texts: list[tuple[int, str, bytes]] = []
        try:
            if state is None:
                raise OSError(errno.EIO, "unknown process state")
            cwd = os.readlink(entry / "cwd")
            found.append((pid, "cwd", cwd))
            for fd in os.listdir(entry / "fd"):
                if pid == me and int(fd) in own_fds:
                    continue
                with suppress(FileNotFoundError):  # closed during the scan
                    found.append((pid, "fd", os.readlink(entry / "fd" / fd)))
            for line in (entry / "maps").read_bytes().splitlines():
                fields = line.split(maxsplit=5)
                if len(fields) == 6:
                    found.append((pid, "maps", os.fsdecode(fields[5])))
            texts.append((pid, "argv", (entry / "cmdline").read_bytes()))
            texts.append((pid, "environ", (entry / "environ").read_bytes()))
        except (OSError, ValueError):
            if not _process_vanished(entry):
                holders.complete = False
                holders.unreadable += 1
            continue
        holders.cwds[pid] = cwd
        holders.paths.extend((p, channel, target.removesuffix(" (deleted)")) for p, channel, target in found)
        holders.texts.extend(texts)
    return holders


def _lock(run_fd: int) -> tuple[int | None, str | None]:
    """Take the run's lock when it has a usable one; a missing or unusable lock proves nothing."""
    try:
        info = os.stat(ownership.LOCK_FILENAME, dir_fd=run_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None, None
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
        return None, None
    try:
        lock = os.open(
            ownership.LOCK_FILENAME, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=run_fd
        )
    except FileNotFoundError:
        return None, None
    except OSError:
        return None, "lock_unknown"
    try:
        if not os.path.samestat(os.fstat(lock), info):
            raise OSError(errno.ESTALE, "lock replaced while opening")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        os.close(lock)
        return None, "in_use" if isinstance(error, BlockingIOError) else "lock_unknown"
    return lock, None


@dataclass
class Candidate:
    name: str
    namespace: Path
    ns_fd: int
    row: dict[str, Any]
    identity: tuple[int, int]
    before: dict[str, tuple[Any, ...]] | None = None
    lock: int | None = None


def _classify(
    name: str, namespace: Path, ns_fd: int, *, holders: Holders, worktrees: set[Path] | None, now: float,
    apply: bool, stack: ExitStack,
) -> Candidate:
    """Decide one run folder; on apply also keep its lock and pre-rename fingerprint."""
    path = namespace / name
    row = sweep._bare_row(name, "symlink_or_not_directory", kind="other")
    info = os.stat(name, dir_fd=ns_fd, follow_symlinks=False)
    candidate = Candidate(name, namespace, ns_fd, row, (info.st_dev, info.st_ino))
    if not stat.S_ISDIR(info.st_mode):
        return candidate
    row.update(kind="directory", identity=[info.st_dev, info.st_ino, info.st_uid])
    run_fd = os.open(name, sweep._DIR_FLAGS, dir_fd=ns_fd)
    try:
        if not os.path.samestat(os.fstat(run_fd), info):
            row["reason"] = "identity_changed"
            return candidate
        candidate.lock, reason = _lock(run_fd)
    finally:
        os.close(run_fd)
    if candidate.lock is not None:
        if apply:  # held until the folder is deleted or returned
            stack.callback(os.close, candidate.lock)
        else:  # a dry run only observes the lock
            os.close(candidate.lock)
            candidate.lock = None
    if reason:
        row["reason"] = reason
        return candidate
    # Fingerprint first: a write after it shows at the post-rename comparison,
    # a write before it is seen by the age scan below.
    candidate.before = sweep.tree_fingerprint(path) if apply else None
    row["bytes"], _newest, changed, problem = sweep.tree_facts(path)
    row["newest_change"] = changed
    row["idle_hours"] = round(max(0.0, now - changed) / 3600, 2)
    pids, channels = holders.holding([path])
    row.update(live_pids=pids, holders=channels)
    if problem:
        row["reason"] = problem
    elif apply and candidate.before is None:
        row["reason"] = "tree_unknown"
    elif now - changed <= INACTIVE_S:
        row["reason"] = "too_young"
    elif pids:
        row["reason"] = "live_process"
    elif not holders.complete:
        row["reason"] = "liveness_unknown"
    elif worktrees is None or any(w == path or w in path.parents or path in w.parents for w in worktrees):
        row["reason"] = "git_registration_unknown" if worktrees is None else "registered_worktree"
    else:
        row.update(decision="would_delete", reason="inactive_pytest_scratch")
    return candidate


def _return(candidate: Candidate, quarantine: sweep.Quarantine, reason: str) -> int:
    """Rename a held folder back under its own name; an occupied name keeps it held for recovery."""
    try:
        sweep.rename_noreplace(quarantine.fd, candidate.name, candidate.ns_fd, candidate.name)
    except OSError as error:
        candidate.row.update(decision="preserve", reason="restore_blocked", found=reason, error=sweep._errno_name(error))
        return 1
    sweep._sync_rename(quarantine.fd, candidate.ns_fd)
    candidate.row.update(decision="preserve", reason=reason)
    return 0


def _recheck(candidate: Candidate, quarantine: sweep.Quarantine, holders: Holders) -> str | None:
    """Re-prove a held folder: same inode, no holder of either path, an unchanged tree."""
    held = quarantine.path / candidate.name
    try:
        info = os.stat(candidate.name, dir_fd=quarantine.fd, follow_symlinks=False)
    except OSError:
        return "identity_changed"
    if (info.st_dev, info.st_ino) != candidate.identity:
        return "identity_changed"
    if not _same(candidate.namespace, candidate.ns_fd) or not _same(quarantine.path, quarantine.fd):
        return "identity_changed"
    pids, channels = holders.holding([candidate.namespace / candidate.name, held])
    if pids:
        candidate.row.update(live_pids=pids, holders=channels)
        return "live_process"
    if not holders.complete:
        return "liveness_unknown"
    return None if sweep.tree_fingerprint(held) == candidate.before else "recent_write"


def _delete(candidates: list[Candidate], namespace: Path, ns_fd: int, *, repo_root: Path) -> int:
    """Rename every proven folder aside, recheck once for all of them, then delete or return each."""
    errors = 0
    quarantine = sweep.open_quarantine(namespace, ns_fd)
    try:
        held = []
        for candidate in candidates:
            row = candidate.row
            try:
                info = os.stat(candidate.name, dir_fd=ns_fd, follow_symlinks=False)
            except OSError:
                info = None
            if info is None or (info.st_dev, info.st_ino) != candidate.identity or not _same(namespace, ns_fd):
                row.update(decision="preserve", reason="identity_changed")
                continue
            try:
                sweep.rename_noreplace(ns_fd, candidate.name, quarantine.fd, candidate.name)
            except OSError as error:
                row.update(decision="preserve", reason="rename_refused", error=sweep._errno_name(error))
                errors += 1
                continue
            sweep._sync_rename(ns_fd, quarantine.fd)
            held.append(candidate)
        # Nothing can newly reach a held folder by its old name. Our run locks are inspection handles.
        holders = holder_snapshot(frozenset(c.lock for c in held if c.lock is not None))
        for candidate in held:
            reason = _recheck(candidate, quarantine, holders)
            if reason:
                errors += _return(candidate, quarantine, reason)
                continue
            try:
                sweep.reap_attributed_temp(
                    quarantine.path / candidate.name, repo_root=repo_root, temp_root=quarantine.path,
                    expected_dev=candidate.identity[0], expected_ino=candidate.identity[1],
                )
                if os.path.lexists(quarantine.path / candidate.name):
                    raise OSError(errno.ENOTEMPTY, "common reaper left residue")
            except (OSError, ValueError, ownership.TaskScratchError) as error:
                detail = sweep._errno_name(error) if isinstance(error, OSError) else type(error).__name__
                # Whatever the remover left goes back under its own name.
                blocked = os.path.lexists(quarantine.path / candidate.name) and _return(
                    candidate, quarantine, "delete_refused"
                )
                errors += 1 + blocked
                if not blocked:
                    candidate.row.update(decision="preserve", reason="delete_refused", error=detail)
                continue
            sweep.sync_directory(quarantine.fd)
            candidate.row.update(decision="deleted")
    finally:
        sweep.close_quarantine(quarantine, ns_fd)
    return errors


def _namespace(
    namespaces: tuple[Path, ...], *, apply: bool, ledger: Ledger, run_id: str, task_root: Path,
    quarantine_s: float, repo_root: Path,
) -> tuple[list[dict[str, Any]], int, Holders | None]:
    rows: list[dict[str, Any]] = []
    errors = 0
    holders = None
    with ExitStack() as stack:
        opened = []
        for namespace in namespaces:
            try:
                ns_fd = _open_private(namespace, stack)
            except FileNotFoundError:
                continue
            except (OSError, ValueError):
                errors += 1
                rows.append(sweep._bare_row("pytest-runs", "namespace_untrusted"))
                continue
            if ledger.directory == namespace or namespace in ledger.directory.parents:
                raise ValueError("ledger_inside_pytest_namespace")
            # Entries an earlier policy quarantined keep their recorded recovery and purge path.
            entries, _malformed = ledger.entries()
            local = {key: entry for key, entry in entries.items() if entry.original.parent == namespace}
            recovered, step_errors = sweep.reconcile_ledger(local, ledger, run_id, apply=apply)
            errors += step_errors
            rows.extend(recovered)
            if apply:
                entries, _malformed = ledger.entries()
                local = {key: entry for key, entry in entries.items() if entry.original.parent == namespace}
            known = frozenset(entry.location for entry in local.values() if entry.state in sweep.HELD_STATES)
            recovered, _restored, step_errors = sweep.recover_quarantines(namespace, ns_fd, apply=apply, known=known)
            errors += step_errors
            rows.extend(recovered)
            purged, step_errors = sweep.purge_quarantine(
                local, ledger, run_id, now=sweep.time.time(), quarantine_s=quarantine_s,
                task_root=task_root, repo_root=repo_root, apply=apply,
            )
            errors += step_errors
            rows.extend(purged)
            opened.append((namespace, ns_fd))
        if not opened:
            return rows, errors, holders
        holders = holder_snapshot()
        worktrees = sweep.registered_worktrees(repo_root)
        for namespace, ns_fd in opened:
            eligible = []
            for name in sorted(os.listdir(ns_fd)):
                if name.startswith(sweep.QUARANTINE_PREFIX):
                    continue
                try:
                    candidate = _classify(
                        name, namespace, ns_fd, holders=holders, worktrees=worktrees, now=sweep.time.time(),
                        apply=apply, stack=stack,
                    )
                except OSError as error:
                    errors += 1
                    rows.append(sweep._bare_row(name, "scan_error", error=sweep._errno_name(error)))
                    continue
                rows.append(candidate.row)
                if apply and candidate.row["decision"] == "would_delete":
                    eligible.append(candidate)
            if eligible:
                errors += _delete(eligible, namespace, ns_fd, repo_root=repo_root)
    return rows, errors, holders


def sweep_pytest_runs(
    *, apply: bool, ledger: Ledger, run_id: str, task_root: Path, quarantine_s: float, repo_root: Path,
) -> dict[str, Any]:
    """Sweep the dedicated pytest namespaces, never the general managed scratch tree."""
    rows = []
    errors = 0
    unreadable = 0
    complete = True
    try:
        roots = set(scratch_scan_roots())
    except ScratchScanRootError:
        # The general temp sweep may already have applied. Keep its report and
        # fail this confined scan closed without falling back to host roots.
        roots = set()
        errors += 1
        rows.append(sweep._bare_row("pytest-runs", "scan_root_invalid"))
    for root in sorted(roots):
        namespaces = tuple(root / NAMESPACE / name for name in (RUNS_DIRNAME, ownership.NAMESPACE_DIRNAME))
        try:
            # Legacy roots outside the two namespaces stay visible and untouched.
            with ExitStack() as stack:
                root_fd = _open_private(root, stack, private=False)
                for name in sorted(os.listdir(root_fd)):
                    if name.startswith("pytest-") and name != NAMESPACE:
                        size, _newest, _changed, _problem = sweep.tree_facts(root / name)
                        rows.append(sweep._bare_row(name, "legacy_ownership_unknown", bytes=size))
            found, step_errors, holders = _namespace(
                namespaces, apply=apply, ledger=ledger, run_id=run_id,
                task_root=task_root, quarantine_s=quarantine_s, repo_root=repo_root,
            )
            rows.extend(found)
            errors += step_errors
            if holders is not None:
                complete = complete and holders.complete
                unreadable = max(unreadable, holders.unreadable)
        except FileNotFoundError:
            continue
        except (OSError, ValueError):
            errors += 1
            rows.append(sweep._bare_row("pytest-runs", "namespace_untrusted"))
    held = [
        entry for entry in ledger.entries()[0].values()
        if entry.state in sweep.HELD_STATES
        and entry.original.parent in {
            root / NAMESPACE / name for root in roots for name in (RUNS_DIRNAME, ownership.NAMESPACE_DIRNAME)
        }
    ]

    def total(decision: str) -> int:
        return sum(row["bytes"] or 0 for row in rows if row["decision"] == decision)

    return {
        "inactive_hours": INACTIVE_S / 3600, "rows": rows, "errors": errors,
        "liveness_complete": complete, "liveness_unreadable_processes": unreadable,
        "runs": len(rows), "bytes": sum(row["bytes"] or 0 for row in rows),
        "by_reason": dict(Counter(row["reason"] for row in rows)),
        "by_decision": dict(Counter(row["decision"] for row in rows)),
        "would_delete_entries": sum(row["decision"] == "would_delete" for row in rows),
        "would_delete_bytes": total("would_delete"),
        "deleted_entries": sum(row["decision"] == "deleted" for row in rows),
        "deleted_bytes": total("deleted"),
        "protected_bytes": total("preserve"),
        "remaining_runs": sum(row["decision"] in {"preserve", "would_delete"} for row in rows),
        "remaining_bytes": total("preserve") + total("would_delete"),
        "quarantine_held_entries": len(held),
        "quarantine_held_bytes": sum(entry.intent.get("allocated_bytes") or 0 for entry in held),
        "purged_entries": sum(row["decision"] == "purged" for row in rows),
        "purged_bytes": total("purged"),
    }
