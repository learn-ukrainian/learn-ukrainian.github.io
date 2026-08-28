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
import re
import stat
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Sequence
from contextlib import ExitStack
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
GEMINI_RECOVERY_SCHEMA = "phase3_cycle007_gemini_provider_recovery_v1"
GEMINI_RECOVERY_RECEIPT = "provider-recovery.json"
GEMINI_SECOND_RECOVERY_SCHEMA = "phase3_cycle007_gemini_provider_second_recovery_v1"
GEMINI_SECOND_RECOVERY_RECEIPT = "provider-recovery-attempt-3.json"
GEMINI_STOP_RECOVERY_ROOT = ".cycle007-gemini-stop-recovery"
GEMINI_RECOVERABLE_FIRST_STOP_CODES = frozenset(
    {
        "structured_output_envelope_drift",
        "provider_status_quota_or_rate_limit",
        "provider_status_capacity_unavailable",
        "provider_status_timeout",
        "provider_status_cancelled",
        "provider_status_internal_error",
    }
)
GEMINI_RECOVERABLE_STOP_CODES = GEMINI_RECOVERABLE_FIRST_STOP_CODES
GEMINI_AUTOMATIC_RETRY_CODES = frozenset(
    {
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "ordinal_key_drift",
        "label_json_invalid",
        "label_count_or_envelope_drift",
    }
)
GEMINI_ATTEMPT_MARKER_RE = re.compile(
    r"^attempt-(?P<attempt>[1-9][0-9]*)-chunk-(?P<chunk>[0-9]+)\.(?P<state>started|terminal)\.json$"
)
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
    mount_command: tuple[str, ...]
    operator_inspected_count: int | None
    resolution_authorization: Path | None
    resolution_authority_attestation: Path | None
    resolution_authority_root: Path | None
    resolution_nonce_ledger: Path | None
    resolution_advisor_response: Path | None
    expected_stop_sha256: str | None


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


def _exclusive_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        raise GuardianError("stop_recovery_collision") from None
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(_canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        _fsync_directory(path.parent)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _private_json(
    path: Path,
    uid: int,
    gid: int,
    *,
    alternate_owner: tuple[int, int] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    _assert_no_symlink_components(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        raise GuardianError("stop_recovery_state_drift") from None
    allowed_owners = {(uid, gid)}
    if alternate_owner is not None:
        allowed_owners.add(alternate_owner)
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or stat.S_IMODE(info.st_mode) != 0o600
        or (info.st_uid, info.st_gid) not in allowed_owners
    ):
        raise GuardianError("stop_recovery_state_drift")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise GuardianError("stop_recovery_state_drift")
            result[key] = value
        return result

    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise GuardianError("stop_recovery_state_drift") from None
    if not isinstance(value, dict):
        raise GuardianError("stop_recovery_state_drift")
    return raw, value


def _canonical_private_json(
    path: Path,
    uid: int,
    gid: int,
    *,
    alternate_owner: tuple[int, int] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    try:
        raw, value = _private_json(
            path,
            uid,
            gid,
            alternate_owner=alternate_owner,
        )
    except GuardianError:
        raise GuardianError("ownership_repair_state_drift") from None
    if raw != _canonical(value) or value.get("text_free") is not True:
        raise GuardianError("ownership_repair_state_drift")
    return raw, value


def _require_runtime_owner_context(config: Config) -> None:
    if (os.geteuid(), os.getegid()) != (config.owner_uid, config.owner_gid):
        raise GuardianError("runtime_owner_context_mismatch")


def _require_owned_lock_file(path: Path, config: Config) -> None:
    _assert_no_symlink_components(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        raise GuardianError("ownership_repair_state_drift") from None
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or stat.S_IMODE(info.st_mode) != 0o600
        or (info.st_uid, info.st_gid) != (config.owner_uid, config.owner_gid)
    ):
        raise GuardianError("ownership_repair_state_drift")


def _durable_chown(path: Path, uid: int, gid: int) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        os.fchown(descriptor, uid, gid)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)


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


def _bind_mount(source: Path, target: Path, mount_command: tuple[str, ...]) -> None:
    _validate_mount_command(mount_command)
    try:
        completed = subprocess.run(
            [*mount_command, "--bind", str(source), str(target)],
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


def _validate_mount_command(mount_command: tuple[str, ...]) -> None:
    direct = len(mount_command) == 1 and Path(mount_command[0]).is_absolute()
    sudo = (
        len(mount_command) == 3
        and Path(mount_command[0]).is_absolute()
        and mount_command[1] == "-n"
        and Path(mount_command[2]).is_absolute()
    )
    if any(not part or "\0" in part for part in mount_command) or not (direct or sudo):
        raise GuardianError("invalid_mount_command")


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


def _prepare(config: Config, mounts: list[dict[str, Any]], *, provider_bindings: bool) -> dict[str, Any]:
    preflight_ready = False
    if provider_bindings:
        execution = _lock(config.execution_lock, "active_worker")
        try:
            _invoke_controller(config, "preflight", execution_fd=execution.fileno())
            preflight_ready = True
        finally:
            execution.close()
    return {
        "schema_version": RECEIPT_SCHEMA,
        "ok": True,
        "action": "prepare",
        "mount_count": len(mounts),
        "mounts": mounts,
        "available_bytes": _available_bytes(config.backing_root),
        "min_free_bytes": config.min_free_bytes,
        "preflight_ready": preflight_ready,
        "text_free": True,
    }


def _repair_runtime_ownership(
    config: Config,
    mounts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Repair only an exact privileged-write incident without invoking a provider."""
    expected_stop = config.expected_stop_sha256
    if (
        os.geteuid() != 0
        or not isinstance(expected_stop, str)
        or len(expected_stop) != 64
        or any(character not in "0123456789abcdef" for character in expected_stop)
    ):
        raise GuardianError("ownership_repair_not_authorized")
    assert config.preflight_receipt is not None
    assert config.gemini_canary_receipt is not None
    assert config.grok_canary_receipt is not None
    privileged_owner = (os.geteuid(), os.getegid())
    expected_owner = (config.owner_uid, config.owner_gid)
    for lock_path in (
        config.guardian_lock,
        config.controller_lock,
        config.execution_lock,
    ):
        _require_owned_lock_file(lock_path, config)

    with ExitStack() as locks:
        locks.enter_context(_lock(config.execution_lock, "active_worker"))
        locks.enter_context(_lock(config.controller_lock, "controller_already_running"))
        control = config.package / "control"
        _private_directory(control, config.owner_uid, config.owner_gid, create=False)
        state_paths = [
            *(control / f"stage-{stage}.complete.json" for stage in STAGES),
            *(control / f"guardian-{stage}.active.json" for stage in MARKED_STAGES),
        ]
        if any(path.exists() or path.is_symlink() for path in state_paths):
            raise GuardianError("ownership_repair_state_drift")

        candidates: list[tuple[Path, bytes]] = []
        receipt_pairs = (
            (control / "preflight-receipt.json", config.preflight_receipt),
            (control / "gemini-canary-receipt.json", config.gemini_canary_receipt),
            (control / "grok-canary-receipt.json", config.grok_canary_receipt),
        )
        for installed_path, source_path in receipt_pairs:
            source_raw, _source = _canonical_private_json(
                source_path,
                config.owner_uid,
                config.owner_gid,
                alternate_owner=privileged_owner,
            )
            installed_raw, _installed = _canonical_private_json(
                installed_path,
                config.owner_uid,
                config.owner_gid,
                alternate_owner=privileged_owner,
            )
            if installed_raw != source_raw:
                raise GuardianError("ownership_repair_identity_drift")
            candidates.append((installed_path, installed_raw))

        output = config.backing_root / OUTPUT_ROOTS[0]
        _private_directory(output, config.owner_uid, config.owner_gid, create=False)
        stop_path = output / "provider-stop.json"
        stop_raw, stop = _canonical_private_json(
            stop_path,
            config.owner_uid,
            config.owner_gid,
            alternate_owner=privileged_owner,
        )
        if _digest(stop_raw) != expected_stop:
            raise GuardianError("ownership_repair_identity_drift")
        _validate_gemini_stop(stop)
        if stop.get("schema_version") != "phase3_cycle007_gemini_provider_stop_v2":
            raise GuardianError("ownership_repair_state_drift")
        attempt_root, chunk_index, attempt = _stopped_attempt_coordinates(
            config,
            output,
            stop,
            alternate_owner=privileged_owner,
        )
        started_path = attempt_root / f"attempt-{attempt}-chunk-{chunk_index:02d}.started.json"
        terminal_path = attempt_root / f"attempt-{attempt}-chunk-{chunk_index:02d}.terminal.json"
        started_raw, _started = _canonical_private_json(
            started_path,
            config.owner_uid,
            config.owner_gid,
            alternate_owner=privileged_owner,
        )
        terminal_raw, _terminal = _canonical_private_json(
            terminal_path,
            config.owner_uid,
            config.owner_gid,
            alternate_owner=privileged_owner,
        )
        if stop.get("terminal_marker_sha256") != _digest(terminal_raw):
            raise GuardianError("ownership_repair_identity_drift")
        candidates.extend(
            (
                (stop_path, stop_raw),
                (started_path, started_raw),
                (terminal_path, terminal_raw),
            )
        )

        repaired = 0
        for path, raw in candidates:
            info = path.lstat()
            owner = (info.st_uid, info.st_gid)
            if owner not in {expected_owner, privileged_owner}:
                raise GuardianError("ownership_repair_state_drift")
            if owner != expected_owner:
                _durable_chown(path, config.owner_uid, config.owner_gid)
                repaired += 1
            verified_raw, _verified = _canonical_private_json(
                path,
                config.owner_uid,
                config.owner_gid,
            )
            if verified_raw != raw:
                raise GuardianError("ownership_repair_identity_drift")
        return {
            "schema_version": RECEIPT_SCHEMA,
            "ok": True,
            "action": "repair-runtime-ownership",
            "mount_count": len(mounts),
            "mounts": mounts,
            "available_bytes": _available_bytes(config.backing_root),
            "min_free_bytes": config.min_free_bytes,
            "validated_file_count": len(candidates),
            "repaired_file_count": repaired,
            "provider_call_count": 0,
            "text_free": True,
        }
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


def _archive_exact_stop(
    config: Config,
    *,
    stop_path: Path,
    expected_stop: str,
) -> None:
    archive_root = config.backing_root / GEMINI_STOP_RECOVERY_ROOT
    _private_directory(archive_root, config.owner_uid, config.owner_gid, create=True)
    _fsync_directory(config.backing_root)
    archive = archive_root / expected_stop
    _private_directory(archive, config.owner_uid, config.owner_gid, create=True)
    _fsync_directory(archive_root)
    archived_stop = archive / "provider-stop.json"
    if archived_stop.exists() or archived_stop.is_symlink():
        archived_raw, _archived = _private_json(
            archived_stop, config.owner_uid, config.owner_gid
        )
        if _digest(archived_raw) != expected_stop:
            raise GuardianError("stop_recovery_collision")
        return
    try:
        os.link(stop_path, archived_stop, follow_symlinks=False)
    except OSError:
        raise GuardianError("stop_recovery_archive_failed") from None
    _fsync_directory(archive)


def _hex_digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _attempt_marker_coordinates(path: Path) -> tuple[int, int, str]:
    match = GEMINI_ATTEMPT_MARKER_RE.fullmatch(path.name)
    if match is None:
        raise GuardianError("stop_recovery_state_drift")
    return int(match["attempt"]), int(match["chunk"]), match["state"]


def _gemini_attempt_pair(
    config: Config,
    attempt_root: Path,
    *,
    lane: str,
    packet_index: int,
    chunk_index: int,
    attempt: int,
    alternate_owner: tuple[int, int] | None = None,
) -> tuple[bytes, dict[str, Any], bytes, dict[str, Any]]:
    terminal_path = attempt_root / f"attempt-{attempt}-chunk-{chunk_index:02d}.terminal.json"
    started_path = terminal_path.with_name(
        f"attempt-{attempt}-chunk-{chunk_index:02d}.started.json"
    )
    terminal_raw, terminal = _private_json(
        terminal_path,
        config.owner_uid,
        config.owner_gid,
        alternate_owner=alternate_owner,
    )
    started_raw, started = _private_json(
        started_path,
        config.owner_uid,
        config.owner_gid,
        alternate_owner=alternate_owner,
    )
    common = {
        "schema_version": "phase3_cycle007_gemini_attempt_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": lane,
        "packet_index": packet_index,
        "chunk_index": chunk_index,
        "attempt": attempt,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
    }
    if any(started.get(key) != value for key, value in common.items()) or (
        set(started) != set(common) | {"state"} or started.get("state") != "started"
    ):
        raise GuardianError("stop_recovery_state_drift")
    provider_call_started = terminal.get("provider_call_started")
    pre_call_failure = (
        provider_call_started is False
        and attempt == 1
        and terminal.get("failure_code") in GEMINI_AUTOMATIC_RETRY_CODES
        and terminal.get("failure_stage") == "executable_binding"
        and terminal.get("executable_binding_result") == "mismatch"
        and terminal.get("provider_return_code") == "not_started"
        and terminal.get("raw_byte_count") == 0
        and terminal.get("raw_sha256") == _digest(b"")
        and terminal.get("log_byte_count") == 0
        and terminal.get("log_sha256") == _digest(b"")
        and terminal.get("init_count") == 0
        and terminal.get("result_count") == 0
        and terminal.get("first_event_kind") == "unavailable"
        and terminal.get("last_event_kind") == "unavailable"
        and terminal.get("model_binding_result") == "not_inspected"
        and terminal.get("result_status") == "not_inspected"
        and terminal.get("structured_output_type") == "not_inspected"
    )
    provider_failure = (
        provider_call_started is True
        and terminal.get("executable_binding_result") in {"verified", "synthetic"}
        and terminal.get("provider_return_code") in {"zero", "nonzero"}
    )
    if (
        any(terminal.get(key) != value for key, value in common.items())
        or terminal.get("state") != "terminal"
        or terminal.get("failure_code")
        not in GEMINI_AUTOMATIC_RETRY_CODES | GEMINI_RECOVERABLE_STOP_CODES
        or terminal.get("failure_stage")
        not in {
            "package_binding",
            "executable_binding",
            "provider_return",
            "stream_parse",
            "result_validation",
        }
        or not (pre_call_failure or provider_failure)
        or not isinstance(terminal.get("raw_byte_count"), int)
        or terminal.get("raw_byte_count", -1) < 0
        or not _hex_digest(terminal.get("raw_sha256"))
        or not isinstance(terminal.get("log_byte_count"), int)
        or terminal.get("log_byte_count", -1) < 0
        or not _hex_digest(terminal.get("log_sha256"))
        or not isinstance(terminal.get("init_count"), int)
        or not 0 <= terminal.get("init_count", -1) <= 255
        or not isinstance(terminal.get("result_count"), int)
        or not 0 <= terminal.get("result_count", -1) <= 255
        or terminal.get("first_event_kind")
        not in {"empty", "init", "result", "other", "unavailable"}
        or terminal.get("last_event_kind")
        not in {"empty", "init", "result", "other", "unavailable"}
        or terminal.get("model_binding_result")
        not in {"not_inspected", "verified", "mismatch", "missing"}
        or terminal.get("result_status")
        not in {"not_inspected", "success", "non_success", "missing"}
        or terminal.get("structured_output_type")
        not in {"not_inspected", "missing", "object", "string", "null", "other"}
    ):
        raise GuardianError("stop_recovery_state_drift")
    terminal_fields = set(common) | {
        "state",
        "failure_code",
        "failure_stage",
        "provider_call_started",
        "executable_binding_result",
        "provider_return_code",
        "raw_byte_count",
        "raw_sha256",
        "log_byte_count",
        "log_sha256",
        "init_count",
        "result_count",
        "first_event_kind",
        "last_event_kind",
        "model_binding_result",
        "result_status",
        "structured_output_type",
    }
    if set(terminal) != terminal_fields:
        raise GuardianError("stop_recovery_state_drift")
    return started_raw, started, terminal_raw, terminal


def _legacy_recovery_path(
    output: Path,
    attempt_root: Path,
    *,
    lane: str,
    packet_index: int,
    chunk_index: int,
    authorized_attempt: int,
) -> Path | None:
    if (
        lane != "clean_label"
        or packet_index != 1
        or chunk_index != 1
        or attempt_root != output / "clean_label/chunks/packet-0001"
    ):
        return None
    if authorized_attempt == 2:
        return output / GEMINI_RECOVERY_RECEIPT
    if authorized_attempt == 3:
        return output / GEMINI_SECOND_RECOVERY_RECEIPT
    return None


def _recovery_path_candidates(
    output: Path,
    attempt_root: Path,
    *,
    lane: str,
    packet_index: int,
    chunk_index: int,
    authorized_attempt: int,
) -> tuple[Path, ...]:
    local = attempt_root / (
        f"provider-recovery-chunk-{chunk_index:02d}-attempt-{authorized_attempt}.json"
    )
    legacy = _legacy_recovery_path(
        output,
        attempt_root,
        lane=lane,
        packet_index=packet_index,
        chunk_index=chunk_index,
        authorized_attempt=authorized_attempt,
    )
    return (local,) if legacy is None else (legacy, local)


def _existing_recovery_path(
    output: Path,
    attempt_root: Path,
    *,
    lane: str,
    packet_index: int,
    chunk_index: int,
    authorized_attempt: int,
) -> Path | None:
    paths = [
        path
        for path in _recovery_path_candidates(
            output,
            attempt_root,
            lane=lane,
            packet_index=packet_index,
            chunk_index=chunk_index,
            authorized_attempt=authorized_attempt,
        )
        if path.exists() or path.is_symlink()
    ]
    if len(paths) > 1:
        raise GuardianError("stop_recovery_collision")
    return paths[0] if paths else None


def _verified_recovery_receipt(
    config: Config,
    path: Path,
    *,
    started_raw: bytes,
    terminal_raw: bytes,
    terminal: dict[str, Any],
    authorized_attempt: int,
    prior_recovery_raw: bytes | None,
    prior_provider_call_count: int | None,
) -> tuple[bytes, dict[str, Any]]:
    recovery_raw, recovery = _private_json(path, config.owner_uid, config.owner_gid)
    call_count = recovery.get("prior_provider_call_count")
    body = {
        "schema_version": (
            GEMINI_RECOVERY_SCHEMA
            if prior_recovery_raw is None
            else GEMINI_SECOND_RECOVERY_SCHEMA
        ),
        "evaluation_cycle_id": terminal["evaluation_cycle_id"],
        "source_provider_stop_sha256": recovery.get("source_provider_stop_sha256"),
        "started_marker_sha256": _digest(started_raw),
        "terminal_marker_sha256": _digest(terminal_raw),
        "failure_code": terminal["failure_code"],
        "failure_stage": terminal["failure_stage"],
        "prior_provider_call_count": call_count,
        "authorized_additional_provider_calls": 1,
        "exact_model": terminal["exact_model"],
        "model_family": terminal["model_family"],
        "harness": terminal["harness"],
        "text_free": True,
    }
    if prior_recovery_raw is not None:
        body |= {
            "prior_recovery_receipt_sha256": _digest(prior_recovery_raw),
            "authorized_attempt": authorized_attempt,
        }
    if (
        not _hex_digest(body["source_provider_stop_sha256"])
        or not isinstance(call_count, int)
        or isinstance(call_count, bool)
        or call_count < 1
        or (
            prior_provider_call_count is not None
            and call_count != prior_provider_call_count + 1
        )
        or set(recovery) != set(body) | {"receipt_sha256"}
        or any(recovery.get(key) != value for key, value in body.items())
        or recovery.get("receipt_sha256") != _digest(_canonical(body))
        or _digest(recovery_raw) != _digest(_canonical(recovery))
    ):
        raise GuardianError("stop_recovery_state_drift")
    archive_root = config.backing_root / GEMINI_STOP_RECOVERY_ROOT
    archive = archive_root / str(body["source_provider_stop_sha256"])
    _private_directory(archive_root, config.owner_uid, config.owner_gid, create=False)
    _private_directory(archive, config.owner_uid, config.owner_gid, create=False)
    archived_raw, _archived = _private_json(
        archive / "provider-stop.json", config.owner_uid, config.owner_gid
    )
    if _digest(archived_raw) != body["source_provider_stop_sha256"]:
        raise GuardianError("stop_recovery_binding_drift")
    return recovery_raw, recovery


def _attempt_chain(
    config: Config,
    output: Path,
    attempt_root: Path,
    *,
    lane: str,
    packet_index: int,
    chunk_index: int,
    terminal_attempt: int,
) -> tuple[
    list[tuple[bytes, dict[str, Any], bytes, dict[str, Any]]],
    bytes | None,
    int | None,
]:
    observed: dict[tuple[int, str], Path] = {}
    for path in attempt_root.iterdir():
        match = GEMINI_ATTEMPT_MARKER_RE.fullmatch(path.name)
        if match is None or int(match["chunk"]) != chunk_index:
            continue
        key = (int(match["attempt"]), match["state"])
        if key in observed or path.is_symlink():
            raise GuardianError("stop_recovery_state_drift")
        observed[key] = path
    attempts = sorted({attempt for attempt, _state in observed})
    if attempts != list(range(1, len(attempts) + 1)) or terminal_attempt != len(attempts):
        raise GuardianError("stop_recovery_state_drift")
    expected = {
        (attempt, state)
        for attempt in attempts
        for state in ("started", "terminal")
    }
    if set(observed) != expected:
        raise GuardianError("stop_recovery_state_drift")

    pairs = []
    prior_recovery_raw: bytes | None = None
    prior_provider_call_count: int | None = None
    for attempt in attempts:
        pair = _gemini_attempt_pair(
            config,
            attempt_root,
            lane=lane,
            packet_index=packet_index,
            chunk_index=chunk_index,
            attempt=attempt,
        )
        pairs.append(pair)
        if attempt == terminal_attempt:
            continue
        terminal = pair[3]
        recovery_path = _existing_recovery_path(
            output,
            attempt_root,
            lane=lane,
            packet_index=packet_index,
            chunk_index=chunk_index,
            authorized_attempt=attempt + 1,
        )
        if (
            attempt == 1
            and terminal["failure_code"] in GEMINI_AUTOMATIC_RETRY_CODES
            and recovery_path is None
        ):
            continue
        if recovery_path is None:
            raise GuardianError("stop_recovery_state_drift")
        prior_recovery_raw, recovery = _verified_recovery_receipt(
            config,
            recovery_path,
            started_raw=pair[0],
            terminal_raw=pair[2],
            terminal=terminal,
            authorized_attempt=attempt + 1,
            prior_recovery_raw=prior_recovery_raw,
            prior_provider_call_count=prior_provider_call_count,
        )
        prior_provider_call_count = recovery["prior_provider_call_count"]
    return pairs, prior_recovery_raw, prior_provider_call_count


def _stop_projection(stop: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in stop.items()
        if key
        not in {
            "schema_version",
            "terminal_packet_index",
            "new_provider_calls_allowed",
            "chunk_index",
            "attempt",
            "terminal_marker_sha256",
        }
    }


def _terminal_projection(terminal: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in terminal.items()
        if key not in {"schema_version", "state", "packet_index", "chunk_index", "attempt"}
    }


def _stopped_attempt_coordinates(
    config: Config,
    output: Path,
    stop: dict[str, Any],
    *,
    alternate_owner: tuple[int, int] | None = None,
) -> tuple[Path, int, int]:
    lane = stop.get("lane")
    packet_index = stop.get("terminal_packet_index")
    if lane not in {"clean_label", "residual_label"} or not isinstance(
        packet_index, int
    ) or isinstance(packet_index, bool) or packet_index < 1:
        raise GuardianError("stop_recovery_state_drift")
    attempt_root = output / lane / "chunks" / f"packet-{packet_index:04d}"
    _private_directory(attempt_root, config.owner_uid, config.owner_gid, create=False)

    chunk_attempts: dict[int, set[int]] = {}
    for path in attempt_root.iterdir():
        match = GEMINI_ATTEMPT_MARKER_RE.fullmatch(path.name)
        if match is None:
            continue
        if path.is_symlink():
            raise GuardianError("stop_recovery_state_drift")
        chunk_index = int(match["chunk"])
        chunk_attempts.setdefault(chunk_index, set()).add(int(match["attempt"]))
    uncommitted: list[int] = []
    for chunk_index in sorted(chunk_attempts):
        labels = attempt_root / f"labels-chunk-{chunk_index:02d}.json"
        receipt = attempt_root / f"receipt-chunk-{chunk_index:02d}.json"
        labels_exists = labels.exists() or labels.is_symlink()
        receipt_exists = receipt.exists() or receipt.is_symlink()
        if labels_exists != receipt_exists or labels.is_symlink() or receipt.is_symlink():
            raise GuardianError("stop_recovery_state_drift")
        if not labels_exists:
            uncommitted.append(chunk_index)
    if len(uncommitted) != 1:
        raise GuardianError("stop_recovery_state_drift")
    chunk_index = uncommitted[0]
    attempts = sorted(chunk_attempts[chunk_index])
    if attempts != list(range(1, len(attempts) + 1)):
        raise GuardianError("stop_recovery_state_drift")
    terminal_attempt = len(attempts)
    terminal_path = (
        attempt_root / f"attempt-{terminal_attempt}-chunk-{chunk_index:02d}.terminal.json"
    )
    if not terminal_path.exists() or terminal_path.is_symlink():
        raise GuardianError("stop_recovery_state_drift")
    _started_raw, _started, _terminal_raw, terminal = _gemini_attempt_pair(
        config,
        attempt_root,
        lane=lane,
        packet_index=packet_index,
        chunk_index=chunk_index,
        attempt=terminal_attempt,
        alternate_owner=alternate_owner,
    )
    if _terminal_projection(terminal) != _stop_projection(stop):
        raise GuardianError("stop_recovery_state_drift")
    if stop["schema_version"] == "phase3_cycle007_gemini_provider_stop_v2":
        if (
            stop.get("chunk_index") != chunk_index
            or stop.get("attempt") != terminal_attempt
            or stop.get("terminal_marker_sha256") != _digest(_terminal_raw)
        ):
            raise GuardianError("stop_recovery_binding_drift")
    elif not (
        lane == "clean_label"
        and packet_index == 1
        and chunk_index == 1
        and terminal_attempt <= 3
    ):
        raise GuardianError("stop_recovery_binding_drift")
    return attempt_root, chunk_index, terminal_attempt


def _provider_call_count(config: Config, output: Path) -> int:
    count = 0
    successful_attempts: dict[tuple[Path, int], int] = {}
    for receipt_path in output.rglob("receipt-chunk-*.json"):
        if receipt_path.is_symlink():
            raise GuardianError("stop_recovery_state_drift")
        _raw, receipt = _private_json(
            receipt_path, config.owner_uid, config.owner_gid
        )
        attempt_count = receipt.get("attempt_count")
        chunk_text = receipt_path.stem.removeprefix("receipt-chunk-")
        if (
            receipt.get("schema_version") != "phase3_cycle007_gemini_chunk_receipt_v1"
            or receipt.get("text_free") is not True
            or not chunk_text.isdigit()
            or not isinstance(attempt_count, int)
            or isinstance(attempt_count, bool)
            or attempt_count < 1
        ):
            raise GuardianError("stop_recovery_state_drift")
        labels_path = receipt_path.with_name(f"labels-chunk-{int(chunk_text):02d}.json")
        try:
            _assert_no_symlink_components(labels_path)
            labels_info = labels_path.lstat()
        except (GuardianError, OSError):
            raise GuardianError("stop_recovery_state_drift") from None
        if (
            not stat.S_ISREG(labels_info.st_mode)
            or stat.S_IMODE(labels_info.st_mode) != 0o600
            or labels_info.st_uid != config.owner_uid
            or labels_info.st_gid != config.owner_gid
        ):
            raise GuardianError("stop_recovery_state_drift")
        key = (receipt_path.parent, int(chunk_text))
        if key in successful_attempts:
            raise GuardianError("stop_recovery_state_drift")
        successful_attempts[key] = attempt_count
        count += 1

    terminals: set[tuple[Path, int, int]] = set()
    for terminal_path in output.rglob("attempt-*-chunk-*.terminal.json"):
        if terminal_path.is_symlink():
            raise GuardianError("stop_recovery_state_drift")
        attempt, chunk_index, state = _attempt_marker_coordinates(terminal_path)
        if state != "terminal":
            raise GuardianError("stop_recovery_state_drift")
        _raw, terminal = _private_json(
            terminal_path, config.owner_uid, config.owner_gid
        )
        key = (terminal_path.parent, chunk_index, attempt)
        if (
            key in terminals
            or terminal.get("schema_version") != "phase3_cycle007_gemini_attempt_v1"
            or terminal.get("state") != "terminal"
            or terminal.get("text_free") is not True
            or (
                terminal.get("provider_call_started") is not True
                and terminal.get("provider_call_started") is not False
            )
        ):
            raise GuardianError("stop_recovery_state_drift")
        terminals.add(key)
        if terminal["provider_call_started"] is True:
            count += 1

    started_attempts: set[tuple[Path, int, int]] = set()
    for started_path in output.rglob("attempt-*-chunk-*.started.json"):
        if started_path.is_symlink():
            raise GuardianError("stop_recovery_state_drift")
        attempt, chunk_index, state = _attempt_marker_coordinates(started_path)
        if state != "started":
            raise GuardianError("stop_recovery_state_drift")
        terminal_key = (started_path.parent, chunk_index, attempt)
        if terminal_key in started_attempts:
            raise GuardianError("stop_recovery_state_drift")
        started_attempts.add(terminal_key)
        success_attempt = successful_attempts.get((started_path.parent, chunk_index))
        if terminal_key not in terminals and success_attempt != attempt:
            raise GuardianError("stop_recovery_state_drift")
    if any(
        (parent, chunk_index, attempt) not in started_attempts
        for (parent, chunk_index), attempt in successful_attempts.items()
    ):
        raise GuardianError("stop_recovery_state_drift")
    if not terminals.issubset(started_attempts):
        raise GuardianError("stop_recovery_state_drift")
    return count


def _validate_gemini_stop(stop: dict[str, Any]) -> None:
    lane = stop.get("lane")
    packet_index = stop.get("terminal_packet_index")
    if (
        stop.get("schema_version")
        not in {
            "phase3_cycle007_gemini_provider_stop_v1",
            "phase3_cycle007_gemini_provider_stop_v2",
        }
        or stop.get("evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-007"
        or lane not in {"clean_label", "residual_label"}
        or not isinstance(packet_index, int)
        or isinstance(packet_index, bool)
        or packet_index < 1
        or stop.get("failure_code") not in GEMINI_RECOVERABLE_STOP_CODES
        or stop.get("failure_stage") != "provider_return"
        or stop.get("provider_call_started") is not True
        or stop.get("new_provider_calls_allowed") is not False
        or stop.get("exact_model") != "Gemini 3.6 Flash (High)"
        or stop.get("model_family") != "google"
        or stop.get("harness") != "agy"
        or stop.get("text_free") is not True
    ):
        raise GuardianError("stop_recovery_state_drift")
    base_fields = {
        "schema_version",
        "evaluation_cycle_id",
        "lane",
        "terminal_packet_index",
        "failure_code",
        "new_provider_calls_allowed",
        "exact_model",
        "model_family",
        "harness",
        "text_free",
        "failure_stage",
        "provider_call_started",
        "executable_binding_result",
        "provider_return_code",
        "raw_byte_count",
        "raw_sha256",
        "log_byte_count",
        "log_sha256",
        "init_count",
        "result_count",
        "first_event_kind",
        "last_event_kind",
        "model_binding_result",
        "result_status",
        "structured_output_type",
    }
    occurrence_fields = {"chunk_index", "attempt", "terminal_marker_sha256"}
    if set(stop) != base_fields | (
        occurrence_fields
        if stop["schema_version"] == "phase3_cycle007_gemini_provider_stop_v2"
        else set()
    ):
        raise GuardianError("stop_recovery_state_drift")


def _validate_pre_call_chain_stop(stop: dict[str, Any]) -> None:
    """Accept only the exact content-free stop emitted before a new attempt starts."""
    lane = stop.get("lane")
    packet_index = stop.get("terminal_packet_index")
    empty_sha256 = _digest(b"")
    expected = {
        "schema_version": "phase3_cycle007_gemini_provider_stop_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": lane,
        "terminal_packet_index": packet_index,
        "failure_code": "ordinal_identity_binding_drift",
        "new_provider_calls_allowed": False,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
        "failure_stage": "package_binding",
        "provider_call_started": False,
        "executable_binding_result": "not_checked",
        "provider_return_code": "not_started",
        "raw_byte_count": 0,
        "raw_sha256": empty_sha256,
        "log_byte_count": 0,
        "log_sha256": empty_sha256,
        "init_count": 0,
        "result_count": 0,
        "first_event_kind": "unavailable",
        "last_event_kind": "unavailable",
        "model_binding_result": "not_inspected",
        "result_status": "not_inspected",
        "structured_output_type": "not_inspected",
    }
    if (
        lane not in {"clean_label", "residual_label"}
        or not isinstance(packet_index, int)
        or isinstance(packet_index, bool)
        or packet_index < 1
        or stop != expected
    ):
        raise GuardianError("stop_recovery_state_drift")


def _existing_unstarted_authorization(
    config: Config,
    output: Path,
    stop: dict[str, Any],
) -> tuple[int, int]:
    """Return the sole marker-bound authorization whose attempt has not started."""
    lane = str(stop["lane"])
    packet_index = int(stop["terminal_packet_index"])
    attempt_root = output / lane / "chunks" / f"packet-{packet_index:04d}"
    _private_directory(attempt_root, config.owner_uid, config.owner_gid, create=False)

    chunk_attempts: dict[int, set[int]] = {}
    for path in attempt_root.iterdir():
        match = GEMINI_ATTEMPT_MARKER_RE.fullmatch(path.name)
        if match is None:
            continue
        if path.is_symlink():
            raise GuardianError("stop_recovery_state_drift")
        chunk_attempts.setdefault(int(match["chunk"]), set()).add(int(match["attempt"]))

    candidates: list[tuple[int, int]] = []
    for chunk_index, attempts in sorted(chunk_attempts.items()):
        terminal_attempt = max(attempts)
        pairs, prior_recovery_raw, prior_provider_call_count = _attempt_chain(
            config,
            output,
            attempt_root,
            lane=lane,
            packet_index=packet_index,
            chunk_index=chunk_index,
            terminal_attempt=terminal_attempt,
        )
        authorized_attempt = terminal_attempt + 1
        next_markers = [
            attempt_root
            / f"attempt-{authorized_attempt}-chunk-{chunk_index:02d}.{state}.json"
            for state in ("started", "terminal")
        ]
        if any(path.exists() or path.is_symlink() for path in next_markers):
            raise GuardianError("stop_recovery_state_drift")
        recovery_path = _existing_recovery_path(
            output,
            attempt_root,
            lane=lane,
            packet_index=packet_index,
            chunk_index=chunk_index,
            authorized_attempt=authorized_attempt,
        )
        if recovery_path is None:
            continue
        committed = [
            attempt_root / f"{prefix}-chunk-{chunk_index:02d}.json"
            for prefix in ("labels", "receipt")
        ]
        if any(path.exists() or path.is_symlink() for path in committed):
            raise GuardianError("stop_recovery_state_drift")
        started_raw, _started, terminal_raw, terminal = pairs[-1]
        _recovery_raw, receipt = _verified_recovery_receipt(
            config,
            recovery_path,
            started_raw=started_raw,
            terminal_raw=terminal_raw,
            terminal=terminal,
            authorized_attempt=authorized_attempt,
            prior_recovery_raw=prior_recovery_raw,
            prior_provider_call_count=prior_provider_call_count,
        )
        provider_call_count = _provider_call_count(config, output)
        if provider_call_count != receipt.get("prior_provider_call_count"):
            raise GuardianError("stop_recovery_state_drift")
        candidates.append((authorized_attempt, provider_call_count))
    if len(candidates) != 1:
        raise GuardianError("stop_recovery_state_drift")
    return candidates[0]


def _reuse_pre_call_authorization(
    config: Config,
    mounts: list[dict[str, Any]],
    *,
    output: Path,
    expected_stop: str,
    stop_raw: bytes,
    stop: dict[str, Any],
    stop_path: Path | None,
) -> dict[str, Any]:
    """Archive one exact pre-call stop without consuming or widening authorization."""
    if _digest(stop_raw) != expected_stop:
        raise GuardianError("stop_recovery_binding_drift")
    _validate_pre_call_chain_stop(stop)
    authorized_attempt, provider_call_count = _existing_unstarted_authorization(
        config, output, stop
    )
    if stop_path is not None:
        _archive_exact_stop(config, stop_path=stop_path, expected_stop=expected_stop)
        _remove_durable(stop_path)
    if _provider_call_count(config, output) != provider_call_count:
        raise GuardianError("stop_recovery_state_drift")
    return {
        "schema_version": RECEIPT_SCHEMA,
        "ok": True,
        "action": "recover-gemini-stop",
        "mount_count": len(mounts),
        "mounts": mounts,
        "available_bytes": _available_bytes(config.backing_root),
        "min_free_bytes": config.min_free_bytes,
        "prior_provider_call_count": provider_call_count,
        "authorized_additional_provider_calls": 1,
        "authorized_attempt": authorized_attempt,
        "recovered_stop_count": 1,
        "reused_existing_authorization": True,
        "text_free": True,
    }


def _idempotent_recovery(
    config: Config,
    mounts: list[dict[str, Any]],
    *,
    output: Path,
    expected_stop: str,
) -> dict[str, Any]:
    archive_root = config.backing_root / GEMINI_STOP_RECOVERY_ROOT
    archive = archive_root / expected_stop
    _private_directory(archive_root, config.owner_uid, config.owner_gid, create=False)
    _private_directory(archive, config.owner_uid, config.owner_gid, create=False)
    archived_raw, archived = _private_json(
        archive / "provider-stop.json", config.owner_uid, config.owner_gid
    )
    if _digest(archived_raw) != expected_stop:
        raise GuardianError("stop_recovery_binding_drift")
    if archived.get("failure_code") == "ordinal_identity_binding_drift":
        return _reuse_pre_call_authorization(
            config,
            mounts,
            output=output,
            expected_stop=expected_stop,
            stop_raw=archived_raw,
            stop=archived,
            stop_path=None,
        )
    _validate_gemini_stop(archived)
    attempt_root, chunk_index, terminal_attempt = _stopped_attempt_coordinates(
        config, output, archived
    )
    pairs, prior_recovery_raw, prior_provider_call_count = _attempt_chain(
        config,
        output,
        attempt_root,
        lane=archived["lane"],
        packet_index=archived["terminal_packet_index"],
        chunk_index=chunk_index,
        terminal_attempt=terminal_attempt,
    )
    authorized_attempt = terminal_attempt + 1
    path = _existing_recovery_path(
        output,
        attempt_root,
        lane=archived["lane"],
        packet_index=archived["terminal_packet_index"],
        chunk_index=chunk_index,
        authorized_attempt=authorized_attempt,
    )
    if path is None:
        raise GuardianError("stop_recovery_state_drift")
    started_raw, _started, terminal_raw, terminal = pairs[-1]
    _recovery_raw, receipt = _verified_recovery_receipt(
        config,
        path,
        started_raw=started_raw,
        terminal_raw=terminal_raw,
        terminal=terminal,
        authorized_attempt=authorized_attempt,
        prior_recovery_raw=prior_recovery_raw,
        prior_provider_call_count=prior_provider_call_count,
    )
    if (
        receipt.get("source_provider_stop_sha256") != expected_stop
        or _provider_call_count(config, output)
        != receipt.get("prior_provider_call_count")
    ):
        raise GuardianError("stop_recovery_state_drift")
    return {
        "schema_version": RECEIPT_SCHEMA,
        "ok": True,
        "action": "recover-gemini-stop",
        "mount_count": len(mounts),
        "mounts": mounts,
        "available_bytes": _available_bytes(config.backing_root),
        "min_free_bytes": config.min_free_bytes,
        "prior_provider_call_count": receipt["prior_provider_call_count"],
        "authorized_additional_provider_calls": 1,
        "authorized_attempt": authorized_attempt,
        "recovered_stop_count": 1,
        "text_free": True,
    }


def _gemini_stop_recovery(config: Config, mounts: list[dict[str, Any]]) -> dict[str, Any]:
    """Preserve one exact stopped call and authorize exactly one next attempt."""
    expected_stop = config.expected_stop_sha256
    if (
        not isinstance(expected_stop, str)
        or len(expected_stop) != 64
        or any(character not in "0123456789abcdef" for character in expected_stop)
    ):
        raise GuardianError("expected_stop_sha256_required")

    execution = _lock(config.execution_lock, "active_worker")
    try:
        status = _invoke_controller(config, "status", execution_fd=execution.fileno())
        if _completed_stages(status):
            raise GuardianError("stop_recovery_state_drift")

        output = config.backing_root / OUTPUT_ROOTS[0]
        _private_directory(output, config.owner_uid, config.owner_gid, create=False)
        stop_path = output / "provider-stop.json"
        if not stop_path.exists() and not stop_path.is_symlink():
            if status.get("stopped") is not False:
                raise GuardianError("stop_recovery_state_drift")
            return _idempotent_recovery(
                config, mounts, output=output, expected_stop=expected_stop
            )
        if status.get("stopped") is not True:
            raise GuardianError("stop_recovery_state_drift")
        stop_raw, stop = _private_json(stop_path, config.owner_uid, config.owner_gid)
        if _digest(stop_raw) != expected_stop:
            raise GuardianError("stop_recovery_binding_drift")
        if stop.get("failure_code") == "ordinal_identity_binding_drift":
            return _reuse_pre_call_authorization(
                config,
                mounts,
                output=output,
                expected_stop=expected_stop,
                stop_raw=stop_raw,
                stop=stop,
                stop_path=stop_path,
            )
        _validate_gemini_stop(stop)
        lane = stop["lane"]
        packet_index = stop["terminal_packet_index"]
        attempt_root, chunk_index, terminal_attempt = _stopped_attempt_coordinates(
            config, output, stop
        )
        pairs, prior_recovery_raw, _prior_provider_call_count = _attempt_chain(
            config,
            output,
            attempt_root,
            lane=str(lane),
            packet_index=packet_index,
            chunk_index=chunk_index,
            terminal_attempt=terminal_attempt,
        )
        started_raw, _started, terminal_raw, terminal = pairs[-1]
        authorized_attempt = terminal_attempt + 1
        receipt_path = _recovery_path_candidates(
            output,
            attempt_root,
            lane=str(lane),
            packet_index=packet_index,
            chunk_index=chunk_index,
            authorized_attempt=authorized_attempt,
        )[0]
        existing_path = _existing_recovery_path(
            output,
            attempt_root,
            lane=str(lane),
            packet_index=packet_index,
            chunk_index=chunk_index,
            authorized_attempt=authorized_attempt,
        )
        if existing_path is not None:
            receipt_path = existing_path

        _archive_exact_stop(config, stop_path=stop_path, expected_stop=expected_stop)
        provider_call_count = _provider_call_count(config, output)
        receipt_body: dict[str, Any] = {
            "schema_version": (
                GEMINI_RECOVERY_SCHEMA
                if prior_recovery_raw is None
                else GEMINI_SECOND_RECOVERY_SCHEMA
            ),
            "evaluation_cycle_id": terminal["evaluation_cycle_id"],
            "source_provider_stop_sha256": expected_stop,
            "started_marker_sha256": _digest(started_raw),
            "terminal_marker_sha256": _digest(terminal_raw),
            "failure_code": terminal["failure_code"],
            "failure_stage": terminal["failure_stage"],
            "prior_provider_call_count": provider_call_count,
            "authorized_additional_provider_calls": 1,
            "exact_model": terminal["exact_model"],
            "model_family": terminal["model_family"],
            "harness": terminal["harness"],
            "text_free": True,
        }
        if prior_recovery_raw is not None:
            receipt_body |= {
                "prior_recovery_receipt_sha256": _digest(prior_recovery_raw),
                "authorized_attempt": authorized_attempt,
            }
        receipt = receipt_body | {"receipt_sha256": _digest(_canonical(receipt_body))}
        if receipt_path.exists() or receipt_path.is_symlink():
            existing_raw, existing = _private_json(
                receipt_path, config.owner_uid, config.owner_gid
            )
            if existing != receipt or _digest(existing_raw) != _digest(_canonical(receipt)):
                raise GuardianError("stop_recovery_collision")
        else:
            _exclusive_json(receipt_path, receipt)
        if stop_path.exists():
            _remove_durable(stop_path)

        return {
            "schema_version": RECEIPT_SCHEMA,
            "ok": True,
            "action": "recover-gemini-stop",
            "mount_count": len(mounts),
            "mounts": mounts,
            "available_bytes": _available_bytes(config.backing_root),
            "min_free_bytes": config.min_free_bytes,
            "prior_provider_call_count": provider_call_count,
            "authorized_additional_provider_calls": 1,
            "authorized_attempt": authorized_attempt,
            "recovered_stop_count": 1,
            "text_free": True,
        }
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
    mount_command = (
        (str(args.sudo_command), "-n", str(args.mount_command))
        if args.sudo_command is not None
        else (str(args.mount_command),)
    )
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
        mount_command=mount_command,
        operator_inspected_count=args.operator_inspected_count,
        resolution_authorization=args.resolution_authorization,
        resolution_authority_attestation=args.resolution_authority_attestation,
        resolution_authority_root=args.resolution_authority_root,
        resolution_nonce_ledger=args.resolution_nonce_ledger,
        resolution_advisor_response=args.resolution_advisor_response,
        expected_stop_sha256=args.expected_stop_sha256,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "prepare",
            "status",
            "plan",
            "repair-runtime-ownership",
            "recover-gemini-stop",
            "resume",
        ),
    )
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
    parser.add_argument("--mount-command", type=Path, default=Path("mount"), help=argparse.SUPPRESS)
    parser.add_argument("--sudo-command", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--operator-inspected-count", type=int)
    parser.add_argument("--resolution-authorization", type=Path)
    parser.add_argument("--resolution-authority-attestation", type=Path)
    parser.add_argument("--resolution-authority-root", type=Path)
    parser.add_argument("--resolution-nonce-ledger", type=Path)
    parser.add_argument("--resolution-advisor-response", type=Path)
    parser.add_argument(
        "--expected-stop-sha256",
        help="exact stopped Gemini receipt SHA-256; required for recovery or ownership repair",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result: dict[str, Any]
    config: Config | None = None
    guardian: BinaryIO | None = None
    receipt_allowed = False
    try:
        config = _config(args)
        if config.owner_uid < 0 or config.owner_gid < 0 or config.min_free_bytes <= 0:
            raise GuardianError("invalid_runtime_parameter")
        repair_ownership = config.action == "repair-runtime-ownership"
        if repair_ownership:
            if config.receipt is not None:
                raise GuardianError("ownership_repair_not_authorized")
            _require_owned_lock_file(config.guardian_lock, config)
        else:
            _require_runtime_owner_context(config)
            receipt_allowed = True
        provider_bindings = _provider_bindings_complete(
            config,
            required=config.action
            in {"repair-runtime-ownership", "recover-gemini-stop", "resume"},
        )
        if config.action in {"prepare", "recover-gemini-stop", "resume"}:
            _validate_mount_command(config.mount_command)
        guardian = _lock(config.guardian_lock, "guardian_already_running")
        mounts = _ensure_mounts(
            config, mutate=config.action in {"prepare", "recover-gemini-stop", "resume"}
        )
        _require_free_space(config)
        if config.action == "prepare":
            result = _prepare(config, mounts, provider_bindings=provider_bindings)
        elif config.action in {"status", "plan"}:
            _reconcile_markers(config, mutate=False)
            result = (
                _safe_status(config, mounts=mounts)
                if provider_bindings
                else _fresh_provider_free_status(config, mounts=mounts)
            )
        elif config.action == "repair-runtime-ownership":
            result = _repair_runtime_ownership(config, mounts)
        elif config.action == "recover-gemini-stop":
            result = _gemini_stop_recovery(config, mounts)
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
    if config is not None and receipt_allowed and config.receipt is not None:
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
