"""Delete abandoned pytest scratch (#11297, #11409; DISK-1109).

Within the managed pytest namespaces only (``pytest-runs/runs`` and the
legacy ``pytest-runs/task-scratch``), a run folder is abandoned, and deleted,
when its lease owner is provably dead and nothing inside it has changed
(write or inode change) for two hours. The owner is dead when the lease names
this run (directory identity, invocation id and uid) and either records an
earlier kernel boot, or records this boot and the recorded pid is absent or
now reports a different start time (the number was reused). The run's lease
lock must also be acquired exclusively. The owner holds it shared for its
lifetime, and so do the pytest processes that work inside the run (xdist
workers, nested sessions), so a run whose owner was killed is kept while any
of them lives. A folder with no lease, or a malformed one, records no owner:
it is the residue of an interrupted removal (the lease is written before
anything else exists) and goes once idle, when its lock (if any) is free. An
unreadable lease, a parsed lease without its lock, a live or unknown owner, a
mount or a foreign-owned node inside, an unreadable tree or a registered
worktree keeps the folder. With ``--apply``, a directory of an abandoned run
that its owner cannot list (a test can leave mode 000) gets owner rwx back,
and the run is kept in that sweep; the change makes it young, so a later sweep
judges its whole tree.

No snapshot of other processes is taken: on this host an unprivileged sweep
can never read every process, so requiring one kept every run (machinery
#30, #57). The contents of a run are pytest's own scratch, so checkouts,
hard links (virtual environments) and sockets inside it do not keep it.

Deletion reuses the sweep's primitives: an atomic no-replace rename into a
locked holding directory, a recheck that the renamed folder is the same
inode with an unchanged tree fingerprint, then the descriptor-safe common
remover. A failed recheck renames the folder back; a crash leaves it in an
unlocked holding directory, which the next run's recovery returns to its name.
"""

from __future__ import annotations

import errno
import fcntl
import os
import stat
from collections import Counter
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.common import task_scratch as ownership
from scripts.common.pytest_scratch import NAMESPACE, RUNS_DIRNAME
from scripts.common.scratch import ScratchScanRootError, scratch_scan_roots
from scripts.hygiene import tmp_sweep as sweep
from scripts.hygiene.tmp_sweep_ledger import Ledger

INACTIVE_S = 2 * 3600
LARGEST_PRESERVED_RUNS = 10
PROC_ROOT = Path("/proc")
_DESCRIPTOR_ERRORS = {errno.EMFILE, errno.ENFILE}


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
    except OSError as error:
        return None, "descriptor_exhausted" if error.errno in _DESCRIPTOR_ERRORS else "lock_unknown"
    try:
        if not os.path.samestat(os.fstat(lock), info):
            raise OSError(errno.ESTALE, "lock replaced while opening")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        os.close(lock)
        if error.errno in _DESCRIPTOR_ERRORS:
            return None, "descriptor_exhausted"
        return None, "in_use" if isinstance(error, BlockingIOError) else "lock_unknown"
    return lock, None


def _read_lease(run_fd: int) -> tuple[dict[str, Any] | None, str | None]:
    """Read ``lease.json`` relative to the run: ``(lease, error)``.

    A missing lease records no owner. A lease that exists but cannot be read as
    a regular, owner-owned file of bounded size is unknown and preserves. A
    malformed lease, including one the parser fails on outright, also records
    no owner but is not an I/O failure, so the lock and idle time decide like
    an unleased run.
    """
    try:
        info = os.stat(ownership.LEASE_FILENAME, dir_fd=run_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None, None
    except OSError:
        return None, "lease_unreadable"
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_size > ownership.LEASE_MAX_BYTES:
        return None, "lease_unreadable"
    try:
        fd = os.open(ownership.LEASE_FILENAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=run_fd)
    except OSError:
        return None, "lease_unreadable"
    try:
        if not os.path.samestat(os.fstat(fd), info):
            return None, "lease_unreadable"
        data = bytearray()
        while chunk := os.read(fd, 65536):
            data += chunk
            if len(data) > ownership.LEASE_MAX_BYTES:
                return None, "lease_unreadable"
    except OSError:
        return None, "lease_unreadable"
    finally:
        os.close(fd)
    try:
        return ownership.parse_lease(bytes(data)), None
    except Exception:  # any parser failure, e.g. RecursionError, is a malformed lease
        return None, None


def _pid_present(pid: int) -> bool | None:
    """Whether ``/proc/<pid>`` exists; ``None`` when the probe itself fails."""
    if pid <= 0:
        return False
    try:
        (PROC_ROOT / str(pid)).lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return None
    return True


def _process_start_time(pid: int) -> int | None:
    """Field 22 of ``/proc/<pid>/stat`` from ``PROC_ROOT``; ``None`` when unreadable."""
    try:
        blob = (PROC_ROOT / str(pid) / "stat").read_bytes()
    except OSError:
        return None
    _, _, tail = blob.rpartition(b")")
    fields = tail.split()
    if len(fields) <= 19:
        return None
    try:
        return int(fields[19])
    except ValueError:
        return None


def _owner_status(lease: dict[str, Any], boot_id: str | None) -> str:
    """Classify the recorded owner: ``owner_dead``, ``owner_alive`` or ``owner_liveness_unknown``.

    An earlier kernel boot proves the owner dead. On this boot the recorded
    pid must be absent, or report a start time other than the recorded one.
    A missing boot id, start time or process table is unknown, never dead.
    """
    owner = lease["owner"]
    recorded_boot = owner.get("boot_id")
    if boot_id is None or recorded_boot is None:
        return "owner_liveness_unknown"
    if recorded_boot != boot_id:
        return "owner_dead"
    if not PROC_ROOT.is_dir():
        return "owner_liveness_unknown"
    pid = int(owner["pid"])
    present = _pid_present(pid)
    if present is None:
        return "owner_liveness_unknown"
    if not present:
        return "owner_dead"
    recorded_start = owner.get("start_time")
    if recorded_start is None:
        return "owner_liveness_unknown"
    current = _process_start_time(pid)
    if current is None:
        return "owner_liveness_unknown"
    return "owner_alive" if current == recorded_start else "owner_dead"


@dataclass
class Candidate:
    name: str
    namespace: Path
    ns_fd: int
    row: dict[str, Any]
    identity: tuple[int, int]
    before: dict[str, tuple[Any, ...]] | None = None
    lock: int | None = None
    locked: bool = False
    lease: dict[str, Any] | None = None
    lease_error: str | None = None


def _names_run(lease: dict[str, Any], candidate: Candidate) -> bool:
    """Whether the lease records this run: its directory identity, invocation id and owner uid.

    A lease copied from another run names that run's owner, so it proves
    nothing about this one; a missing field proves nothing either.
    """
    directory = lease.get("dir") or {}
    dev, ino, uid = candidate.row["identity"]
    return (
        (directory.get("dev"), directory.get("ino")) == (dev, ino)
        and lease.get("invocation_id") == candidate.name
        and lease.get("uid") == uid == os.geteuid()
    )


def _abandonment(candidate: Candidate, *, boot_id: str | None) -> str | None:
    """Why the owner evidence keeps the run, or ``None`` when it is abandoned.

    A run with a lease must have had its lock acquired exclusively, and the
    lease must name this run and prove its owner dead. A missing or malformed
    lease records no owner: the lock, when present, must be free, and only the
    idle time decides.
    """
    if candidate.lease_error:
        return candidate.lease_error
    if candidate.lease is None:
        return None
    if not candidate.locked:
        return "lock_missing"
    if not _names_run(candidate.lease, candidate):
        return "owner_liveness_unknown"
    status = _owner_status(candidate.lease, boot_id)
    if status == "owner_dead":
        return None
    return "live_owner" if status == "owner_alive" else status


def _unlock_owned_dirs(dir_fd: int, path: Path, mounts: frozenset[str]) -> int:
    """Give owner rwx to each of our directories below ``dir_fd`` that the owner cannot list or enter.

    A test can leave such a directory (mode 000), which no scan can see into, so
    the run could never be judged. This runs only in apply mode, on a run whose
    owner is proven gone and whose lock the sweep holds. The repair changes each
    directory's ctime, and the run is kept in this sweep, so a later sweep judges
    its whole tree from that change on. It never follows a symlink, crosses a device or touches a mount
    point. Returns how many directories it repaired.
    """
    listable = stat.S_IRUSR | stat.S_IXUSR
    repaired = 0
    device = os.fstat(dir_fd).st_dev
    with os.scandir(dir_fd) as entries:
        children = [(entry.name, entry.stat(follow_symlinks=False)) for entry in entries]
    for name, info in children:
        if not stat.S_ISDIR(info.st_mode) or info.st_dev != device or str(path / name) in mounts:
            continue
        if info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) & listable != listable:
            os.chmod(name, stat.S_IMODE(info.st_mode) | stat.S_IRWXU, dir_fd=dir_fd, follow_symlinks=False)
            repaired += 1
        try:
            child = os.open(name, sweep._DIR_FLAGS, dir_fd=dir_fd)
        except PermissionError:
            continue  # not ours to repair; the tree scan reports it
        try:
            if os.path.samestat(os.fstat(child), info):
                repaired += _unlock_owned_dirs(child, path / name, mounts)
        finally:
            os.close(child)
    return repaired


def _classify(
    name: str, namespace: Path, ns_fd: int, *, worktrees: set[Path] | None, now: float,
    apply: bool, stack: ExitStack,
) -> Candidate:
    """Decide one run folder; transfer only eligible apply locks to the deletion scope."""
    path = namespace / name
    boot_id = ownership.current_boot_id()
    row = sweep._bare_row(name, "symlink_or_not_directory", kind="other", bytes=None)
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
        candidate.locked = candidate.lock is not None
        candidate.lease, candidate.lease_error = _read_lease(run_fd)
        mounts = sweep.mount_points()
        if apply and not reason and mounts is not None and _abandonment(candidate, boot_id=boot_id) is None:
            row["permissions_repaired"] = _unlock_owned_dirs(run_fd, path, mounts)
    finally:
        os.close(run_fd)
    with ExitStack() as inspection:
        if candidate.lock is not None:
            inspection.callback(os.close, candidate.lock)
            if not apply:  # a dry run only observes the lock
                inspection.close()
                candidate.lock = None
        if reason:
            row["reason"] = reason
            return candidate
        # Fingerprint first: a write after it shows at the post-rename comparison,
        # a write before it is seen by the age scan below.
        candidate.before = sweep.tree_fingerprint(path) if apply else None
        owner_reason = _abandonment(candidate, boot_id=boot_id)
        row["bytes"], _newest, changed, problem = sweep.tree_facts(path, run_contents=True)
        row["newest_change"] = changed
        row["idle_hours"] = round(max(0.0, now - changed) / 3600, 2)
        if problem:
            row["reason"] = problem
            row["bytes"] = None
        elif apply and candidate.before is None:
            row["reason"] = "tree_unknown"
        elif row.get("permissions_repaired"):
            # What the repair uncovered is judged by a later sweep, from this change on.
            row["reason"] = "permissions_repaired"
        elif now - changed <= INACTIVE_S:
            row["reason"] = "too_young"
        elif owner_reason:
            row["reason"] = owner_reason
        elif worktrees is None or any(w == path or w in path.parents or path in w.parents for w in worktrees):
            row["reason"] = "git_registration_unknown" if worktrees is None else "registered_worktree"
        else:
            row.update(decision="would_delete", reason="inactive_pytest_scratch")
        if apply and row["decision"] == "would_delete":
            # Transfer only eligible locks; retained runs need no inspection handles.
            stack.enter_context(inspection.pop_all())
        else:
            candidate.lock = None
        return candidate


def _return(candidate: Candidate, quarantine: sweep.Quarantine, reason: str) -> int:
    """Rename a held folder back under its own name; an occupied name keeps it held for recovery."""
    try:
        sweep.rename_noreplace(quarantine.fd, candidate.name, candidate.ns_fd, candidate.name)
    except OSError as error:
        candidate.row.update(decision="preserve", reason="restore_blocked", found=reason,
                             error=sweep._errno_name(error), bytes=None)
        return 1
    sweep._sync_rename(quarantine.fd, candidate.ns_fd)
    candidate.row.update(decision="preserve", reason=reason, bytes=None)
    return 0


def _recheck(candidate: Candidate, quarantine: sweep.Quarantine) -> str | None:
    """Re-prove a held folder: the same inode in the same directories, with an unchanged tree."""
    held = quarantine.path / candidate.name
    try:
        info = os.stat(candidate.name, dir_fd=quarantine.fd, follow_symlinks=False)
    except OSError:
        return "identity_changed"
    if (info.st_dev, info.st_ino) != candidate.identity:
        return "identity_changed"
    if not _same(candidate.namespace, candidate.ns_fd) or not _same(quarantine.path, quarantine.fd):
        return "identity_changed"
    return None if sweep.tree_fingerprint(held) == candidate.before else "recent_write"


def _delete(candidate: Candidate, namespace: Path, ns_fd: int, *, repo_root: Path) -> int:
    """Rename a proven folder aside, recheck it, then delete it or return it."""
    row = candidate.row
    try:
        info = os.stat(candidate.name, dir_fd=ns_fd, follow_symlinks=False)
    except OSError:
        info = None
    if info is None or (info.st_dev, info.st_ino) != candidate.identity or not _same(namespace, ns_fd):
        row.update(decision="preserve", reason="identity_changed", bytes=None)
        return 0
    quarantine = sweep.open_quarantine(namespace, ns_fd)
    try:
        try:
            sweep.rename_noreplace(ns_fd, candidate.name, quarantine.fd, candidate.name)
        except OSError as error:
            row.update(decision="preserve", reason="rename_refused", error=sweep._errno_name(error), bytes=None)
            return 1
        sweep._sync_rename(ns_fd, quarantine.fd)
        reason = _recheck(candidate, quarantine)
        if reason:
            return _return(candidate, quarantine, reason)
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
            if not blocked:
                row.update(decision="preserve", reason="delete_refused", error=detail, bytes=None)
            return 1 + blocked
        sweep.sync_directory(quarantine.fd)
        row.update(decision="deleted")
        return 0
    finally:
        sweep.close_quarantine(quarantine, ns_fd)


def _namespace(
    namespaces: tuple[Path, ...], *, apply: bool, ledger: Ledger, run_id: str, task_root: Path,
    quarantine_s: float, repo_root: Path,
) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    errors = 0
    with ExitStack() as stack:
        opened = []
        for namespace in namespaces:
            try:
                ns_fd = _open_private(namespace, stack)
            except FileNotFoundError:
                continue
            except (OSError, ValueError) as error:
                errors += 1
                reason = ("descriptor_exhausted" if isinstance(error, OSError) and error.errno in _DESCRIPTOR_ERRORS
                          else "namespace_untrusted")
                rows.append(sweep._bare_row("pytest-runs", reason, bytes=None))
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
            # Unledgered leftovers have no measurement; the shared helper's
            # default zero is not an allocated-byte observation.
            for row in recovered:
                row["bytes"] = None
            rows.extend(recovered)
            purged, step_errors = sweep.purge_quarantine(
                local, ledger, run_id, now=sweep.time.time(), quarantine_s=quarantine_s,
                task_root=task_root, repo_root=repo_root, apply=apply,
            )
            errors += step_errors
            rows.extend(purged)
            opened.append((namespace, ns_fd))
        if not opened:
            return rows, errors
        worktrees = sweep.registered_worktrees(repo_root)
        for namespace, ns_fd in opened:
            for name in sorted(os.listdir(ns_fd)):
                if name.startswith(sweep.QUARANTINE_PREFIX):
                    continue
                candidate = None
                try:
                    # One candidate owns its lock through its complete disposition.
                    with ExitStack() as disposition:
                        candidate = _classify(
                            name, namespace, ns_fd, worktrees=worktrees, now=sweep.time.time(),
                            apply=apply, stack=disposition,
                        )
                        rows.append(candidate.row)
                        if candidate.row["reason"] == "descriptor_exhausted":
                            errors += 1
                        if apply and candidate.row["decision"] == "would_delete":
                            errors += _delete(candidate, namespace, ns_fd, repo_root=repo_root)
                except OSError as error:
                    errors += 1
                    reason = "descriptor_exhausted" if error.errno in _DESCRIPTOR_ERRORS else "scan_error"
                    if candidate is None:
                        rows.append(sweep._bare_row(name, reason, error=sweep._errno_name(error), bytes=None))
                    elif candidate.row["decision"] != "deleted":
                        candidate.row.update(decision="preserve", reason=reason,
                                             error=sweep._errno_name(error), bytes=None)
    return rows, errors


def sweep_pytest_runs(
    *, apply: bool, ledger: Ledger, run_id: str, task_root: Path, quarantine_s: float, repo_root: Path,
) -> dict[str, Any]:
    """Sweep pytest namespaces with numeric measured-byte subtotals and completeness flags.

    An unmeasured row has ``bytes=None``. Existing numeric summary fields sum
    only measured rows; ``*_bytes_complete`` and ``*_unmeasured_entries``
    explicitly distinguish these lower bounds from complete totals.
    """
    rows = []
    errors = 0
    try:
        roots = set(scratch_scan_roots())
    except ScratchScanRootError:
        # The general temp sweep may already have applied. Keep its report and
        # fail this confined scan closed without falling back to host roots.
        roots = set()
        errors += 1
        rows.append(sweep._bare_row("pytest-runs", "scan_root_invalid", bytes=None))
    for root in sorted(roots):
        namespaces = tuple(root / NAMESPACE / name for name in (RUNS_DIRNAME, ownership.NAMESPACE_DIRNAME))
        try:
            # Legacy roots outside the two namespaces stay visible and untouched.
            with ExitStack() as stack:
                root_fd = _open_private(root, stack, private=False)
                for name in sorted(os.listdir(root_fd)):
                    if name.startswith("pytest-") and name != NAMESPACE:
                        size, _newest, _changed, problem = sweep.tree_facts(root / name)
                        rows.append(sweep._bare_row(name, "legacy_ownership_unknown", bytes=None if problem else size))
            found, step_errors = _namespace(
                namespaces, apply=apply, ledger=ledger, run_id=run_id,
                task_root=task_root, quarantine_s=quarantine_s, repo_root=repo_root,
            )
            rows.extend(found)
            errors += step_errors
        except FileNotFoundError:
            continue
        except (OSError, ValueError) as error:
            errors += 1
            reason = ("descriptor_exhausted" if isinstance(error, OSError) and error.errno in _DESCRIPTOR_ERRORS
                      else "namespace_untrusted")
            rows.append(sweep._bare_row("pytest-runs", reason, bytes=None))
    entries = ledger.entries()[0]
    for row in rows:
        entry = entries.get(row.get("ledger_id"))
        if entry is not None and entry.intent.get("allocated_bytes") is None:
            row["bytes"] = None
    held = [
        entry for entry in entries.values()
        if entry.state in sweep.HELD_STATES
        and entry.original.parent in {
            root / NAMESPACE / name for root in roots for name in (RUNS_DIRNAME, ownership.NAMESPACE_DIRNAME)
        }
    ]

    def total(decision: str) -> int:
        return sum(row["bytes"] or 0 for row in rows if row["decision"] == decision)

    unmeasured = sum(row["bytes"] is None for row in rows)
    protected_unmeasured = sum(row["bytes"] is None and row["decision"] == "preserve" for row in rows)
    remaining_unmeasured = sum(
        row["bytes"] is None and row["decision"] in {"preserve", "would_delete"} for row in rows
    )
    preserved_runs = sorted(
        (row for row in rows if row["decision"] == "preserve" and row["bytes"] is not None),
        key=lambda row: row["bytes"], reverse=True,
    )[:LARGEST_PRESERVED_RUNS]
    for rank, row in enumerate(preserved_runs, start=1):
        # The full receipt names it: rows still carry the folder name next to this rank.
        row["largest_preserved_rank"] = rank
    return {
        "inactive_hours": INACTIVE_S / 3600, "rows": rows, "errors": errors,
        "runs": len(rows), "bytes": sum(row["bytes"] or 0 for row in rows),
        "bytes_complete": unmeasured == 0, "unmeasured_entries": unmeasured,
        "protected_bytes_complete": protected_unmeasured == 0,
        "protected_unmeasured_entries": protected_unmeasured,
        "remaining_bytes_complete": remaining_unmeasured == 0,
        "remaining_unmeasured_entries": remaining_unmeasured,
        "descriptor_exhaustion_entries": sum(row["reason"] == "descriptor_exhausted" for row in rows),
        "by_reason": dict(Counter(row["reason"] for row in rows)),
        "by_decision": dict(Counter(row["decision"] for row in rows)),
        "preserved_by_reason": dict(
            Counter(row["reason"] for row in rows if row["decision"] == "preserve")
        ),
        "largest_preserved_runs": [
            {
                "rank": rank, "bytes": row["bytes"], "reason": row["reason"],
                "idle_hours": row.get("idle_hours"),
            }
            for rank, row in enumerate(preserved_runs, start=1)
        ],
        "would_delete_entries": sum(row["decision"] == "would_delete" for row in rows),
        "would_delete_bytes": total("would_delete"),
        "deleted_entries": sum(row["decision"] == "deleted" for row in rows),
        "deleted_bytes": total("deleted"),
        "reclaimed_entries": sum(row["decision"] == "deleted" for row in rows),
        "reclaimed_bytes": total("deleted"),
        "protected_bytes": total("preserve"),
        "remaining_runs": sum(row["decision"] in {"preserve", "would_delete"} for row in rows),
        "remaining_bytes": total("preserve") + total("would_delete"),
        "quarantine_held_entries": len(held),
        "quarantine_held_bytes": sum(entry.intent.get("allocated_bytes") or 0 for entry in held),
        "quarantine_held_bytes_complete": all(entry.intent.get("allocated_bytes") is not None for entry in held),
        "quarantine_held_unmeasured_entries": sum(entry.intent.get("allocated_bytes") is None for entry in held),
        "purged_entries": sum(row["decision"] == "purged" for row in rows),
        "purged_bytes": total("purged"),
    }
