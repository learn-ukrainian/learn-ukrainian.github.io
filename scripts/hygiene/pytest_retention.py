"""Delete inactive pytest scratch whose owner is provably gone (#11297, #11409).

Within the managed pytest namespaces only (``pytest-runs/runs`` and the
legacy ``pytest-runs/task-scratch``), a run folder is deleted once its newest
change anywhere inside (write or inode change, so freshly extracted files
with old mtimes stay young) is more than two hours old, no live process holds
it through its working directory, an open descriptor, a mapped file, its
command line or its environment, and its recorded lease owner is dead. A run
is abandoned only when the owner cannot be alive on this host: the lease
records the same kernel boot id, and the recorded pid is absent or now
reports a different start time (the number was reused). The lease lock must
also be acquired exclusively, so a live writer is never raced.

Unreadable processes are classified by owner. The run namespace is mode 0700
owned by the scanning user, so a holder must be that user or root. A
foreign-uid process cannot traverse the namespace and does not make liveness
unknown, which is the defect #11409 fixes: refusing to act because another
user's processes are unreadable meant nothing was ever reclaimed. When the
lease proves the owner dead on this boot, an unreadable process table no
longer blocks deletion at all; the lock is held by the sweep and the tree is
rechecked. The residual is a same-user or root process whose ``/proc`` entry
is unreadable (a non-dumpable process, or root) and that holds an idle
descriptor or working directory without writing: it is not distinguished
from no holder, and the run can be deleted after the bounded quarantine
rename and unchanged-fingerprint recheck. A same-user or root writer that
changes the tree during that window is renamed back. A run without a valid
lease keeps the older rule: an unreadable process of the scanning user, or of
an undeterminable owner, makes liveness unknown, and unknown preserves.

A missing or malformed lease carries no owner, so the older evidence applies:
the run lock, a readable live holder, and a trusted process snapshot. A
lease that exists but cannot be read (permission, not a regular file, foreign
owner, oversized or a read error) preserves as ``lease_unreadable``. Ownership
metadata, completion state, retention counts and the seven-day quarantine
play no part in the decision (the operator's retention decision for #11297).

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


@dataclass
class Holders:
    """One pass over every process: path references and raw argv/environment, never emitted.

    ``paths`` holds descriptor, cwd and map targets plus every path an
    absolute argument or environment value names; ``relative`` holds the
    paths their relative spellings name from the process cwd; ``texts``
    keeps the raw blobs so an absolute path embedded anywhere in a value
    still counts.
    ``complete`` is False when any live process of the scanning user (or of
    an undeterminable owner) could not be fully read; a foreign-uid process
    cannot reach the private namespace, and a root process is handled by the
    bounded quarantine/recheck path.
    ``unreadable`` counts every unreadable live process for the privacy-safe
    report; ``unreadable_foreign`` and ``unreadable_root`` split that count.
    ``descriptor_errors`` counts resource failures separately from process
    visibility failures; callers report them as sweep errors.
    """

    paths: list[tuple[int, str, str]] = field(default_factory=list)
    relative: list[tuple[int, str, str]] = field(default_factory=list)
    texts: list[tuple[int, str, bytes]] = field(default_factory=list)
    complete: bool = True
    unreadable: int = 0
    unreadable_foreign: int = 0
    unreadable_root: int = 0
    descriptor_errors: int = 0

    def holding(self, paths: Iterable[Path]) -> tuple[list[int], list[str]]:
        """PIDs and channels that reach any of ``paths`` or a path below it."""
        found: set[tuple[int, str]] = set()
        for path in paths:
            needle = str(path)
            prefix = needle + "/"
            encoded = os.fsencode(needle)
            for pid, channel, target in self.paths:
                if target == needle or target.startswith(prefix):
                    found.add((pid, channel))
            for pid, channel, blob in self.texts:
                if encoded in blob:
                    found.add((pid, channel))
            for pid, channel, target in self.relative:
                # Inside a held cwd every word reads as a path below it; the cwd already says so.
                if (target == needle or target.startswith(prefix)) and (pid, "cwd") not in found:
                    found.add((pid, channel))
        return sorted({pid for pid, _ in found}), sorted({channel for _, channel in found})


def _named_paths(blob: bytes, cwd: str, forms: dict[str, set[Path]]) -> tuple[set[str], set[str]]:
    """Paths an argument, ``VAR=value`` value or ``:`` list entry names: (absolute, relative to the cwd).

    Each spelling gets the general sweep's reference forms (``..`` and ``.``
    folded lexically, plus the form the kernel resolves, which follows a
    symlink before a later ``..``), so ancestor-relative, dot-dot and aliased
    spellings, alone or combined, reach the same run as its canonical path.
    ``forms`` caches them across processes for one snapshot.
    """
    base = cwd.removesuffix(" (deleted)")
    absolute: set[str] = set()
    relative: set[str] = set()
    for token in blob.split(b"\0"):
        for value in {token, token.partition(b"=")[2]}:
            for item in value.split(b":"):
                if not item:
                    continue
                spelling = os.path.join(base, os.fsdecode(item))
                if spelling not in forms:
                    forms[spelling] = sweep._reference_forms(spelling)
                (absolute if item.startswith(b"/") else relative).update(map(str, forms[spelling]))
    return absolute, relative


def _process_uid(entry: Path) -> int | None:
    """The uid owning a ``/proc/<pid>`` entry, or ``None`` when even that is unreadable."""
    try:
        return entry.stat().st_uid
    except OSError:
        return None


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
    except OSError as error:
        holders.complete = False
        holders.descriptor_errors += error.errno in _DESCRIPTOR_ERRORS
        return holders
    me = os.getpid()
    forms: dict[str, set[Path]] = {}
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
                # The shared state reader hides OSError. Preserve resource failures
                # separately from genuinely unreadable live processes.
                (entry / "stat").read_bytes()
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
        except (OSError, ValueError) as error:
            if isinstance(error, OSError) and error.errno in _DESCRIPTOR_ERRORS:
                holders.complete = False
                holders.descriptor_errors += 1
                continue
            if _process_vanished(entry):
                continue
            holders.unreadable += 1
            uid = _process_uid(entry)
            if uid == 0:
                # Root may reach the private namespace; deletion uses the bounded
                # quarantine/recheck path instead of requiring all-process visibility.
                holders.unreadable_root += 1
            elif uid is not None and uid != os.geteuid():
                holders.unreadable_foreign += 1
            else:
                holders.complete = False
            continue
        holders.paths.extend((p, channel, target.removesuffix(" (deleted)")) for p, channel, target in found)
        for p, channel, blob in texts:
            absolute, relative = _named_paths(blob, cwd, forms)
            holders.paths.extend((p, channel, named) for named in absolute)
            holders.relative.extend((p, channel, named) for named in relative)
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


def _read_lease(run_fd: int) -> tuple[dict[str, Any] | None, str | None, bool]:
    """Read ``lease.json`` relative to the run: ``(lease, error, present)``.

    A missing lease records no owner. A lease that exists but cannot be read as
    a regular, owner-owned file of bounded size is unknown and preserves. A
    malformed lease also records no owner but is not an I/O failure, so the
    lock and holder evidence decide like an unleased run.
    """
    try:
        info = os.stat(ownership.LEASE_FILENAME, dir_fd=run_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None, None, False
    except OSError:
        return None, "lease_unreadable", True
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_size > ownership.LEASE_MAX_BYTES:
        return None, "lease_unreadable", True
    try:
        fd = os.open(ownership.LEASE_FILENAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=run_fd)
    except OSError:
        return None, "lease_unreadable", True
    try:
        if not os.path.samestat(os.fstat(fd), info):
            return None, "lease_unreadable", True
        data = bytearray()
        while chunk := os.read(fd, 65536):
            data += chunk
            if len(data) > ownership.LEASE_MAX_BYTES:
                return None, "lease_unreadable", True
    except OSError:
        return None, "lease_unreadable", True
    finally:
        os.close(fd)
    lease = ownership.parse_lease(bytes(data))
    if lease is None:
        return None, None, True
    return lease, None, True


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
    """Classify the recorded owner: ``owner_dead``, ``owner_alive``, ``different_boot`` or unknown.

    Only the same kernel boot and a matching recorded start time prove the
    process is the owner. A missing boot id, start time or process table is
    unknown, never dead.
    """
    owner = lease["owner"]
    recorded_boot = owner.get("boot_id")
    if boot_id is None or recorded_boot is None:
        return "owner_liveness_unknown"
    if recorded_boot != boot_id:
        return "different_boot"
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
    lease_present: bool = False
    owner_dead: bool = False


def _abandonment(candidate: Candidate, *, boot_id: str | None) -> tuple[str | None, bool]:
    """Why the recorded owner does not prove abandonment, and whether it does.

    A run with a lease must also have had its lock acquired exclusively; a
    missing or malformed lease records no owner and falls back to the lock and
    holder evidence. An unreadable lease always preserves. ``True`` means the
    owner is provably dead on this boot, so an unreadable process snapshot no
    longer blocks the deletion; the quarantine/recheck still proves the tree.
    """
    if candidate.lease_error:
        return candidate.lease_error, False
    if candidate.lease is not None:
        if not candidate.locked:
            return "lock_missing", False
        status = _owner_status(candidate.lease, boot_id)
        if status == "owner_dead":
            return None, True
        return ("live_owner" if status == "owner_alive" else status), False
    if candidate.lease_present and not candidate.locked:
        return "lock_missing", False
    return None, False


def _classify(
    name: str, namespace: Path, ns_fd: int, *, holders: Holders, worktrees: set[Path] | None, now: float,
    apply: bool, stack: ExitStack,
) -> Candidate:
    """Decide one run folder; transfer only eligible apply locks to the deletion scope."""
    path = namespace / name
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
        candidate.lease, candidate.lease_error, candidate.lease_present = _read_lease(run_fd)
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
        row["bytes"], _newest, changed, problem = sweep.tree_facts(path)
        row["newest_change"] = changed
        row["idle_hours"] = round(max(0.0, now - changed) / 3600, 2)
        pids, channels = holders.holding([path])
        row.update(live_pids=pids, holders=channels)
        owner_reason, candidate.owner_dead = _abandonment(
            candidate, boot_id=ownership.current_boot_id()
        )
        if problem:
            row["reason"] = problem
            row["bytes"] = None
        elif apply and candidate.before is None:
            row["reason"] = "tree_unknown"
        elif now - changed <= INACTIVE_S:
            row["reason"] = "too_young"
        elif pids:
            row["reason"] = "live_process"
        elif holders.descriptor_errors:
            row["reason"] = "descriptor_exhausted"
        elif owner_reason:
            row["reason"] = owner_reason
        elif not candidate.owner_dead and not holders.complete:
            row["reason"] = "liveness_unknown"
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
    if holders.descriptor_errors:
        return "descriptor_exhausted"
    if not candidate.owner_dead and not holders.complete:
        return "liveness_unknown"
    return None if sweep.tree_fingerprint(held) == candidate.before else "recent_write"


def _delete(
    candidates: list[Candidate], namespace: Path, ns_fd: int, *, repo_root: Path, scan_holders: Holders,
) -> int:
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
                row.update(decision="preserve", reason="identity_changed", bytes=None)
                continue
            try:
                sweep.rename_noreplace(ns_fd, candidate.name, quarantine.fd, candidate.name)
            except OSError as error:
                row.update(decision="preserve", reason="rename_refused", error=sweep._errno_name(error), bytes=None)
                errors += 1
                continue
            sweep._sync_rename(ns_fd, quarantine.fd)
            held.append(candidate)
        # Nothing can newly reach a held folder by its old name. Our run locks are inspection handles.
        holders = holder_snapshot(frozenset(c.lock for c in held if c.lock is not None))
        scan_holders.complete = scan_holders.complete and holders.complete
        scan_holders.unreadable = max(scan_holders.unreadable, holders.unreadable)
        scan_holders.unreadable_foreign = max(scan_holders.unreadable_foreign, holders.unreadable_foreign)
        scan_holders.unreadable_root = max(scan_holders.unreadable_root, holders.unreadable_root)
        scan_holders.descriptor_errors += holders.descriptor_errors
        errors += holders.descriptor_errors
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
                    candidate.row.update(decision="preserve", reason="delete_refused", error=detail, bytes=None)
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
            return rows, errors, holders
        holders = holder_snapshot()
        errors += holders.descriptor_errors
        worktrees = sweep.registered_worktrees(repo_root)
        for namespace, ns_fd in opened:
            for name in sorted(os.listdir(ns_fd)):
                if name.startswith(sweep.QUARANTINE_PREFIX):
                    continue
                candidate = None
                try:
                    # One candidate owns its lock through its complete disposition.
                    # Releasing it here leaves headroom for the next fresh holder scan,
                    # independently of cohort size or namespace order.
                    with ExitStack() as disposition:
                        candidate = _classify(
                            name, namespace, ns_fd, holders=holders, worktrees=worktrees, now=sweep.time.time(),
                            apply=apply, stack=disposition,
                        )
                        rows.append(candidate.row)
                        if candidate.row["reason"] == "descriptor_exhausted" and not holders.descriptor_errors:
                            errors += 1
                        if apply and candidate.row["decision"] == "would_delete":
                            errors += _delete([candidate], namespace, ns_fd, repo_root=repo_root, scan_holders=holders)
                except OSError as error:
                    errors += 1
                    reason = "descriptor_exhausted" if error.errno in _DESCRIPTOR_ERRORS else "scan_error"
                    if candidate is None:
                        rows.append(sweep._bare_row(name, reason, error=sweep._errno_name(error), bytes=None))
                    elif candidate.row["decision"] != "deleted":
                        candidate.row.update(decision="preserve", reason=reason,
                                             error=sweep._errno_name(error), bytes=None)
    return rows, errors, holders


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
    unreadable = 0
    unreadable_foreign = 0
    unreadable_root = 0
    complete = True
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
            found, step_errors, holders = _namespace(
                namespaces, apply=apply, ledger=ledger, run_id=run_id,
                task_root=task_root, quarantine_s=quarantine_s, repo_root=repo_root,
            )
            rows.extend(found)
            errors += step_errors
            if holders is not None:
                complete = complete and holders.complete
                unreadable = max(unreadable, holders.unreadable)
                unreadable_foreign = max(unreadable_foreign, holders.unreadable_foreign)
                unreadable_root = max(unreadable_root, holders.unreadable_root)
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
        "liveness_complete": complete, "liveness_unreadable_processes": unreadable,
        "liveness_unreadable_foreign_processes": unreadable_foreign,
        "liveness_unreadable_root_processes": unreadable_root,
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
