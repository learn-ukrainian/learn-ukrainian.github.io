"""Inventory only owned pytest invocations for the existing scheduled sweep (#10831).

Completed runs leave the newest three eligible invocations in place. Older
ones enter the sweep's existing recoverable quarantine. Locks stay held across
selection and rename; unknown ownership never becomes an age-based deletion.
"""

from __future__ import annotations

import fcntl
import math
import os
import stat
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from scripts.common import task_scratch as ownership
from scripts.common.pytest_scratch import NAMESPACE
from scripts.common.scratch import scratch_scan_roots
from scripts.hygiene import tmp_sweep as sweep
from scripts.hygiene.tmp_sweep_ledger import Ledger


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


def _proof(fd: int, name: str) -> tuple[dict[str, Any] | None, str | None]:
    """Require completed, inode-bound pytest ownership and a proven dead owner."""
    metadata_fd = os.open(
        ownership.LEASE_FILENAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=fd,
    )
    try:
        metadata = os.fstat(metadata_fd)
        if (
            not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid()
            or metadata.st_nlink != 1 or metadata.st_size > ownership.LEASE_MAX_BYTES
        ):
            return None, "ownership_unknown"
        lease = ownership.parse_lease(os.read(metadata_fd, ownership.LEASE_MAX_BYTES + 1))
    finally:
        os.close(metadata_fd)
    info = os.fstat(fd)
    if (
        lease is None or lease["task_id"] != "pytest" or lease["invocation_id"] != name
        or lease["uid"] != os.geteuid()
        or lease["dir"] != {"dev": info.st_dev, "ino": info.st_ino}
        or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077
        or not math.isfinite(lease["created_at"]) or lease["created_at"] <= 0
        or lease["owner"]["pid"] <= 0 or not lease["owner"]["start_time"] or not lease["owner"]["boot_id"]
    ):
        return None, "ownership_unknown"
    if lease["state"] != "preserved":
        return lease, "completion_unknown"
    dead, reason = ownership._owner_dead(lease, boot=ownership.current_boot_id())
    if not dead:
        return lease, reason
    dead, reason = ownership._child_group_dead(lease, boot=ownership.current_boot_id())
    return lease, None if dead else reason


def _locked_run(path: Path, ns_fd: int, stack: ExitStack) -> tuple[int, int]:
    fd = os.open(path.name, sweep._DIR_FLAGS, dir_fd=ns_fd)
    stack.callback(os.close, fd)
    lock = os.open(ownership.LOCK_FILENAME, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    stack.callback(os.close, lock)
    info = os.fstat(lock)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_nlink != 1:
        raise ValueError("lock_untrusted")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if not os.path.samestat(os.stat(ownership.LOCK_FILENAME, dir_fd=fd, follow_symlinks=False), info):
        raise ValueError("lock_changed")
    return fd, lock


def _namespace(
    namespace: Path, *, keep: int, apply: bool, ledger: Ledger, run_id: str,
    task_root: Path, digest_limit: int, quarantine_s: float, repo_root: Path,
) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    errors = 0
    with ExitStack() as stack:
        ns_fd = _open_private(namespace, stack)
        if ledger.directory == namespace or namespace in ledger.directory.parents:
            raise ValueError("ledger_inside_pytest_namespace")
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
        tasks = sweep.load_tasks(task_root)
        references, process_complete = sweep.process_snapshot()
        worktrees = sweep.registered_worktrees(repo_root)
        eligible = []
        for name in sorted(os.listdir(ns_fd)):
            if name.startswith(sweep.QUARANTINE_PREFIX):
                continue
            path = namespace / name
            row = sweep._bare_row(name, "ownership_unknown", kind="directory")
            rows.append(row)
            row["bytes"], _newest, _changed, problem = sweep.tree_facts(path)
            try:
                fd, lock = _locked_run(path, ns_fd, stack)
                lease, reason = _proof(fd, name)
                if reason:
                    row["reason"] = reason
                    continue
                if problem:
                    row["reason"] = problem
                    continue
                if not _same(path, fd) or not _same(namespace, ns_fd):
                    row["reason"] = "identity_changed"
                    continue
                if not tasks.complete:
                    row["reason"] = "task_inventory_unknown"
                    continue
                if sweep.task_referenced(path, tasks.references) or sweep.task_attribution(name, tasks.records):
                    row["reason"] = "task_reference"
                    continue
                if not process_complete or any(ref == path or path in ref.parents for _pid, ref in references):
                    row["reason"] = "live_process" if process_complete else "liveness_unknown"
                    continue
                if worktrees is None or any(w == path or w in path.parents or path in w.parents for w in worktrees):
                    row["reason"] = "git_registration_unknown" if worktrees is None else "registered_worktree"
                    continue
                info = os.fstat(fd)
                row.update(identity=[info.st_dev, info.st_ino, info.st_uid])
                eligible.append((lease["created_at"], name, row, fd, lock, lease))
            except BlockingIOError:
                row["reason"] = "in_use"
            except FileNotFoundError:
                row["reason"] = "lock_missing_or_vanished"
            except (OSError, ValueError):
                row["reason"] = "ownership_unknown"
        quarantine = None
        try:
            for index, (_created, name, row, fd, lock, lease) in enumerate(sorted(eligible, reverse=True)):
                row["reason"] = "pytest_keep_newest" if index < keep else "completed_pytest_run"
                if index < keep:
                    continue
                row["decision"] = "would_reap"
                if not apply:
                    continue
                path = namespace / name
                before = sweep.tree_fingerprint(path)

                def recheck(
                    location: Path, fd: int = fd, name: str = name, lock: int = lock,
                    lease: dict[str, Any] = lease, before: Any = before,
                ) -> str | None:
                    current, reason = _proof(fd, name)
                    try:
                        lock_info = os.stat(ownership.LOCK_FILENAME, dir_fd=fd, follow_symlinks=False)
                    except OSError:
                        return "lock_changed"
                    if reason or current != lease or not os.path.samestat(lock_info, os.fstat(lock)):
                        return reason or "ownership_changed"
                    if not _same(namespace, ns_fd) or not _same(location, fd):
                        return "identity_changed"
                    return None if sweep.tree_fingerprint(location) == before else "quarantine_write"

                if before is None or recheck(path):
                    row.update(decision="preserve", reason="proof_changed")
                    continue
                quarantine = quarantine or sweep.open_quarantine(namespace, ns_fd)
                updated = sweep.quarantine_entry(
                    path, row, before, quarantine, root_fd=ns_fd, task_root=task_root,
                    ledger=ledger, run_id=run_id, digest_limit=digest_limit, recheck=recheck,
                )
                row.update(updated)
                errors += row["reason"] == "restore_blocked"
        finally:
            if quarantine is not None:
                sweep.close_quarantine(quarantine, ns_fd)
    return rows, errors


def sweep_pytest_runs(
    *, keep: int, apply: bool, ledger: Ledger, run_id: str, task_root: Path, digest_limit: int,
    quarantine_s: float, repo_root: Path,
) -> dict[str, Any]:
    """Sweep the dedicated pytest namespace, never the general managed scratch tree."""
    rows = []
    errors = 0
    roots = set(scratch_scan_roots())
    for root in sorted(roots):
        namespace = root / NAMESPACE / ownership.NAMESPACE_DIRNAME
        try:
            # Legacy lockless roots stay visible, but filenames never prove ownership.
            with ExitStack() as stack:
                root_fd = _open_private(root, stack, private=False)
                for name in sorted(os.listdir(root_fd)):
                    if name.startswith("pytest-") and name != NAMESPACE:
                        size, _newest, _changed, _problem = sweep.tree_facts(root / name)
                        rows.append(sweep._bare_row(name, "legacy_ownership_unknown", bytes=size))
            found, step_errors = _namespace(
                namespace, keep=keep, apply=apply, ledger=ledger, run_id=run_id,
                task_root=task_root, digest_limit=digest_limit, quarantine_s=quarantine_s, repo_root=repo_root,
            )
            rows.extend(found)
            errors += step_errors
        except FileNotFoundError:
            continue
        except (OSError, ValueError):
            errors += 1
            rows.append(sweep._bare_row("pytest-runs", "namespace_untrusted"))
    held = [
        entry for entry in ledger.entries()[0].values()
        if entry.state in sweep.HELD_STATES
        and entry.original.parent in {root / NAMESPACE / ownership.NAMESPACE_DIRNAME for root in roots}
    ]
    return {
        "keep": keep, "rows": rows, "errors": errors,
        "runs": len(rows), "bytes": sum(row["bytes"] or 0 for row in rows),
        "by_reason": dict(Counter(row["reason"] for row in rows)),
        "by_decision": dict(Counter(row["decision"] for row in rows)),
        "quarantined_bytes": sum(row["bytes"] or 0 for row in rows if row["decision"] == "quarantined"),
        "protected_bytes": sum(row["bytes"] or 0 for row in rows if row["decision"] == "preserve"),
        "remaining_runs": sum(row["decision"] in {"preserve", "would_reap"} for row in rows),
        "remaining_bytes": sum(row["bytes"] or 0 for row in rows if row["decision"] in {"preserve", "would_reap"}),
        "quarantine_held_entries": len(held),
        "quarantine_held_bytes": sum(entry.intent.get("allocated_bytes") or 0 for entry in held),
        "purged_entries": sum(row["decision"] == "purged" for row in rows),
        "purged_bytes": sum(row["bytes"] or 0 for row in rows if row["decision"] == "purged"),
    }
