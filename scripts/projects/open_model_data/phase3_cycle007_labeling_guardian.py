#!/usr/bin/env python3
"""Storage-safe, resumable guardian for Cycle 007 dual-provider labeling.

This wrapper never reads label content and never discovers runtime locations.
It validates six explicit bind mounts, excludes duplicate execution, and drives
the reviewed controller only up to an operator-selected stage boundary.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

STAGES = ("gemini", "grok", "compare", "audit", "adjudicate", "resolve", "certify")
OUTPUT_ROOTS = (
    "label-output-gemini-cycle007-v1",
    "label-output-grok-cycle007-v1",
    "dual-label-output-cycle007-v1",
    "consensus-audit-cycle007-v1",
    "dual-label-adjudication-cycle007-v1",
    "dual-label-final-cycle007-v1",
)
MARKED_STAGES = frozenset({"audit", "adjudicate"})
EXECUTION_LOCK_FD_ENV = "PHASE3_CYCLE007_EXECUTION_LOCK_FD"
RECEIPT_SCHEMA = "phase3_cycle007_labeling_guardian_v1"
MAX_RECOVERY_FILES = 64
MAX_RECOVERY_BYTES = 16 * 1024 * 1024
MOUNT_TIMEOUT_SECONDS = 30
STATUS_TIMEOUT_SECONDS = 300
STAGE_TIMEOUT_SECONDS = 72 * 60 * 60


class GuardianError(ValueError):
    """Expected fail-stop condition represented by a text-free failure code."""


@dataclass(frozen=True)
class MountEntry:
    mount_point: Path
    root: str
    source: str
    device: str


@dataclass(frozen=True)
class Config:
    action: str
    package: Path
    backing_root: Path
    guardian_lock: Path
    controller_lock: Path
    execution_lock: Path
    controller: Path
    preflight_receipt: Path | None
    gemini_canary_receipt: Path | None
    grok_canary_receipt: Path | None
    agy_executable: Path | None
    grok_executable: Path | None
    code_paths: dict[str, Path]
    owner_uid: int
    owner_gid: int
    min_free_bytes: int
    through: str | None
    receipt: Path | None
    mountinfo: Path
    mount_command: str
    operator_inspected_count: int | None
    resolution_authorization: Path | None
    resolution_authority_attestation: Path | None
    resolution_authority_root: Path | None
    resolution_nonce_ledger: Path | None
    resolution_advisor_response: Path | None


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".cycle007-guardian-tmp-{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(_canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        _fsync_directory(path.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _remove_durable(path: Path) -> None:
    path.unlink(missing_ok=True)
    _fsync_directory(path.parent)


def _assert_absolute(path: Path, code: str = "invalid_runtime_path") -> None:
    if not path.is_absolute():
        raise GuardianError(code)


def _assert_no_symlink_components(path: Path, *, allow_missing_leaf: bool = False) -> None:
    _assert_absolute(path)
    current = Path(path.anchor)
    parts = path.parts[1:]
    for index, part in enumerate(parts):
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            if allow_missing_leaf and index == len(parts) - 1:
                return
            raise GuardianError("runtime_path_missing") from None
        if stat.S_ISLNK(info.st_mode):
            raise GuardianError("runtime_path_symlink")


def _private_directory(path: Path, uid: int, gid: int, *, create: bool) -> None:
    _assert_absolute(path)
    _assert_no_symlink_components(path, allow_missing_leaf=create)
    if create and not path.exists():
        path.mkdir(mode=0o700)
        os.chown(path, uid, gid)
    try:
        info = path.lstat()
    except FileNotFoundError:
        raise GuardianError("runtime_path_missing") from None
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise GuardianError("invalid_runtime_path")
    if info.st_uid != uid or info.st_gid != gid or stat.S_IMODE(info.st_mode) != 0o700:
        raise GuardianError("runtime_permission_drift")


def _non_overlapping(first: Path, second: Path) -> bool:
    return not (first == second or first.is_relative_to(second) or second.is_relative_to(first))


def _decode_mount_field(value: str) -> str:
    return value.replace("\\040", " ").replace("\\011", "\t").replace("\\012", "\n").replace("\\134", "\\")


def _mount_entries(path: Path) -> list[MountEntry]:
    entries: list[MountEntry] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        raise GuardianError("mount_table_unavailable") from None
    for line in lines:
        fields = line.split()
        try:
            separator = fields.index("-")
            entries.append(
                MountEntry(
                    mount_point=Path(_decode_mount_field(fields[4])),
                    root=_decode_mount_field(fields[3]),
                    source=_decode_mount_field(fields[separator + 2]),
                    device=fields[2],
                )
            )
        except (IndexError, ValueError):
            raise GuardianError("mount_table_invalid") from None
    return entries


def _exact_mount(entries: Sequence[MountEntry], target: Path) -> MountEntry | None:
    matches = [entry for entry in entries if entry.mount_point == target]
    if len(matches) > 1:
        raise GuardianError("mount_identity_drift")
    return matches[0] if matches else None


def _same_identity(source: Path, target: Path) -> bool:
    source_info = source.stat()
    target_info = target.stat()
    return (source_info.st_dev, source_info.st_ino) == (target_info.st_dev, target_info.st_ino)


def _available_bytes(path: Path) -> int:
    value = os.statvfs(path)
    return value.f_bavail * value.f_frsize


def _bind_mount(source: Path, target: Path, mount_command: str) -> None:
    try:
        completed = subprocess.run(
            [mount_command, "--bind", str(source), str(target)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=False,
            timeout=MOUNT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise GuardianError("bind_mount_timeout") from None
    if completed.returncode != 0:
        raise GuardianError("bind_mount_failed")


def _validate_roots(config: Config, *, create: bool) -> None:
    for path in (
        config.package,
        config.backing_root,
        config.guardian_lock,
        config.controller_lock,
        config.execution_lock,
        config.controller,
        config.preflight_receipt,
        config.gemini_canary_receipt,
        config.grok_canary_receipt,
        config.agy_executable,
        config.grok_executable,
    ):
        if path is None:
            continue
        _assert_absolute(path)
    _assert_no_symlink_components(config.package)
    _assert_no_symlink_components(config.backing_root)
    if not _non_overlapping(config.package, config.backing_root):
        raise GuardianError("runtime_path_overlap")
    if config.package.stat().st_dev == config.backing_root.stat().st_dev:
        raise GuardianError("backing_device_drift")
    lock_paths = (config.guardian_lock, config.controller_lock, config.execution_lock)
    if len(set(lock_paths)) != len(lock_paths):
        raise GuardianError("lock_path_collision")
    for lock_path in lock_paths:
        if not _non_overlapping(lock_path, config.package) or not _non_overlapping(
            lock_path, config.backing_root
        ):
            raise GuardianError("lock_path_collision")
        if create and not lock_path.parent.exists():
            _assert_no_symlink_components(lock_path.parent, allow_missing_leaf=True)
            lock_path.parent.mkdir(mode=0o700)
            os.chown(lock_path.parent, config.owner_uid, config.owner_gid)
        _assert_no_symlink_components(lock_path.parent)
        if lock_path.exists() or lock_path.is_symlink():
            info = lock_path.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                raise GuardianError("lock_path_drift")
    for root_name in OUTPUT_ROOTS:
        source = config.backing_root / root_name
        target = config.package / root_name
        if not _non_overlapping(source, target):
            raise GuardianError("runtime_path_overlap")
        _private_directory(source, config.owner_uid, config.owner_gid, create=create)
        _private_directory(target, config.owner_uid, config.owner_gid, create=create)


def _ensure_mounts(config: Config, *, mutate: bool) -> list[dict[str, Any]]:
    _validate_roots(config, create=mutate)
    entries = _mount_entries(config.mountinfo)
    result: list[dict[str, Any]] = []
    backing_devices: set[int] = set()
    for root_name in OUTPUT_ROOTS:
        source = config.backing_root / root_name
        target = config.package / root_name
        entry = _exact_mount(entries, target)
        if entry is None:
            if not mutate:
                raise GuardianError("storage_not_prepared")
            try:
                is_empty = not any(target.iterdir())
            except OSError:
                raise GuardianError("mount_target_unreadable") from None
            if not is_empty:
                raise GuardianError("mount_target_not_empty")
            _bind_mount(source, target, config.mount_command)
            entries = _mount_entries(config.mountinfo)
            entry = _exact_mount(entries, target)
            if entry is None:
                raise GuardianError("bind_mount_failed")
        if not _same_identity(source, target):
            raise GuardianError("mount_identity_drift")
        _private_directory(source, config.owner_uid, config.owner_gid, create=False)
        _private_directory(target, config.owner_uid, config.owner_gid, create=False)
        source_info = source.stat()
        backing_devices.add(source_info.st_dev)
        if source_info.st_dev == config.package.stat().st_dev:
            raise GuardianError("backing_device_drift")
        result.append(
            {
                "name": root_name,
                "identity_sha256": _digest(f"{source_info.st_dev}:{source_info.st_ino}".encode()),
            }
        )
    if len(backing_devices) != 1:
        raise GuardianError("backing_device_drift")
    return result


def _recover_guardian_temporaries(config: Config) -> int:
    recovery = config.backing_root / ".cycle007-guardian-recovery"
    candidates: list[Path] = []
    total_bytes = 0
    for root_name in OUTPUT_ROOTS:
        root = config.backing_root / root_name
        for candidate in root.rglob(".cycle007-guardian-tmp-*"):
            info = candidate.lstat()
            if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise GuardianError("ambiguous_partial_seal")
            candidates.append(candidate)
            total_bytes += info.st_size
    if len(candidates) > MAX_RECOVERY_FILES or total_bytes > MAX_RECOVERY_BYTES:
        raise GuardianError("recovery_bound_exceeded")
    if not candidates:
        return 0
    _private_directory(recovery, config.owner_uid, config.owner_gid, create=True)
    for index, candidate in enumerate(sorted(candidates)):
        if candidate.stat().st_dev != recovery.stat().st_dev:
            raise GuardianError("recovery_device_drift")
        destination = recovery / f"orphan-{index:03d}-{_digest(str(candidate).encode())[:16]}"
        if destination.exists() or destination.is_symlink():
            raise GuardianError("recovery_collision")
        os.replace(candidate, destination)
    _fsync_directory(recovery)
    return len(candidates)


def _lock(path: Path, failure_code: str) -> BinaryIO:
    _assert_absolute(path)
    _assert_no_symlink_components(path.parent, allow_missing_leaf=True)
    if not path.parent.exists():
        path.parent.mkdir(mode=0o700)
    _assert_no_symlink_components(path.parent)
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise GuardianError("lock_path_drift")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError:
        raise GuardianError("lock_path_drift") from None
    handle = os.fdopen(descriptor, "a+b")
    os.fchmod(handle.fileno(), 0o600)
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise GuardianError(failure_code) from None
    return handle


def _parse_controller_output(completed: subprocess.CompletedProcess[bytes]) -> dict[str, Any]:
    try:
        value = json.loads(completed.stdout.decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise GuardianError("controller_protocol_failure") from None
    if not isinstance(value, dict) or value.get("text_free") is not True:
        raise GuardianError("controller_protocol_failure")
    if completed.returncode != 0 or value.get("ok") is not True:
        code = value.get("failure_code")
        raise GuardianError(code if isinstance(code, str) and code else "controller_execution_failure")
    return value


def _controller_command(config: Config, action: str, stage: str | None = None) -> list[str]:
    _provider_bindings_complete(config, required=True)
    assert config.preflight_receipt is not None
    assert config.gemini_canary_receipt is not None
    assert config.grok_canary_receipt is not None
    assert config.agy_executable is not None
    assert config.grok_executable is not None
    command = [
        sys.executable,
        str(config.controller),
        action,
        "--package",
        str(config.package),
        "--lock",
        str(config.controller_lock),
        "--preflight-receipt",
        str(config.preflight_receipt),
        "--gemini-canary-receipt",
        str(config.gemini_canary_receipt),
        "--grok-canary-receipt",
        str(config.grok_canary_receipt),
        "--agy-executable",
        str(config.agy_executable),
        "--grok-executable",
        str(config.grok_executable),
    ]
    for label, path in sorted(config.code_paths.items()):
        command.extend(["--code-path", f"{label}={path}"])
    if stage is not None:
        command.extend(["--stage", stage])
        if stage != "gemini":
            label = f"{stage}_runner"
            runner = config.code_paths.get(label)
            if runner is None:
                raise GuardianError("stage_runner_required")
            command.extend(["--runner", str(runner)])
    if config.operator_inspected_count is not None:
        command.extend(["--operator-inspected-count", str(config.operator_inspected_count)])
    optional_paths = (
        ("--resolution-authorization", config.resolution_authorization),
        ("--resolution-authority-attestation", config.resolution_authority_attestation),
        ("--resolution-authority-root", config.resolution_authority_root),
        ("--resolution-nonce-ledger", config.resolution_nonce_ledger),
        ("--resolution-advisor-response", config.resolution_advisor_response),
    )
    for flag, path in optional_paths:
        if path is not None:
            command.extend([flag, str(path)])
    return command


def _invoke_controller(config: Config, action: str, *, execution_fd: int | None = None, stage: str | None = None) -> dict[str, Any]:
    environment = os.environ.copy()
    environment.pop(EXECUTION_LOCK_FD_ENV, None)
    pass_fds: tuple[int, ...] = ()
    if execution_fd is not None:
        environment[EXECUTION_LOCK_FD_ENV] = str(execution_fd)
        pass_fds = (execution_fd,)
    try:
        completed = subprocess.run(
            _controller_command(config, action, stage),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=False,
            env=environment,
            pass_fds=pass_fds,
            timeout=STATUS_TIMEOUT_SECONDS if action == "status" else STAGE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise GuardianError("controller_timeout") from None
    return _parse_controller_output(completed)


def _marker(config: Config, stage: str) -> Path:
    return config.package / "control" / f"guardian-{stage}.active.json"


def _stage_seal(config: Config, stage: str) -> Path:
    return config.package / "control" / f"stage-{stage}.complete.json"


def _reconcile_markers(config: Config, *, mutate: bool) -> None:
    for stage in MARKED_STAGES:
        marker = _marker(config, stage)
        if not marker.exists() and not marker.is_symlink():
            continue
        if marker.is_symlink() or not marker.is_file():
            raise GuardianError("ambiguous_provider_attempt")
        if _stage_seal(config, stage).is_file() and not _stage_seal(config, stage).is_symlink():
            if mutate:
                _remove_durable(marker)
            continue
        raise GuardianError("ambiguous_provider_attempt")


def _completed_stages(status: dict[str, Any]) -> list[str]:
    completed = status.get("completed_stages")
    if not isinstance(completed, list) or not all(item in STAGES for item in completed):
        raise GuardianError("controller_protocol_failure")
    if completed != list(STAGES[: len(completed)]):
        raise GuardianError("invalid_stage_seal")
    return completed


def _provider_bindings_complete(config: Config, *, required: bool) -> bool:
    values = (
        config.preflight_receipt,
        config.gemini_canary_receipt,
        config.grok_canary_receipt,
        config.agy_executable,
        config.grok_executable,
    )
    present = sum(value is not None for value in values)
    if present == 0:
        if required:
            raise GuardianError("provider_preflight_required")
        return False
    if present != len(values):
        raise GuardianError("provider_binding_incomplete")
    return True


def _require_lock_idle(path: Path, failure_code: str) -> None:
    if not path.exists() and not path.is_symlink():
        return
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise GuardianError("lock_path_drift")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    acquired = False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError:
            raise GuardianError(failure_code) from None
        finally:
            if acquired:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _fresh_provider_free_status(config: Config, *, mounts: list[dict[str, Any]]) -> dict[str, Any]:
    """Report the pristine pre-provider state without weakening the resume gate."""
    _require_lock_idle(config.controller_lock, "controller_already_running")
    _require_lock_idle(config.execution_lock, "active_worker")
    control = config.package / "control"
    state_paths = [
        *(control / f"stage-{stage}.complete.json" for stage in STAGES),
        *(control / f"guardian-{stage}.active.json" for stage in MARKED_STAGES),
        control / "preflight-receipt.json",
        control / "gemini-canary-receipt.json",
        control / "grok-canary-receipt.json",
    ]
    if any(path.exists() or path.is_symlink() for path in state_paths):
        raise GuardianError("provider_preflight_required")
    for root_name in OUTPUT_ROOTS:
        try:
            if any((config.backing_root / root_name).iterdir()):
                raise GuardianError("bootstrap_output_not_empty")
        except OSError:
            raise GuardianError("mount_target_unreadable") from None
    return {
        "schema_version": RECEIPT_SCHEMA,
        "ok": True,
        "action": config.action,
        "completed_stages": [],
        "next_stage": STAGES[0],
        "through": config.through,
        "mount_count": len(mounts),
        "mounts": mounts,
        "available_bytes": _available_bytes(config.backing_root),
        "min_free_bytes": config.min_free_bytes,
        "recovered_temporary_count": 0,
        "ready": False,
        "text_free": True,
    }


def _safe_status(config: Config, *, mounts: list[dict[str, Any]], recovered: int = 0) -> dict[str, Any]:
    controller = _invoke_controller(config, "status")
    completed = _completed_stages(controller)
    free_bytes = _available_bytes(config.backing_root)
    return {
        "schema_version": RECEIPT_SCHEMA,
        "ok": True,
        "action": config.action,
        "completed_stages": completed,
        "next_stage": STAGES[len(completed)] if len(completed) < len(STAGES) else None,
        "through": config.through,
        "mount_count": len(mounts),
        "mounts": mounts,
        "available_bytes": free_bytes,
        "min_free_bytes": config.min_free_bytes,
        "recovered_temporary_count": recovered,
        "ready": controller.get("ready") is True,
        "text_free": True,
    }


def _require_free_space(config: Config) -> int:
    available = _available_bytes(config.backing_root)
    if available < config.min_free_bytes:
        raise GuardianError("actual_disk_floor")
    return available


def _resume(config: Config, mounts: list[dict[str, Any]]) -> dict[str, Any]:
    if config.through is None:
        raise GuardianError("through_required")
    execution = _lock(config.execution_lock, "active_worker")
    try:
        execution_fd = execution.fileno()
        recovered = _recover_guardian_temporaries(config)
        _reconcile_markers(config, mutate=True)
        status = _invoke_controller(config, "status", execution_fd=execution_fd)
        completed = _completed_stages(status)
        boundary = STAGES.index(config.through)
        while len(completed) <= boundary:
            stage = STAGES[len(completed)]
            _require_free_space(config)
            marker = _marker(config, stage)
            if stage in MARKED_STAGES:
                _atomic_json(
                    marker,
                    {
                        "schema_version": "phase3_cycle007_active_stage_v1",
                        "stage": stage,
                        "text_free": True,
                    },
                )
            _invoke_controller(config, "run", execution_fd=execution_fd, stage=stage)
            if stage in MARKED_STAGES:
                if not _stage_seal(config, stage).is_file() or _stage_seal(config, stage).is_symlink():
                    raise GuardianError("ambiguous_provider_attempt")
                _remove_durable(marker)
            status = _invoke_controller(config, "status", execution_fd=execution_fd)
            completed = _completed_stages(status)
        result = _safe_status(config, mounts=mounts, recovered=recovered)
        result["available_bytes"] = _require_free_space(config)
        return result
    finally:
        execution.close()


def _parse_code_paths(items: Iterable[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for item in items:
        label, separator, raw_path = item.partition("=")
        if not separator or not label or not raw_path or label in result:
            raise GuardianError("invalid_code_binding")
        path = Path(raw_path)
        _assert_absolute(path, "invalid_code_binding")
        result[label] = path
    return result


def _config(args: argparse.Namespace) -> Config:
    return Config(
        action=args.action,
        package=args.package,
        backing_root=args.backing_root,
        guardian_lock=args.guardian_lock,
        controller_lock=args.controller_lock,
        execution_lock=args.execution_lock,
        controller=args.controller,
        preflight_receipt=args.preflight_receipt,
        gemini_canary_receipt=args.gemini_canary_receipt,
        grok_canary_receipt=args.grok_canary_receipt,
        agy_executable=args.agy_executable,
        grok_executable=args.grok_executable,
        code_paths=_parse_code_paths(args.code_path),
        owner_uid=args.owner_uid,
        owner_gid=args.owner_gid,
        min_free_bytes=args.min_free_bytes,
        through=args.through,
        receipt=args.receipt,
        mountinfo=args.mountinfo,
        mount_command=args.mount_command,
        operator_inspected_count=args.operator_inspected_count,
        resolution_authorization=args.resolution_authorization,
        resolution_authority_attestation=args.resolution_authority_attestation,
        resolution_authority_root=args.resolution_authority_root,
        resolution_nonce_ledger=args.resolution_nonce_ledger,
        resolution_advisor_response=args.resolution_advisor_response,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "status", "plan", "resume"))
    parser.add_argument("--package", type=Path, required=True, help="explicit Cycle 007 package path")
    parser.add_argument("--backing-root", type=Path, required=True, help="explicit separate-filesystem output root")
    parser.add_argument("--guardian-lock", type=Path, required=True, help="stable outer guardian lock")
    parser.add_argument("--controller-lock", type=Path, required=True, help="distinct stable controller lock")
    parser.add_argument("--execution-lock", type=Path, required=True, help="distinct inherited runner lock")
    parser.add_argument("--controller", type=Path, required=True, help="reviewed controller path")
    parser.add_argument("--preflight-receipt", type=Path, help="text-free reviewed preflight receipt")
    parser.add_argument("--gemini-canary-receipt", type=Path, help="text-free Gemini canary receipt")
    parser.add_argument("--grok-canary-receipt", type=Path, help="text-free Grok canary receipt")
    parser.add_argument("--agy-executable", type=Path, help="explicit reviewed AGY executable")
    parser.add_argument("--grok-executable", type=Path, help="explicit reviewed Grok executable")
    parser.add_argument("--code-path", action="append", default=[], help="LABEL=/absolute/public/code/path; repeat")
    parser.add_argument("--owner-uid", type=int, required=True, help="required output owner UID")
    parser.add_argument("--owner-gid", type=int, required=True, help="required output owner GID")
    parser.add_argument("--min-free-bytes", type=int, required=True, help="actual-free hard floor before every stage")
    parser.add_argument("--through", choices=STAGES, help="last stage the resume action may execute")
    parser.add_argument("--receipt", type=Path, help="optional external text-free guardian receipt")
    parser.add_argument("--mountinfo", type=Path, default=Path("/proc/self/mountinfo"), help=argparse.SUPPRESS)
    parser.add_argument("--mount-command", default="mount", help=argparse.SUPPRESS)
    parser.add_argument("--operator-inspected-count", type=int)
    parser.add_argument("--resolution-authorization", type=Path)
    parser.add_argument("--resolution-authority-attestation", type=Path)
    parser.add_argument("--resolution-authority-root", type=Path)
    parser.add_argument("--resolution-nonce-ledger", type=Path)
    parser.add_argument("--resolution-advisor-response", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result: dict[str, Any]
    config: Config | None = None
    guardian: BinaryIO | None = None
    try:
        config = _config(args)
        if config.owner_uid < 0 or config.owner_gid < 0 or config.min_free_bytes <= 0:
            raise GuardianError("invalid_runtime_parameter")
        provider_bindings = _provider_bindings_complete(config, required=config.action == "resume")
        guardian = _lock(config.guardian_lock, "guardian_already_running")
        mounts = _ensure_mounts(config, mutate=config.action in {"prepare", "resume"})
        _require_free_space(config)
        if config.action == "prepare":
            result = {
                "schema_version": RECEIPT_SCHEMA,
                "ok": True,
                "action": "prepare",
                "mount_count": len(mounts),
                "mounts": mounts,
                "available_bytes": _available_bytes(config.backing_root),
                "min_free_bytes": config.min_free_bytes,
                "text_free": True,
            }
        elif config.action in {"status", "plan"}:
            _reconcile_markers(config, mutate=False)
            result = (
                _safe_status(config, mounts=mounts)
                if provider_bindings
                else _fresh_provider_free_status(config, mounts=mounts)
            )
        else:
            result = _resume(config, mounts)
    except GuardianError as exc:
        result = {
            "schema_version": RECEIPT_SCHEMA,
            "ok": False,
            "failure_code": str(exc),
            "text_free": True,
        }
    except Exception:
        result = {
            "schema_version": RECEIPT_SCHEMA,
            "ok": False,
            "failure_code": "guardian_execution_failure",
            "text_free": True,
        }
    finally:
        if guardian is not None:
            guardian.close()
    if config is not None and config.receipt is not None:
        try:
            _atomic_json(config.receipt, result)
        except Exception:
            result = {
                "schema_version": RECEIPT_SCHEMA,
                "ok": False,
                "failure_code": "receipt_write_failed",
                "text_free": True,
            }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
