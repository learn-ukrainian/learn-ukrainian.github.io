"""Legacy runtime scratch creation and guarded evidence-preserving cleanup (B6).

The sweep of pre-v2 leases remains with its existing owner. These operations
handle one v2 worker's lease and reuse the authoritative task store.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import stat
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root as _main_checkout_root
from scripts.common.repo_root import resolve_repo_root
from scripts.common.scratch import (
    DEFAULT_SCRATCH_ROOT,
    ScratchScanRootError,
    ensure_scratch_root,
    fallback_scratch_root,
    resolve_scratch_root,
    scratch_scan_roots,
)
from scripts.dispatcher import store
from scripts.orchestration.task_record_store import task_state_lock
from scripts.orchestration.task_record_store import write_record_unlocked as _write_record_unlocked

_REPO_ROOT = resolve_repo_root(Path(__file__), 2)
_RUNTIME_TMP_TASK_ID_MARKER = ".delegate-task-id"
_state_path_no_create = store.record_path

def _runtime_tmp_lease_name(task_id: str) -> str:
    """Return one safe path component for a task's runtime tmp lease."""
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", task_id):
        return task_id
    return re.sub(r"[^A-Za-z0-9._-]+", "-", task_id).strip("./-") or "task"


def _create_runtime_tmp_lease(task_id: str) -> tuple[Path, Path]:
    """Create and return a task lease plus its resolved namespace root.

    The lease is intentionally deterministic per task ID: a task can restart
    after its previous worker has finished and re-create the same root, while
    Stage 2 will eventually handle roots left by crashed processes.

    #7164: the namespace lives under the disk-backed fleet scratch root
    (``scripts/common/scratch.py``), not tmpfs ``/tmp`` — worker TMPDIR
    payloads must not be able to exhaust the small per-user tmpfs quota.
    """
    namespace_root = ensure_scratch_root() / "learn-ukrainian"
    try:
        namespace_root.mkdir(parents=True, exist_ok=True)
        namespace_stat = namespace_root.lstat()
    except OSError as exc:
        raise RuntimeError(
            f"could not create runtime tmp namespace {namespace_root}: {exc}",
        ) from exc
    if stat.S_ISLNK(namespace_stat.st_mode):
        raise RuntimeError(
            f"runtime tmp namespace must not be a symlink: {namespace_root}",
        )

    lease_root = namespace_root / _runtime_tmp_lease_name(task_id)
    try:
        lease_root.mkdir(exist_ok=True)
        lease_stat = lease_root.lstat()
        resolved_namespace = namespace_root.resolve(strict=True)
        resolved_lease = lease_root.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError(
            f"could not create runtime tmp lease {lease_root}: {exc}",
        ) from exc
    if stat.S_ISLNK(lease_stat.st_mode):
        raise RuntimeError(
            f"runtime tmp lease must not be a symlink: {lease_root}",
        )
    if not stat.S_ISDIR(lease_stat.st_mode) or resolved_lease.parent != resolved_namespace:
        raise RuntimeError(
            f"runtime tmp lease is not a direct child of its namespace: {lease_root}",
        )
    _write_runtime_tmp_task_id_marker(resolved_lease, task_id)
    return resolved_lease, resolved_namespace


def _runtime_tmp_task_id_marker_path(lease_root: Path) -> Path:
    return lease_root / _RUNTIME_TMP_TASK_ID_MARKER


def _write_runtime_tmp_task_id_marker(
    lease_root: Path,
    task_id: str,
    *,
    no_clobber: bool = False,
) -> None:
    """Persist the owning task id so orphan sweeps never scan task records."""
    marker = _runtime_tmp_task_id_marker_path(lease_root)
    if no_clobber:
        try:
            fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(task_id)
        return
    tmp = marker.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(task_id, encoding="utf-8")
    os.replace(tmp, marker)


def _read_runtime_tmp_task_id_marker(lease_root: Path) -> str | None:
    marker = _runtime_tmp_task_id_marker_path(lease_root)
    try:
        task_id = marker.read_text(encoding="utf-8").strip()
    except (OSError, ValueError):
        return None
    return task_id or None


def _runtime_tmp_lease_bytes(lease_root: Path) -> int:
    """Count lease payload bytes without traversing directory symlinks."""
    total = 0
    seen_regular_files: set[tuple[int, int]] = set()
    for directory, dirnames, filenames in os.walk(lease_root, followlinks=False):
        for name in [*dirnames, *filenames]:
            path = Path(directory) / name
            try:
                entry = path.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISREG(entry.st_mode):
                inode = (entry.st_dev, entry.st_ino)
                if inode in seen_regular_files:
                    continue
                seen_regular_files.add(inode)
                total += entry.st_size
            elif stat.S_ISLNK(entry.st_mode):
                # Account for the link's own small directory entry, never its
                # target. ``os.walk(..., followlinks=False)`` will not descend.
                total += entry.st_size
    return total


def _grant_owner_rwx_at(path: Path, *, dir_fd: int) -> bool:
    """Give the owner access to a non-symlink path anchored at ``dir_fd``."""
    try:
        entry = os.stat(path, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(entry.st_mode):
        return False
    mode = stat.S_IMODE(entry.st_mode)
    repaired_mode = mode | stat.S_IRWXU
    if repaired_mode == mode:
        return False
    os.chmod(
        path,
        repaired_mode,
        dir_fd=dir_fd,
        follow_symlinks=False,
    )
    return True


def _runtime_tmp_reap_onexc(
    lease: Path,
    namespace: Path,
    namespace_fd: int,
    repairs: set[Path],
):
    """Build an ``rmtree`` repair callback confined to one verified lease."""

    def repair(_func: Any, raw_path: str | os.PathLike[str], exc: BaseException) -> None:
        if not isinstance(exc, PermissionError):
            raise exc
        path = Path(raw_path)
        try:
            candidate = path.relative_to(namespace) if path.is_absolute() else path
            candidate.relative_to(lease.name)
        except ValueError:
            raise exc from None
        if _grant_owner_rwx_at(candidate, dir_fd=namespace_fd):
            repairs.add(candidate)
        if _grant_owner_rwx_at(candidate.parent, dir_fd=namespace_fd):
            repairs.add(candidate.parent)

    return repair


def _remove_runtime_tmp_lease(lease: Path, namespace: Path) -> None:
    """Delete one verified lease, repairing restrictive owned entries first."""
    if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
        raise RuntimeError("platform rmtree lacks symlink-attack protection")
    if not hasattr(os, "O_NOFOLLOW"):
        raise RuntimeError("platform lacks O_NOFOLLOW for runtime tmp cleanup")
    open_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    open_flags |= os.O_NOFOLLOW
    last_error: OSError | None = None
    # ``shutil.rmtree`` calls onexc but cannot resume an ``os.open`` that
    # failed while descending into a mode-000 directory. Re-run the complete,
    # fd-relative walk after every actual permission repair: a tree can have
    # any number of nested restricted directories, so a fixed retry count
    # abandons valid entries below the next barrier.
    while os.path.lexists(lease):
        repairs: set[Path] = set()
        namespace_fd = os.open(namespace, open_flags)
        try:
            shutil.rmtree(
                lease.name,
                dir_fd=namespace_fd,
                onexc=_runtime_tmp_reap_onexc(lease, namespace, namespace_fd, repairs),
            )
        except FileNotFoundError:
            return
        except OSError as exc:
            last_error = exc
        finally:
            os.close(namespace_fd)
        if not os.path.lexists(lease):
            return
        if not repairs:
            break
    # A lease already gone at entry (e.g. a concurrent sweep won the race) is
    # success, not a survived-cleanup failure — the loop guard never ran rmtree,
    # so nothing above could return early on its behalf.
    if not os.path.lexists(lease):
        return
    if last_error is not None:
        raise OSError(
            last_error.errno,
            f"runtime tmp lease survived hardened cleanup: {lease}: {last_error.strerror or last_error}",
            last_error.filename or str(lease),
        )
    raise OSError(f"runtime tmp lease survived hardened cleanup: {lease}")


def _scratch_scan_roots() -> list[Path]:
    """Return reaper scan roots, or raise ``ScratchScanRootError`` here.

    A misconfigured ``LU_SCRATCH_SCAN_ROOT`` fails at this dispatch boundary.
    The error names the variable and the reason, includes no filesystem path,
    and is not chained to the resolver's traceback.
    """
    try:
        return scratch_scan_roots()
    except ScratchScanRootError as exc:
        raise ScratchScanRootError(exc.reason) from None


def saved_task_response(record: Mapping[str, Any], record_path: Path | None = None) -> str | None:
    """The worker's response as the record saved it, or None when it is gone or was replaced.

    Held-work preservation reads it. The ``.result`` sidecar next to the record is read first (it moves with the
    record into the archive), then ``result_file``. A text whose length is not
    the recorded ``response_chars`` was replaced after the worker finished. A
    record with an empty response wrote no result file: that response is ``""``.
    """
    chars = record.get("response_chars")
    known_chars = isinstance(chars, int) and not isinstance(chars, bool)
    candidates: list[Path] = []
    if record_path is not None:
        candidates.append(record_path.with_suffix(".result"))
    result_file = record.get("result_file")
    if isinstance(result_file, str) and result_file:
        candidates.append(Path(result_file))
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        return text if not known_chars or len(text) == chars else None
    if known_chars and chars == 0 and not result_file:
        return ""
    return None


def _read_state_json(path: Path) -> dict[str, Any] | None:
    """Read a state file without hydrating read-only snapshot sidecars."""
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _preserve_runtime_tmp_held_work(
    lease: Path,
    record: dict[str, Any] | None,
    response: str | None = None,
) -> dict[str, Any]:
    """Publish held-work and evidence retrieval metadata before any lease deletion.

    The supported ``evidence/`` directory (#11342) is preserved first: a review
    that writes only there keeps an auditable copy after task cleanup. The
    citation-driven held-work pass stays as before. A preservation failure is a
    typed refusal, so the caller retains the lease instead of deleting bytes.
    """
    from scripts.fleet import runtime_held_work

    if record is None:
        # A stateless lease has no task store entry to attribute a receipt to.
        # The dispatch marker distinguishes supported evidence from a tool's
        # own evidence directory, which keeps its existing age-based retention.
        if os.path.lexists(_runtime_tmp_task_id_marker_path(lease)):
            runtime_held_work.require_empty_evidence(lease)
        return {}
    if response is None:
        task_id = record.get("task_id")
        response = saved_task_response(record, _state_path_no_create(task_id) if isinstance(task_id, str) else None)
        if response is None and (record.get("result_file") or record.get("response_chars")):
            raise runtime_held_work.HeldWorkPreservationError()
    try:
        bound_root = record.get("runtime_tmp_root")
        if bound_root and Path(bound_root).absolute() != lease.absolute():
            raise runtime_held_work.HeldWorkPreservationError()
        evidence = runtime_held_work.preserve_evidence(lease, primary=_main_checkout_root(_REPO_ROOT), record=record)
        receipt = runtime_held_work.preserve(
            lease, primary=_main_checkout_root(_REPO_ROOT), record=record, response=response or ""
        )
        updates: dict[str, Any] = {}
        if receipt is not None:
            updates["preserved_held_work"] = receipt
        if evidence is not None:
            updates["preserved_evidence"] = evidence
        if not updates:
            return {}
        path = _state_path_no_create(record["task_id"])
        with task_state_lock(path):
            current = _read_state_json(path)
            if current is None or any(current.get(key) != record.get(key) for key in ("task_id", "run_nonce")):
                raise runtime_held_work.HeldWorkPreservationError()
            current.update(updates)
            _write_record_unlocked(path, current)
        record.update(updates)
        return updates
    except runtime_held_work.EvidencePreservationError:
        raise
    except (OSError, ValueError, TypeError):
        raise runtime_held_work.HeldWorkPreservationError() from None


def _require_preserved_evidence_still_matches(
    lease: Path, updates: Mapping[str, Any], *, dispatch_lease: bool
) -> None:
    """Refuse lease deletion when supported evidence changed after its receipt (#11342).

    ``preserve_evidence`` copies to a fixed point and receipts only a set verified
    identical to the source. Recheck immediately before deletion so a file that
    appeared or changed after the final enumeration is never silently lost; the
    typed refusal keeps the lease.
    Without a receipt, dispatch evidence must still be absent or empty.
    ``dispatch_lease`` is captured before preservation and accounting, so losing
    the marker during either operation cannot bypass the final recheck.
    """
    from scripts.fleet import runtime_held_work

    receipt = updates.get("preserved_evidence") if isinstance(updates, Mapping) else None
    if receipt is None:
        if dispatch_lease:
            runtime_held_work.require_empty_evidence(lease)
        return
    if not runtime_held_work.evidence_matches_receipt(lease, receipt):
        raise runtime_held_work.EvidencePreservationError()


def _reap_runtime_tmp_lease(
    lease_root: Path | str | None,
    namespace_root: Path | str | None,
    *,
    task_record: dict[str, Any] | None = None,
    response: str | None = None,
) -> dict[str, Any]:
    """Best-effort, fd-relative deletion of one task-scoped runtime lease.

    This is intentionally stricter than a generic ``rm -rf``. It only removes
    a non-symlink direct child of the dispatcher-created namespace and uses
    ``shutil.rmtree``'s fd-based implementation so a symlink swap cannot turn
    cleanup into a deletion outside the lease. A filesystem or validation
    failure is recorded on ``tmp_reap_error`` and does not fail the worker.
    Cited held work is copied and its retrieval manifest published before
    deletion; preservation failure refuses deletion with a typed reason.
    ``ScratchScanRootError`` propagates: a misconfigured scan root is not
    telemetry, and this function raises it before it deletes the lease.
    """
    result: dict[str, Any] = {
        "tmp_bytes_freed": 0,
        "tmp_reap_error": None,
    }
    worker_base_root: Path | None = None
    resolved_lease: Path | None = None
    try:
        if lease_root is None or namespace_root is None:
            raise ValueError("runtime tmp lease metadata is missing")
        lease = Path(lease_root)
        namespace = Path(namespace_root)
        namespace_stat = namespace.lstat()
        lease_stat = lease.lstat()
        if stat.S_ISLNK(namespace_stat.st_mode):
            raise ValueError("runtime tmp namespace is a symlink")
        if stat.S_ISLNK(lease_stat.st_mode):
            raise ValueError("runtime tmp lease is a symlink")
        if not stat.S_ISDIR(namespace_stat.st_mode):
            raise ValueError("runtime tmp namespace is not a directory")
        if not stat.S_ISDIR(lease_stat.st_mode):
            raise ValueError("runtime tmp lease is not a directory")

        resolved_namespace = namespace.resolve(strict=True)
        resolved_lease = lease.resolve(strict=True)
        resolved_tmp_root = Path(tempfile.gettempdir()).resolve(strict=True)
        if resolved_tmp_root == resolved_lease:
            # The worker deliberately points TMPDIR at its lease. In that one
            # process context, use the pre-override root recorded by the
            # dispatcher; parent cleanup still validates against its live
            # tempfile root, so a stale inherited base cannot bless a child.
            runtime_tmp_base_root = os.environ.get("LU_RUNTIME_TMP_BASE_ROOT")
            if not runtime_tmp_base_root:
                raise ValueError("runtime tmp worker is missing its base root")
            worker_base_root = Path(runtime_tmp_base_root).resolve(strict=True)
            accepted_parents = {worker_base_root}
        else:
            # #7164: leases live under the disk-backed fleet scratch root; the
            # legacy tmpfs $TMPDIR namespace stays accepted so pre-change
            # leases can still be reaped. Fallback scratch root is also accepted.
            accepted_parents = {root.resolve() for root in _scratch_scan_roots()}
            with contextlib.suppress(OSError):
                accepted_parents.add(resolve_scratch_root().resolve())
            with contextlib.suppress(OSError):
                accepted_parents.add(fallback_scratch_root().resolve())
            with contextlib.suppress(OSError):
                accepted_parents.add(DEFAULT_SCRATCH_ROOT.resolve())
            accepted_parents.add(resolved_tmp_root)
        if resolved_namespace.parent not in accepted_parents:
            raise ValueError(
                "resolved runtime tmp namespace is not directly under an approved scratch root",
            )
        if resolved_lease.parent != resolved_namespace:
            raise ValueError(
                "resolved runtime tmp lease is not under $TMPDIR/learn-ukrainian",
            )
        if resolved_namespace.name != "learn-ukrainian":
            raise ValueError("runtime tmp namespace has the wrong name")
        if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
            raise RuntimeError("platform rmtree lacks symlink-attack protection")

        if task_record is None:
            task_id = _read_runtime_tmp_task_id_marker(lease)
            task_record = _read_state_json(store.record_path(task_id)) if task_id else None
        dispatch_lease = task_record is not None or os.path.lexists(_runtime_tmp_task_id_marker_path(lease))
        result.update(_preserve_runtime_tmp_held_work(lease, task_record, response))
        bytes_freed = _runtime_tmp_lease_bytes(lease)
        _require_preserved_evidence_still_matches(lease, result, dispatch_lease=dispatch_lease)
        _remove_runtime_tmp_lease(lease, namespace)
        if os.path.lexists(lease):
            raise OSError(f"runtime tmp lease survived hardened cleanup: {lease}")
        result["tmp_bytes_freed"] = bytes_freed
    except ScratchScanRootError:
        raise
    except Exception as exc:
        result["tmp_reap_error"] = getattr(exc, "code", None) or (f"{type(exc).__name__}: {exc}")[:500]
    if worker_base_root is not None and resolved_lease is not None and not os.path.lexists(resolved_lease):
        _rebind_reaped_process_tmp(resolved_lease, worker_base_root)
    return result


def _rebind_reaped_process_tmp(lease: Path, base_root: Path) -> None:
    """Move this process's temporary-file root off its reaped runtime lease (#9878).

    A worker process runs with ``TMPDIR`` at its lease, and ``tempfile`` caches
    that root per process. The worker reaps the lease as soon as its agent
    exits, yet the finalize steps after the reap still create temporary files:
    the Kimi content check's and auto-finalize's scratch index, and the hooks of
    the commit and push they spawn. Each found its root gone (FileNotFoundError).
    Those steps now use the base root the lease lived under, which outlives
    them; the runtime lease variable naming the removed directory is dropped.
    """

    def _in_lease(value: str | None) -> bool:
        if not value:
            return False
        try:
            return Path(value).resolve().is_relative_to(lease)
        except (OSError, RuntimeError, ValueError):
            return False

    if _in_lease(tempfile.tempdir):
        tempfile.tempdir = str(base_root)
    if _in_lease(os.environ.get("TMPDIR")):
        os.environ["TMPDIR"] = str(base_root)
    if _in_lease(os.environ.get("LU_RUNTIME_TMP_ROOT")):
        os.environ.pop("LU_RUNTIME_TMP_ROOT", None)
