from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import venv
from dataclasses import replace
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUARDIAN_PATH = ROOT / "scripts/projects/open_model_data/phase3_cycle007_labeling_guardian.py"
CONTROLLER_PATH = ROOT / "batch_state/phase3-run-cycle007-controller-v1.py"


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _temporary_file() -> Any:
    return tempfile.TemporaryFile()


def _signed_receipt(controller: ModuleType, **values: Any) -> dict[str, Any]:
    receipt = dict(values)
    receipt["receipt_sha256"] = controller.digest(controller.canonical(receipt))
    return receipt


@pytest.fixture()
def guardian() -> ModuleType:
    return _load(GUARDIAN_PATH, "cycle007_labeling_guardian_test")


@pytest.fixture()
def controller() -> ModuleType:
    return _load(CONTROLLER_PATH, "cycle007_controller_fd_test")


def _config(guardian: ModuleType, root: Path, **changes: Any) -> Any:
    package = root / "package"
    backing = root / "backing"
    package.mkdir(mode=0o700)
    backing.mkdir(mode=0o700)
    values = {
        "action": "resume",
        "package": package,
        "backing_root": backing,
        "guardian_lock": root / "locks/guardian.lock",
        "controller_lock": root / "locks/controller.lock",
        "execution_lock": root / "locks/execution.lock",
        "controller": root / "controller.py",
        "preflight_receipt": root / "preflight.json",
        "gemini_canary_receipt": root / "gemini.json",
        "grok_canary_receipt": root / "grok.json",
        "agy_executable": root / "agy",
        "grok_executable": root / "grok",
        "code_paths": {},
        "owner_uid": os.getuid(),
        "owner_gid": os.getgid(),
        "min_free_bytes": 1,
        "through": "gemini",
        "receipt": None,
        "mountinfo": root / "mountinfo",
        "mount_command": ("/usr/bin/mount",),
        "operator_inspected_count": None,
        "resolution_authorization": None,
        "resolution_authority_attestation": None,
        "resolution_authority_root": None,
        "resolution_nonce_ledger": None,
        "resolution_advisor_response": None,
        "expected_stop_sha256": None,
    }
    values.update(changes)
    return guardian.Config(**values)


def test_mountinfo_parser_decodes_and_matches_exact_target(guardian: ModuleType, tmp_path: Path) -> None:
    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text(
        "42 31 8:2 /backing\\040root /package/output\\040root rw - ext4 /dev/test rw\n",
        encoding="utf-8",
    )
    entries = guardian._mount_entries(mountinfo)
    assert entries == [
        guardian.MountEntry(
            mount_point=Path("/package/output root"),
            root="/backing root",
            source="/dev/test",
            device="8:2",
        )
    ]
    assert guardian._exact_mount(entries, Path("/package/output")) is None
    assert guardian._exact_mount(entries, Path("/package/output root")) == entries[0]


def test_mountinfo_duplicate_exact_target_fails_closed(guardian: ModuleType) -> None:
    entry = guardian.MountEntry(Path("/target"), "/", "/dev/test", "8:2")
    with pytest.raises(guardian.GuardianError, match="mount_identity_drift"):
        guardian._exact_mount([entry, entry], Path("/target"))


def test_no_symlink_component_and_overlap_rejected(guardian: ModuleType, tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(guardian.GuardianError, match="runtime_path_symlink"):
        guardian._assert_no_symlink_components(link)
    assert guardian._non_overlapping(tmp_path / "one", tmp_path / "two")
    assert not guardian._non_overlapping(tmp_path / "one", tmp_path / "one/child")


def test_actual_free_uses_bavail_not_bfree(guardian: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "statvfs", lambda _path: SimpleNamespace(f_bavail=7, f_bfree=99, f_frsize=4096))
    assert guardian._available_bytes(Path("/unused")) == 7 * 4096


def test_permission_drift_is_rejected(guardian: ModuleType, tmp_path: Path) -> None:
    directory = tmp_path / "output"
    directory.mkdir(mode=0o600)
    os.chmod(directory, 0o600)
    with pytest.raises(guardian.GuardianError, match="runtime_permission_drift"):
        guardian._private_directory(directory, os.getuid(), os.getgid(), create=False)


def test_package_and_backing_on_same_device_are_rejected(guardian: ModuleType, tmp_path: Path) -> None:
    config = _config(guardian, tmp_path)
    config.guardian_lock.parent.mkdir(mode=0o700)
    with pytest.raises(guardian.GuardianError, match="backing_device_drift"):
        guardian._validate_roots(config, create=False)


def test_lock_path_collision_is_rejected(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = tmp_path / "overlap-case"
    case.mkdir()
    config = _config(
        guardian,
        case,
        guardian_lock=(case / "package/guardian.lock"),
    )
    config.controller_lock.parent.mkdir(mode=0o700)
    real_stat = guardian.Path.stat

    def fake_stat(path: Path, *args: Any, **kwargs: Any) -> Any:
        value = real_stat(path, *args, **kwargs)
        if path == config.package:
            fields = list(value)
            fields[2] = 1
            return os.stat_result(fields)
        if path == config.backing_root:
            fields = list(value)
            fields[2] = 2
            return os.stat_result(fields)
        return value

    monkeypatch.setattr(guardian.Path, "stat", fake_stat)
    with pytest.raises(guardian.GuardianError, match="lock_path_collision"):
        guardian._validate_roots(config, create=False)


def test_actual_free_floor_is_enforced(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, min_free_bytes=101)
    monkeypatch.setattr(guardian, "_available_bytes", lambda _path: 100)
    with pytest.raises(guardian.GuardianError, match="actual_disk_floor"):
        guardian._require_free_space(config)


def test_nonempty_unmounted_target_is_rejected_before_mount(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path)
    for name in guardian.OUTPUT_ROOTS:
        (config.backing_root / name).mkdir(mode=0o700)
        (config.package / name).mkdir(mode=0o700)
    (config.package / guardian.OUTPUT_ROOTS[0] / "existing").write_text("", encoding="utf-8")
    monkeypatch.setattr(guardian, "_validate_roots", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(guardian, "_mount_entries", lambda _path: [])
    monkeypatch.setattr(guardian, "_bind_mount", lambda *_args: pytest.fail("mount command invoked"))
    with pytest.raises(guardian.GuardianError, match="mount_target_not_empty"):
        guardian._ensure_mounts(config, mutate=True)


def test_correct_existing_mounts_are_idempotent(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path)
    for name in guardian.OUTPUT_ROOTS:
        (config.backing_root / name).mkdir(mode=0o700)
        (config.package / name).mkdir(mode=0o700)
    entries = [
        guardian.MountEntry(config.package / name, f"/{name}", "/dev/test", "8:2")
        for name in guardian.OUTPUT_ROOTS
    ]
    real_stat = guardian.Path.stat

    def fake_stat(path: Path, *args: Any, **kwargs: Any) -> Any:
        value = real_stat(path, *args, **kwargs)
        if path == config.package:
            fields = list(value)
            fields[2] = 1
            return os.stat_result(fields)
        if path.parent == config.backing_root or path.parent == config.package:
            fields = list(value)
            fields[1] = hash(path.name) & 0xFFFF
            fields[2] = 2
            return os.stat_result(fields)
        return value

    monkeypatch.setattr(guardian, "_validate_roots", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(guardian, "_mount_entries", lambda _path: entries)
    monkeypatch.setattr(guardian, "_same_identity", lambda _source, _target: True)
    monkeypatch.setattr(guardian.Path, "stat", fake_stat)
    monkeypatch.setattr(guardian, "_private_directory", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(guardian, "_bind_mount", lambda *_args: pytest.fail("mount command invoked"))
    mounts = guardian._ensure_mounts(config, mutate=True)
    assert len(mounts) == len(guardian.OUTPUT_ROOTS)
    assert all(set(mount) == {"name", "identity_sha256"} for mount in mounts)


def test_orphan_guardian_temporary_is_quarantined_without_reading(
    guardian: ModuleType, tmp_path: Path
) -> None:
    config = _config(guardian, tmp_path)
    for name in guardian.OUTPUT_ROOTS:
        (config.backing_root / name).mkdir(mode=0o700)
    orphan = config.backing_root / guardian.OUTPUT_ROOTS[0] / ".cycle007-guardian-tmp-receipt.dead"
    orphan.write_bytes(b"opaque")
    assert guardian._recover_guardian_temporaries(config) == 1
    assert not orphan.exists()
    recovery = config.backing_root / ".cycle007-guardian-recovery"
    assert len(list(recovery.iterdir())) == 1


def _write_private_json(path: Path, value: dict[str, Any]) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(raw)
    os.chmod(path, 0o600)
    return raw


def _seed_second_gemini_timeout(
    guardian: ModuleType, config: Any
) -> tuple[Path, str, bytes]:
    output = config.backing_root / guardian.OUTPUT_ROOTS[0]
    attempt_root = output / "clean_label/chunks/packet-0001"
    attempt_root.mkdir(parents=True, mode=0o700)
    for directory in (
        output,
        output / "clean_label",
        output / "clean_label/chunks",
        attempt_root,
    ):
        os.chmod(directory, 0o700)
    common = {
        "schema_version": "phase3_cycle007_gemini_attempt_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": "clean_label",
        "packet_index": 1,
        "chunk_index": 1,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
    }
    terminal_common = {
        "state": "terminal",
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "provider_call_started": True,
        "executable_binding_result": "verified",
        "provider_return_code": "nonzero",
        "raw_byte_count": 1,
        "raw_sha256": "0" * 64,
        "log_byte_count": 1,
        "init_count": 1,
        "result_count": 1,
        "first_event_kind": "init",
        "last_event_kind": "result",
        "model_binding_result": "verified",
        "result_status": "non_success",
        "structured_output_type": "missing",
    }
    first_started_raw = _write_private_json(
        attempt_root / "attempt-1-chunk-01.started.json",
        common | {"attempt": 1, "state": "started"},
    )
    first_terminal = common | {"attempt": 1} | terminal_common | {"log_sha256": "1" * 64}
    first_terminal_raw = _write_private_json(
        attempt_root / "attempt-1-chunk-01.terminal.json", first_terminal
    )
    first_stop = {
        **{
            key: first_terminal[key]
            for key in first_terminal
            if key not in {"schema_version", "state", "packet_index", "chunk_index", "attempt"}
        },
        "schema_version": "phase3_cycle007_gemini_provider_stop_v1",
        "terminal_packet_index": 1,
        "new_provider_calls_allowed": False,
    }
    first_stop_raw = guardian._canonical(first_stop)
    first_stop_sha = guardian._digest(first_stop_raw)
    first_archive = (
        config.backing_root
        / guardian.GEMINI_STOP_RECOVERY_ROOT
        / first_stop_sha
        / "provider-stop.json"
    )
    _write_private_json(first_archive, first_stop)
    for directory in (first_archive.parent.parent, first_archive.parent):
        os.chmod(directory, 0o700)
    first_body = {
        "schema_version": guardian.GEMINI_RECOVERY_SCHEMA,
        "evaluation_cycle_id": common["evaluation_cycle_id"],
        "source_provider_stop_sha256": first_stop_sha,
        "started_marker_sha256": guardian._digest(first_started_raw),
        "terminal_marker_sha256": guardian._digest(first_terminal_raw),
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "prior_provider_call_count": 1,
        "authorized_additional_provider_calls": 1,
        "exact_model": common["exact_model"],
        "model_family": common["model_family"],
        "harness": common["harness"],
        "text_free": True,
    }
    first_receipt = first_body | {
        "receipt_sha256": guardian._digest(guardian._canonical(first_body))
    }
    first_recovery_raw = _write_private_json(
        output / guardian.GEMINI_RECOVERY_RECEIPT, first_receipt
    )

    _write_private_json(
        attempt_root / "attempt-2-chunk-01.started.json",
        common | {"attempt": 2, "state": "started"},
    )
    second_terminal = common | {"attempt": 2} | terminal_common | {"log_sha256": "2" * 64}
    _write_private_json(attempt_root / "attempt-2-chunk-01.terminal.json", second_terminal)
    second_stop = {
        **{
            key: second_terminal[key]
            for key in second_terminal
            if key not in {"schema_version", "state", "packet_index", "chunk_index", "attempt"}
        },
        "schema_version": "phase3_cycle007_gemini_provider_stop_v1",
        "terminal_packet_index": 1,
        "new_provider_calls_allowed": False,
    }
    second_stop_raw = _write_private_json(output / "provider-stop.json", second_stop)
    return output, guardian._digest(second_stop_raw), first_recovery_raw


@pytest.mark.parametrize(
    "failure_code",
    ["structured_output_envelope_drift", "provider_status_quota_or_rate_limit"],
)
def test_explicit_gemini_stop_recovery_preserves_stop_and_authorizes_one_call(
    guardian: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_code: str,
) -> None:
    config = _config(
        guardian,
        tmp_path,
        action="recover-gemini-stop",
        expected_stop_sha256="0" * 64,
    )
    output = config.backing_root / guardian.OUTPUT_ROOTS[0]
    attempt = output / "clean_label/chunks/packet-0001"
    attempt.mkdir(parents=True, mode=0o700)
    for directory in (output, output / "clean_label", output / "clean_label/chunks", attempt):
        os.chmod(directory, 0o700)
    common = {
        "schema_version": "phase3_cycle007_gemini_attempt_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": "clean_label",
        "packet_index": 1,
        "chunk_index": 1,
        "attempt": 1,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
    }
    started_raw = _write_private_json(
        attempt / "attempt-1-chunk-01.started.json", common | {"state": "started"}
    )
    terminal = common | {
        "state": "terminal",
        "failure_code": failure_code,
        "failure_stage": "provider_return",
        "provider_call_started": True,
        "executable_binding_result": "verified",
        "provider_return_code": "nonzero",
        "raw_byte_count": 1,
        "raw_sha256": "0" * 64,
        "log_byte_count": 1,
        "log_sha256": "1" * 64,
        "init_count": 1,
        "result_count": 1,
        "first_event_kind": "init",
        "last_event_kind": "result",
        "model_binding_result": "verified",
        "result_status": "non_success",
        "structured_output_type": "missing",
    }
    terminal_raw = _write_private_json(attempt / "attempt-1-chunk-01.terminal.json", terminal)
    stop = {
        **{key: terminal[key] for key in terminal if key not in {"schema_version", "state", "packet_index", "chunk_index", "attempt"}},
        "schema_version": "phase3_cycle007_gemini_provider_stop_v1",
        "terminal_packet_index": 1,
        "new_provider_calls_allowed": False,
    }
    stop_raw = _write_private_json(output / "provider-stop.json", stop)
    stop_sha = guardian._digest(stop_raw)
    config = replace(config, expected_stop_sha256=stop_sha)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: {
            "ok": True,
            "stopped": (output / "provider-stop.json").exists(),
            "completed_stages": [],
            "text_free": True,
        },
    )
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 123)

    result = guardian._gemini_stop_recovery(config, mounts=[])
    assert result["authorized_additional_provider_calls"] == 1
    assert result["prior_provider_call_count"] == 1
    assert not (output / "provider-stop.json").exists()
    receipt_path = output / guardian.GEMINI_RECOVERY_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["source_provider_stop_sha256"] == stop_sha
    assert receipt["started_marker_sha256"] == guardian._digest(started_raw)
    assert receipt["terminal_marker_sha256"] == guardian._digest(terminal_raw)
    archived = tmp_path / "backing" / guardian.GEMINI_STOP_RECOVERY_ROOT / stop_sha / "provider-stop.json"
    assert guardian._digest(archived.read_bytes()) == stop_sha
    assert guardian._gemini_stop_recovery(config, mounts=[])["recovered_stop_count"] == 1


def test_explicit_gemini_stop_recovery_refuses_unbound_stop(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(
        guardian,
        tmp_path,
        action="recover-gemini-stop",
        expected_stop_sha256="0" * 64,
    )
    output = config.backing_root / guardian.OUTPUT_ROOTS[0]
    output.mkdir(mode=0o700)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: {"stopped": True, "completed_stages": []},
    )
    with pytest.raises(guardian.GuardianError, match="stop_recovery_state_drift"):
        guardian._gemini_stop_recovery(config, mounts=[])


def test_exact_second_gemini_timeout_recovery_chains_receipt_and_is_idempotent(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output, stop_sha, first_recovery_raw = _seed_second_gemini_timeout(guardian, config)
    config = replace(config, expected_stop_sha256=stop_sha)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: {
            "stopped": (output / "provider-stop.json").exists(),
            "completed_stages": [],
        },
    )
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 123)

    result = guardian._gemini_stop_recovery(config, mounts=[])
    assert result["prior_provider_call_count"] == 2
    assert result["authorized_additional_provider_calls"] == 1
    assert result["authorized_attempt"] == 3
    assert not (output / "provider-stop.json").exists()
    receipt_path = output / guardian.GEMINI_SECOND_RECOVERY_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["source_provider_stop_sha256"] == stop_sha
    assert receipt["prior_recovery_receipt_sha256"] == guardian._digest(first_recovery_raw)
    assert receipt["authorized_attempt"] == 3
    archived = (
        config.backing_root
        / guardian.GEMINI_STOP_RECOVERY_ROOT
        / stop_sha
        / "provider-stop.json"
    )
    assert guardian._digest(archived.read_bytes()) == stop_sha
    assert guardian._gemini_stop_recovery(config, mounts=[])["authorized_attempt"] == 3


def test_exact_third_timeout_authorizes_attempt_four_and_survives_restart(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output, second_stop_sha, _first_recovery_raw = _seed_second_gemini_timeout(
        guardian, config
    )
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: {
            "stopped": (output / "provider-stop.json").exists(),
            "completed_stages": [],
        },
    )
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 123)
    config = replace(config, expected_stop_sha256=second_stop_sha)
    guardian._gemini_stop_recovery(config, mounts=[])

    attempt_root = output / "clean_label/chunks/packet-0001"
    common = {
        "schema_version": "phase3_cycle007_gemini_attempt_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": "clean_label",
        "packet_index": 1,
        "chunk_index": 1,
        "attempt": 3,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
    }
    _write_private_json(
        attempt_root / "attempt-3-chunk-01.started.json",
        common | {"state": "started"},
    )
    terminal = common | {
        "state": "terminal",
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "provider_call_started": True,
        "executable_binding_result": "verified",
        "provider_return_code": "nonzero",
        "raw_byte_count": 1,
        "raw_sha256": "3" * 64,
        "log_byte_count": 1,
        "log_sha256": "4" * 64,
        "init_count": 1,
        "result_count": 1,
        "first_event_kind": "init",
        "last_event_kind": "result",
        "model_binding_result": "verified",
        "result_status": "non_success",
        "structured_output_type": "missing",
    }
    _write_private_json(attempt_root / "attempt-3-chunk-01.terminal.json", terminal)
    stop = {
        **{
            key: value
            for key, value in terminal.items()
            if key not in {"schema_version", "state", "packet_index", "chunk_index", "attempt"}
        },
        "schema_version": "phase3_cycle007_gemini_provider_stop_v1",
        "terminal_packet_index": 1,
        "new_provider_calls_allowed": False,
    }
    stop_raw = _write_private_json(output / "provider-stop.json", stop)
    third_stop_sha = guardian._digest(stop_raw)
    config = replace(config, expected_stop_sha256=third_stop_sha)

    result = guardian._gemini_stop_recovery(config, mounts=[])
    assert result["prior_provider_call_count"] == 3
    assert result["authorized_additional_provider_calls"] == 1
    assert result["authorized_attempt"] == 4
    receipt_path = attempt_root / "provider-recovery-chunk-01-attempt-4.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["authorized_attempt"] == 4
    assert receipt["source_provider_stop_sha256"] == third_stop_sha
    assert receipt["prior_recovery_receipt_sha256"] == guardian._digest(
        (output / guardian.GEMINI_SECOND_RECOVERY_RECEIPT).read_bytes()
    )
    assert guardian._gemini_stop_recovery(config, mounts=[])["authorized_attempt"] == 4


def test_recovery_after_committed_progress_is_content_blind_and_chunk_local(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output = config.backing_root / guardian.OUTPUT_ROOTS[0]
    prior_root = output / "clean_label/chunks/packet-0001"
    prior_root.mkdir(parents=True, mode=0o700)
    for directory in (output, output / "clean_label", output / "clean_label/chunks", prior_root):
        os.chmod(directory, 0o700)
    _write_private_json(
        prior_root / "attempt-1-chunk-01.started.json", {"text_free": True}
    )
    opaque = prior_root / "labels-chunk-01.json"
    opaque.write_bytes(b"opaque-committed-content")
    opaque.chmod(0o600)
    _write_private_json(
        prior_root / "receipt-chunk-01.json",
        {
            "schema_version": "phase3_cycle007_gemini_chunk_receipt_v1",
            "attempt_count": 1,
            "text_free": True,
        },
    )

    attempt_root = output / "clean_label/chunks/packet-0002"
    attempt_root.mkdir(mode=0o700)
    common = {
        "schema_version": "phase3_cycle007_gemini_attempt_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": "clean_label",
        "packet_index": 2,
        "chunk_index": 1,
        "attempt": 1,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
    }
    _write_private_json(
        attempt_root / "attempt-1-chunk-01.started.json", common | {"state": "started"}
    )
    terminal = common | {
        "state": "terminal",
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "provider_call_started": True,
        "executable_binding_result": "verified",
        "provider_return_code": "nonzero",
        "raw_byte_count": 1,
        "raw_sha256": "5" * 64,
        "log_byte_count": 1,
        "log_sha256": "6" * 64,
        "init_count": 1,
        "result_count": 1,
        "first_event_kind": "init",
        "last_event_kind": "result",
        "model_binding_result": "verified",
        "result_status": "non_success",
        "structured_output_type": "missing",
    }
    terminal_raw = _write_private_json(
        attempt_root / "attempt-1-chunk-01.terminal.json", terminal
    )
    stop = {
        **{
            key: value
            for key, value in terminal.items()
            if key not in {"schema_version", "state", "packet_index", "chunk_index", "attempt"}
        },
        "schema_version": "phase3_cycle007_gemini_provider_stop_v2",
        "terminal_packet_index": 2,
        "new_provider_calls_allowed": False,
        "chunk_index": 1,
        "attempt": 1,
        "terminal_marker_sha256": guardian._digest(terminal_raw),
    }
    stop_raw = _write_private_json(output / "provider-stop.json", stop)
    config = replace(config, expected_stop_sha256=guardian._digest(stop_raw))
    original_private_json = guardian._private_json

    def guarded_private_json(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == opaque:
            pytest.fail("committed label content was inspected")
        return original_private_json(path, *args, **kwargs)

    monkeypatch.setattr(guardian, "_private_json", guarded_private_json)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: {
            "stopped": (output / "provider-stop.json").exists(),
            "completed_stages": [],
        },
    )
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 123)

    result = guardian._gemini_stop_recovery(config, mounts=[])
    assert result["prior_provider_call_count"] == 2
    assert result["authorized_attempt"] == 2
    assert (
        attempt_root / "provider-recovery-chunk-01-attempt-2.json"
    ).is_file()
    assert opaque.read_bytes() == b"opaque-committed-content"


def test_recovery_paths_are_chunk_scoped_after_legacy_attempts(
    guardian: ModuleType, tmp_path: Path
) -> None:
    output = tmp_path / "output"
    attempt_root = output / "clean_label/chunks/packet-0002"
    first = guardian._recovery_path_candidates(
        output,
        attempt_root,
        lane="clean_label",
        packet_index=2,
        chunk_index=1,
        authorized_attempt=2,
    )
    second = guardian._recovery_path_candidates(
        output,
        attempt_root,
        lane="clean_label",
        packet_index=2,
        chunk_index=2,
        authorized_attempt=2,
    )
    assert first != second
    assert first == (attempt_root / "provider-recovery-chunk-01-attempt-2.json",)
    assert second == (attempt_root / "provider-recovery-chunk-02-attempt-2.json",)


def test_stopped_coordinates_ignore_identical_terminal_from_committed_chunk(
    guardian: ModuleType, tmp_path: Path
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output = config.backing_root / guardian.OUTPUT_ROOTS[0]
    attempt_root = output / "clean_label/chunks/packet-0001"
    attempt_root.mkdir(parents=True, mode=0o700)
    for directory in (output, output / "clean_label", output / "clean_label/chunks"):
        os.chmod(directory, 0o700)
    common = {
        "schema_version": "phase3_cycle007_gemini_attempt_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": "clean_label",
        "packet_index": 1,
        "attempt": 1,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
    }
    terminal_tail = {
        "state": "terminal",
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "provider_call_started": True,
        "executable_binding_result": "verified",
        "provider_return_code": "nonzero",
        "raw_byte_count": 1,
        "raw_sha256": "7" * 64,
        "log_byte_count": 1,
        "log_sha256": "8" * 64,
        "init_count": 1,
        "result_count": 1,
        "first_event_kind": "init",
        "last_event_kind": "result",
        "model_binding_result": "verified",
        "result_status": "non_success",
        "structured_output_type": "missing",
    }
    terminals: dict[int, dict[str, Any]] = {}
    for chunk_index in (1, 2):
        chunk_common = common | {"chunk_index": chunk_index}
        _write_private_json(
            attempt_root / f"attempt-1-chunk-{chunk_index:02d}.started.json",
            chunk_common | {"state": "started"},
        )
        terminal = chunk_common | terminal_tail
        _write_private_json(
            attempt_root / f"attempt-1-chunk-{chunk_index:02d}.terminal.json",
            terminal,
        )
        terminals[chunk_index] = terminal
    labels = attempt_root / "labels-chunk-01.json"
    labels.write_bytes(b"opaque")
    labels.chmod(0o600)
    _write_private_json(
        attempt_root / "receipt-chunk-01.json",
        {
            "schema_version": "phase3_cycle007_gemini_chunk_receipt_v1",
            "attempt_count": 1,
            "text_free": True,
        },
    )
    stopped = terminals[2]
    stop = {
        **{
            key: value
            for key, value in stopped.items()
            if key not in {"schema_version", "state", "packet_index", "chunk_index", "attempt"}
        },
        "schema_version": "phase3_cycle007_gemini_provider_stop_v2",
        "terminal_packet_index": 1,
        "new_provider_calls_allowed": False,
        "chunk_index": 2,
        "attempt": 1,
        "terminal_marker_sha256": guardian._digest(
            guardian._canonical(terminals[2])
        ),
    }
    root, chunk_index, attempt = guardian._stopped_attempt_coordinates(
        config, output, stop
    )
    assert root == attempt_root
    assert (chunk_index, attempt) == (2, 1)


def test_provider_call_count_excludes_pre_call_terminal_marker(
    guardian: ModuleType, tmp_path: Path
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output = config.backing_root / guardian.OUTPUT_ROOTS[0]
    attempt_root = output / "clean_label/chunks/packet-0001"
    attempt_root.mkdir(parents=True, mode=0o700)
    for directory in (output, output / "clean_label", output / "clean_label/chunks"):
        os.chmod(directory, 0o700)
    for attempt in (1, 2):
        _write_private_json(
            attempt_root / f"attempt-{attempt}-chunk-01.started.json",
            {"state": "started", "text_free": True},
        )
    _write_private_json(
        attempt_root / "attempt-1-chunk-01.terminal.json",
        {
            "schema_version": "phase3_cycle007_gemini_attempt_v1",
            "state": "terminal",
            "text_free": True,
            "provider_call_started": False,
        },
    )
    labels = attempt_root / "labels-chunk-01.json"
    labels.write_bytes(b"opaque")
    labels.chmod(0o600)
    _write_private_json(
        attempt_root / "receipt-chunk-01.json",
        {
            "schema_version": "phase3_cycle007_gemini_chunk_receipt_v1",
            "attempt_count": 2,
            "text_free": True,
        },
    )
    assert guardian._provider_call_count(config, output) == 1


def test_provider_call_count_rejects_orphan_terminal(
    guardian: ModuleType, tmp_path: Path
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output = config.backing_root / guardian.OUTPUT_ROOTS[0]
    attempt_root = output / "clean_label/chunks/packet-0001"
    attempt_root.mkdir(parents=True, mode=0o700)
    for directory in (output, output / "clean_label", output / "clean_label/chunks"):
        os.chmod(directory, 0o700)
    _write_private_json(
        attempt_root / "attempt-1-chunk-01.terminal.json",
        {
            "schema_version": "phase3_cycle007_gemini_attempt_v1",
            "state": "terminal",
            "text_free": True,
            "provider_call_started": True,
        },
    )
    with pytest.raises(guardian.GuardianError, match="stop_recovery_state_drift"):
        guardian._provider_call_count(config, output)


def test_occurrence_bound_stop_hash_changes_with_attempt_and_binds_terminal(
    guardian: ModuleType, tmp_path: Path
) -> None:
    base = {
        "schema_version": "phase3_cycle007_gemini_provider_stop_v2",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": "clean_label",
        "terminal_packet_index": 1,
        "failure_code": "provider_status_timeout",
        "new_provider_calls_allowed": False,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
        "failure_stage": "provider_return",
        "provider_call_started": True,
        "executable_binding_result": "verified",
        "provider_return_code": "nonzero",
        "raw_byte_count": 0,
        "raw_sha256": guardian._digest(b""),
        "log_byte_count": 0,
        "log_sha256": guardian._digest(b""),
        "init_count": 0,
        "result_count": 0,
        "first_event_kind": "empty",
        "last_event_kind": "empty",
        "model_binding_result": "not_inspected",
        "result_status": "not_inspected",
        "structured_output_type": "not_inspected",
        "chunk_index": 1,
        "terminal_marker_sha256": "c" * 64,
    }
    third = base | {"attempt": 3}
    fourth = base | {"attempt": 4}
    assert guardian._digest(guardian._canonical(third)) != guardian._digest(
        guardian._canonical(fourth)
    )


def test_legacy_unbound_stop_is_refused_after_installed_attempt_three(
    guardian: ModuleType, tmp_path: Path
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output = config.backing_root / guardian.OUTPUT_ROOTS[0]
    attempt_root = output / "clean_label/chunks/packet-0001"
    attempt_root.mkdir(parents=True, mode=0o700)
    for directory in (output, output / "clean_label", output / "clean_label/chunks"):
        os.chmod(directory, 0o700)
    common = {
        "schema_version": "phase3_cycle007_gemini_attempt_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": "clean_label",
        "packet_index": 1,
        "chunk_index": 1,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
    }
    terminal: dict[str, Any] | None = None
    for attempt in range(1, 5):
        _write_private_json(
            attempt_root / f"attempt-{attempt}-chunk-01.started.json",
            common | {"attempt": attempt, "state": "started"},
        )
        terminal = common | {
            "attempt": attempt,
            "state": "terminal",
            "failure_code": "provider_status_timeout",
            "failure_stage": "provider_return",
            "provider_call_started": True,
            "executable_binding_result": "verified",
            "provider_return_code": "nonzero",
            "raw_byte_count": 0,
            "raw_sha256": guardian._digest(b""),
            "log_byte_count": 0,
            "log_sha256": guardian._digest(b""),
            "init_count": 0,
            "result_count": 0,
            "first_event_kind": "empty",
            "last_event_kind": "empty",
            "model_binding_result": "not_inspected",
            "result_status": "not_inspected",
            "structured_output_type": "not_inspected",
        }
        _write_private_json(
            attempt_root / f"attempt-{attempt}-chunk-01.terminal.json", terminal
        )
    assert terminal is not None
    stop = {
        **{
            key: value
            for key, value in terminal.items()
            if key not in {"schema_version", "state", "packet_index", "chunk_index", "attempt"}
        },
        "schema_version": "phase3_cycle007_gemini_provider_stop_v1",
        "terminal_packet_index": 1,
        "new_provider_calls_allowed": False,
    }
    with pytest.raises(guardian.GuardianError, match="stop_recovery_binding_drift"):
        guardian._stopped_attempt_coordinates(config, output, stop)


def test_pre_call_attempt_then_timeout_is_recoverable_with_exact_call_count(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output = config.backing_root / guardian.OUTPUT_ROOTS[0]
    attempt_root = output / "clean_label/chunks/packet-0001"
    attempt_root.mkdir(parents=True, mode=0o700)
    for directory in (output, output / "clean_label", output / "clean_label/chunks"):
        os.chmod(directory, 0o700)
    common = {
        "schema_version": "phase3_cycle007_gemini_attempt_v1",
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": "clean_label",
        "packet_index": 1,
        "chunk_index": 1,
        "exact_model": "Gemini 3.6 Flash (High)",
        "model_family": "google",
        "harness": "agy",
        "text_free": True,
    }
    empty_sha = guardian._digest(b"")
    _write_private_json(
        attempt_root / "attempt-1-chunk-01.started.json",
        common | {"attempt": 1, "state": "started"},
    )
    _write_private_json(
        attempt_root / "attempt-1-chunk-01.terminal.json",
        common
        | {
            "attempt": 1,
            "state": "terminal",
            "failure_code": "structured_output_envelope_drift",
            "failure_stage": "executable_binding",
            "provider_call_started": False,
            "executable_binding_result": "mismatch",
            "provider_return_code": "not_started",
            "raw_byte_count": 0,
            "raw_sha256": empty_sha,
            "log_byte_count": 0,
            "log_sha256": empty_sha,
            "init_count": 0,
            "result_count": 0,
            "first_event_kind": "unavailable",
            "last_event_kind": "unavailable",
            "model_binding_result": "not_inspected",
            "result_status": "not_inspected",
            "structured_output_type": "not_inspected",
        },
    )
    _write_private_json(
        attempt_root / "attempt-2-chunk-01.started.json",
        common | {"attempt": 2, "state": "started"},
    )
    terminal = common | {
        "attempt": 2,
        "state": "terminal",
        "failure_code": "provider_status_timeout",
        "failure_stage": "provider_return",
        "provider_call_started": True,
        "executable_binding_result": "verified",
        "provider_return_code": "nonzero",
        "raw_byte_count": 1,
        "raw_sha256": "a" * 64,
        "log_byte_count": 1,
        "log_sha256": "b" * 64,
        "init_count": 1,
        "result_count": 1,
        "first_event_kind": "init",
        "last_event_kind": "result",
        "model_binding_result": "verified",
        "result_status": "non_success",
        "structured_output_type": "missing",
    }
    terminal_raw = _write_private_json(
        attempt_root / "attempt-2-chunk-01.terminal.json", terminal
    )
    stop = {
        **{
            key: value
            for key, value in terminal.items()
            if key not in {"schema_version", "state", "packet_index", "chunk_index", "attempt"}
        },
        "schema_version": "phase3_cycle007_gemini_provider_stop_v2",
        "terminal_packet_index": 1,
        "new_provider_calls_allowed": False,
        "chunk_index": 1,
        "attempt": 2,
        "terminal_marker_sha256": guardian._digest(terminal_raw),
    }
    stop_raw = _write_private_json(output / "provider-stop.json", stop)
    config = replace(config, expected_stop_sha256=guardian._digest(stop_raw))
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: {
            "stopped": (output / "provider-stop.json").exists(),
            "completed_stages": [],
        },
    )
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 123)
    result = guardian._gemini_stop_recovery(config, mounts=[])
    assert result["prior_provider_call_count"] == 1
    assert result["authorized_attempt"] == 3
    receipt = json.loads(
        (output / guardian.GEMINI_SECOND_RECOVERY_RECEIPT).read_text(encoding="utf-8")
    )
    assert receipt["prior_provider_call_count"] == 1


def test_recovery_is_idempotent_if_stop_removal_is_interrupted(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output, stop_sha, _first_recovery_raw = _seed_second_gemini_timeout(
        guardian, config
    )
    config = replace(config, expected_stop_sha256=stop_sha)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: {
            "stopped": (output / "provider-stop.json").exists(),
            "completed_stages": [],
        },
    )
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 123)
    monkeypatch.setattr(guardian, "_remove_durable", lambda _path: None)
    first = guardian._gemini_stop_recovery(config, mounts=[])
    second = guardian._gemini_stop_recovery(config, mounts=[])
    assert first == second
    assert (output / "provider-stop.json").is_file()


@pytest.mark.parametrize("mutation", ["terminal", "recovery"])
def test_idempotent_recovery_revalidates_full_chain_after_restart(
    guardian: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output, stop_sha, _first_recovery_raw = _seed_second_gemini_timeout(
        guardian, config
    )
    config = replace(config, expected_stop_sha256=stop_sha)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: {
            "stopped": (output / "provider-stop.json").exists(),
            "completed_stages": [],
        },
    )
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 123)
    guardian._gemini_stop_recovery(config, mounts=[])
    if mutation == "terminal":
        path = output / "clean_label/chunks/packet-0001/attempt-2-chunk-01.terminal.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["log_sha256"] = "9" * 64
    else:
        path = output / guardian.GEMINI_SECOND_RECOVERY_RECEIPT
        value = json.loads(path.read_text(encoding="utf-8"))
        value["prior_provider_call_count"] = 99
    _write_private_json(path, value)
    with pytest.raises(guardian.GuardianError, match="stop_recovery_state_drift"):
        guardian._gemini_stop_recovery(config, mounts=[])


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("wrong_failure_code", "stop_recovery_state_drift"),
        ("wrong_stop_hash", "stop_recovery_binding_drift"),
        ("attempt_count_drift", "stop_recovery_state_drift"),
        ("prior_recovery_drift", "stop_recovery_state_drift"),
    ],
)
def test_second_gemini_timeout_recovery_refuses_state_drift(
    guardian: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    expected_code: str,
) -> None:
    config = _config(guardian, tmp_path, action="recover-gemini-stop")
    output, stop_sha, _first_recovery_raw = _seed_second_gemini_timeout(guardian, config)
    if mutation == "wrong_failure_code":
        terminal_path = output / "clean_label/chunks/packet-0001/attempt-2-chunk-01.terminal.json"
        terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
        terminal["failure_code"] = "provider_status_capacity_unavailable"
        _write_private_json(terminal_path, terminal)
    elif mutation == "wrong_stop_hash":
        stop_sha = "0" * 64
    elif mutation == "attempt_count_drift":
        _write_private_json(
            output / "clean_label/chunks/packet-0001/attempt-3-chunk-01.started.json",
            {"text_free": True},
        )
    else:
        recovery_path = output / guardian.GEMINI_RECOVERY_RECEIPT
        recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
        recovery["authorized_additional_provider_calls"] = 2
        _write_private_json(recovery_path, recovery)
    config = replace(config, expected_stop_sha256=stop_sha)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: {"stopped": True, "completed_stages": []},
    )

    with pytest.raises(guardian.GuardianError, match=expected_code):
        guardian._gemini_stop_recovery(config, mounts=[])


def test_wrong_existing_mount_is_refused_without_mount_command(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path)
    for name in guardian.OUTPUT_ROOTS:
        (config.backing_root / name).mkdir(mode=0o700)
        (config.package / name).mkdir(mode=0o700)
    monkeypatch.setattr(guardian, "_validate_roots", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        guardian,
        "_mount_entries",
        lambda _path: [
            guardian.MountEntry(config.package / name, "/wrong", "/dev/test", "8:2")
            for name in guardian.OUTPUT_ROOTS
        ],
    )
    monkeypatch.setattr(guardian, "_same_identity", lambda _source, _target: False)
    called = False

    def mount(*_args: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(guardian, "_bind_mount", mount)
    with pytest.raises(guardian.GuardianError, match="mount_identity_drift"):
        guardian._ensure_mounts(config, mutate=True)
    assert not called


def test_bind_mount_timeout_has_fixed_failure_code(
    guardian: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        guardian.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("mount", 30)),
    )
    with pytest.raises(guardian.GuardianError, match="bind_mount_timeout"):
        guardian._bind_mount(Path("/source"), Path("/target"), ("/usr/bin/mount",))


def test_bind_mount_supports_explicit_non_shell_prefix(
    guardian: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        captured["command"] = command
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(guardian.subprocess, "run", run)
    guardian._bind_mount(
        Path("/source"),
        Path("/target"),
        ("/usr/bin/sudo", "-n", "/usr/bin/mount"),
    )
    assert captured["command"] == [
        "/usr/bin/sudo",
        "-n",
        "/usr/bin/mount",
        "--bind",
        "/source",
        "/target",
    ]
    assert captured["shell"] is False


@pytest.mark.parametrize(
    "command",
    [
        (),
        ("mount",),
        ("/usr/bin/sudo", "/usr/bin/mount"),
        ("/usr/bin/sudo", "-E", "/usr/bin/mount"),
        ("/usr/bin/mount\0",),
    ],
)
def test_mount_command_rejects_ambiguous_or_path_discovered_argv(
    guardian: ModuleType, command: tuple[str, ...]
) -> None:
    with pytest.raises(guardian.GuardianError, match="invalid_mount_command"):
        guardian._validate_mount_command(command)


def test_mount_cli_builds_exact_noninteractive_sudo_argv(guardian: ModuleType) -> None:
    args = guardian._parser().parse_args(
        [
            "prepare",
            "--package", "/package",
            "--backing-root", "/backing",
            "--guardian-lock", "/locks/guardian",
            "--controller-lock", "/locks/controller",
            "--execution-lock", "/locks/execution",
            "--controller", "/controller",
            "--owner-uid", "1",
            "--owner-gid", "1",
            "--min-free-bytes", "1",
            "--mount-command", "/usr/bin/mount",
            "--sudo-command", "/usr/bin/sudo",
        ]
    )
    assert guardian._config(args).mount_command == (
        "/usr/bin/sudo",
        "-n",
        "/usr/bin/mount",
    )


def test_duplicate_guardian_lock_is_nonblocking(guardian: ModuleType, tmp_path: Path) -> None:
    path = tmp_path / "locks/guardian.lock"
    first = guardian._lock(path, "guardian_already_running")
    try:
        with pytest.raises(guardian.GuardianError, match="guardian_already_running"):
            guardian._lock(path, "guardian_already_running")
    finally:
        first.close()


def test_lock_refuses_symlink_leaf(guardian: ModuleType, tmp_path: Path) -> None:
    lock_directory = tmp_path / "locks"
    lock_directory.mkdir(mode=0o700)
    target = tmp_path / "target"
    target.write_text("", encoding="utf-8")
    link = lock_directory / "execution.lock"
    link.symlink_to(target)
    with pytest.raises(guardian.GuardianError, match="lock_path_drift"):
        guardian._lock(link, "active_worker")


def test_execution_lock_survives_in_inherited_child(guardian: ModuleType, tmp_path: Path) -> None:
    path = tmp_path / "locks/execution.lock"
    owner = guardian._lock(path, "active_worker")
    child = subprocess.Popen(
        [
            os.environ.get("PYTHON", os.sys.executable),
            "-c",
            "import os,time; os.fstat(int(os.environ['LOCK_FD'])); time.sleep(30)",
        ],
        env={**os.environ, "LOCK_FD": str(owner.fileno())},
        pass_fds=(owner.fileno(),),
    )
    owner.close()
    try:
        with pytest.raises(guardian.GuardianError, match="active_worker"):
            guardian._lock(path, "active_worker")
    finally:
        child.terminate()
        child.wait(timeout=5)
    replacement = guardian._lock(path, "active_worker")
    replacement.close()


def test_controller_passes_execution_descriptor_to_stage_runner(
    controller: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = tmp_path / "compare.py"
    runner.write_text("# public fixture\n", encoding="utf-8")
    lock_file = _temporary_file()
    captured: dict[str, Any] = {}

    monkeypatch.setattr(controller, "_require_contiguous", lambda *_args, **_kwargs: None)
    python_target = tmp_path / "python-target"
    python_target.write_bytes(b"fixture interpreter")
    monkeypatch.setattr(controller, "_require_python_binding", lambda *_args, **_kwargs: python_target)
    monkeypatch.setattr(controller, "_commands_for_stage", lambda *_args, **_kwargs: ([['fixture']], None))
    monkeypatch.setattr(controller, "_revalidate_compare_receipts", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(controller, "_stage_stop_paths", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(controller, "_seal", lambda *_args, **_kwargs: None)

    def run(command: list[str], **kwargs: Any) -> tuple[int, bytes]:
        captured["command"] = command
        captured.update(kwargs)
        return 0, b""

    monkeypatch.setattr(controller, "_run_stage_subprocess", run)
    result = controller.run_stage(
        tmp_path,
        "compare",
        runner,
        "a" * 64,
        dry_run=False,
        expected_python_executable_sha256="b" * 64,
        expected_label_prompt_sha256s={
            "gemini": {"clean_label": "c" * 64, "residual_label": "d" * 64},
            "grok": {"clean_label": "e" * 64, "residual_label": "f" * 64},
        },
        expected_custody_sha256="1" * 64,
        expected_label_manifest_sha256="2" * 64,
        expected_evidence_manifest_sha256="3" * 64,
        code_paths={"compare_runner": runner.resolve()},
        execution_lock_fd=lock_file.fileno(),
    )
    assert result["ok"] is True
    assert captured["pass_fds"] == (lock_file.fileno(),)
    assert captured["executable"] == python_target
    lock_file.close()


@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        (
            b'{"failure_code":"sidecar_binding_drift","ok":false,"text_free":true}\n',
            "sidecar_binding_drift",
        ),
        (b'{"failure_code":"PRIVATE CONTENT","ok":false,"text_free":true}\n', "stage_execution_failed"),
        (
            b'{"failure_code":"sidecar_binding_drift","ok":false,"private":"x","text_free":true}\n',
            "stage_execution_failed",
        ),
        (
            b'{"failure_code":"sidecar_binding_drift","ok":true,"ok":false,"text_free":true}\n',
            "stage_execution_failed",
        ),
        (b'{"failure_code":"sidecar_binding_drift","ok":true,"text_free":true}\n', "stage_execution_failed"),
        (b'{"failure_code":"sidecar_binding_drift","ok":false,"text_free":false}\n', "stage_execution_failed"),
        (b'{"failure_code":"","ok":false,"text_free":true}\n', "stage_execution_failed"),
        (b'{"failure_code":123,"ok":false,"text_free":true}\n', "stage_execution_failed"),
        (b'{"failure_code":null,"ok":false,"text_free":true}\n', "stage_execution_failed"),
        (b'{"failure_code":"a","invalid":true,"ok":false}\n', "stage_execution_failed"),
        (
            b'{"failure_code":"' + b"a" * 65 + b'","ok":false,"text_free":true}\n',
            "stage_execution_failed",
        ),
        (b"not-json", "stage_execution_failed"),
        (b"x" * (4096 + 1), "stage_execution_failed"),
    ],
)
def test_controller_accepts_only_bounded_text_free_runner_failure_codes(
    controller: ModuleType, stdout: bytes, expected: str
) -> None:
    assert controller._runner_failure_code(stdout) == expected


def test_controller_stage_subprocess_capture_is_bounded(controller: ModuleType) -> None:
    command = [sys.executable, "-c", "import sys; sys.stdout.write('x' * 8192); raise SystemExit(2)"]
    return_code, status = controller._run_stage_subprocess(
        command,
        executable=Path(sys.executable).resolve(),
        pass_fds=(),
    )
    assert return_code == 2
    assert len(status) == controller.MAX_RUNNER_STATUS_BYTES + 1


def test_controller_discards_successful_stage_stdout(controller: ModuleType) -> None:
    command = [sys.executable, "-c", "print('ignored')"]
    return_code, status = controller._run_stage_subprocess(
        command,
        executable=Path(sys.executable).resolve(),
        pass_fds=(),
    )
    assert return_code == 0
    assert status == b""


def test_controller_does_not_wait_for_grandchild_inherited_stdout(
    controller: ModuleType, tmp_path: Path
) -> None:
    pid_file = tmp_path / "grandchild.pid"
    child = (
        "import pathlib,subprocess,sys; "
        "p=subprocess.Popen([sys.executable,'-c',"
        "\"import os; b=b'x'*65536; exec('while True:\\\\n os.write(1,b)')\"]); "
        f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid)); "
        "raise SystemExit(2)"
    )
    started = time.monotonic()
    try:
        return_code, _status = controller._run_stage_subprocess(
            [sys.executable, "-c", child],
            executable=Path(sys.executable).resolve(),
            pass_fds=(),
        )
        assert return_code == 2
        assert time.monotonic() - started < 5
    finally:
        if pid_file.exists():
            with contextlib.suppress(ProcessLookupError):
                os.kill(int(pid_file.read_text(encoding="utf-8")), 15)


def test_controller_propagates_safe_runner_failure_code(
    controller: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = tmp_path / "compare.py"
    runner.write_text("# public fixture\n", encoding="utf-8")
    python_target = tmp_path / "python-target"
    python_target.write_bytes(b"fixture interpreter")
    monkeypatch.setattr(controller, "_require_contiguous", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(controller, "_require_python_binding", lambda *_args, **_kwargs: python_target)
    monkeypatch.setattr(controller, "_commands_for_stage", lambda *_args, **_kwargs: ([["fixture"]], None))
    monkeypatch.setattr(
        controller,
        "_run_stage_subprocess",
        lambda *_args, **_kwargs: (
            2,
            b'{"failure_code":"sidecar_binding_drift","ok":false,"text_free":true}\n',
        ),
    )

    with pytest.raises(controller.ControllerError, match=r"^sidecar_binding_drift$"):
        controller.run_stage(
            tmp_path,
            "compare",
            runner,
            "a" * 64,
            dry_run=False,
            expected_python_executable_sha256="b" * 64,
            expected_label_prompt_sha256s={
                "gemini": {"clean_label": "c" * 64, "residual_label": "d" * 64},
                "grok": {"clean_label": "e" * 64, "residual_label": "f" * 64},
            },
            expected_custody_sha256="1" * 64,
            expected_label_manifest_sha256="2" * 64,
            expected_evidence_manifest_sha256="3" * 64,
            code_paths={"compare_runner": runner.resolve()},
        )


def test_controller_preserves_python_launcher_for_stage_subprocesses(
    controller: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "base-python"
    target.write_bytes(b"base interpreter")
    launcher = tmp_path / "venv/bin/python"
    launcher.parent.mkdir(mode=0o700, parents=True)
    launcher.symlink_to(target)
    monkeypatch.setattr(controller, "PRIMARY_PYTHON", launcher)
    expected_python_sha256 = controller._python_executable_sha256()
    runner = tmp_path / "gemini.py"
    runner.write_text("# public fixture\n", encoding="utf-8")
    labels = {
        "gemini": {"clean_label": "a" * 64, "residual_label": "b" * 64},
        "grok": {"clean_label": "c" * 64, "residual_label": "d" * 64},
    }
    monkeypatch.setattr(
        controller,
        "gemini_missing_ranges",
        lambda *_args, **_kwargs: {"clean_label": [(1, 1)], "residual_label": []},
    )

    commands, _runner = controller._commands_for_stage(
        tmp_path,
        "gemini",
        None,
        code_paths={"gemini_runner": runner},
        expected_agy_executable_sha256="e" * 64,
        agy_executable=tmp_path / "agy",
        expected_label_prompt_sha256s=labels,
        expected_custody_sha256="f" * 64,
        expected_label_manifest_sha256="1" * 64,
        expected_evidence_manifest_sha256="2" * 64,
        expected_sources_endpoint_identity={
            "server_code_sha256": "3" * 64,
            "sources_db_sha256": "4" * 64,
            "vesum_db_sha256": "5" * 64,
        },
    )

    assert commands[0][0] == os.fspath(launcher)
    assert commands[0][0] != os.fspath(target)
    assert commands[0][commands[0].index("--expected-server-code-sha") + 1] == "3" * 64
    assert commands[0][commands[0].index("--expected-sources-db-sha") + 1] == "4" * 64
    assert commands[0][commands[0].index("--expected-vesum-db-sha") + 1] == "5" * 64
    assert expected_python_sha256 == controller._python_executable_sha256()
    assert controller._require_python_binding(expected_python_sha256) == target


def test_controller_binds_preflight_source_identity_into_grok_command(
    controller: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = tmp_path / "grok.py"
    runner.write_text("# public fixture\n", encoding="utf-8")
    monkeypatch.setattr(controller, "_load_bound_runner", lambda *_args: SimpleNamespace())
    monkeypatch.setattr(
        controller,
        "grok_missing_ranges",
        lambda *_args, **_kwargs: {"clean_label": [(1, 1)], "residual_label": []},
    )

    commands, _runner = controller._commands_for_stage(
        tmp_path,
        "grok",
        runner,
        code_paths={"grok_runner": runner},
        expected_agy_executable_sha256="a" * 64,
        expected_grok_executable_sha256="b" * 64,
        grok_executable=tmp_path / "grok",
        expected_label_prompt_sha256s={
            "gemini": {"clean_label": "c" * 64, "residual_label": "d" * 64},
            "grok": {"clean_label": "e" * 64, "residual_label": "f" * 64},
        },
        expected_custody_sha256="1" * 64,
        expected_label_manifest_sha256="2" * 64,
        expected_evidence_manifest_sha256="3" * 64,
        expected_sources_endpoint_identity={
            "server_code_sha256": "4" * 64,
            "sources_db_sha256": "5" * 64,
            "vesum_db_sha256": "6" * 64,
        },
    )

    command = commands[0]
    assert command[command.index("--expected-server-code-sha") + 1] == "4" * 64
    assert command[command.index("--expected-sources-db-sha") + 1] == "5" * 64
    assert command[command.index("--expected-vesum-db-sha") + 1] == "6" * 64


def test_controller_executes_bound_target_with_venv_launcher_semantics(
    controller: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    venv_root = tmp_path / "venv"
    venv.EnvBuilder(with_pip=False, symlinks=True).create(venv_root)
    launcher = venv_root / "bin/python"
    marker = tmp_path / "venv-active"
    runner = tmp_path / "probe.py"
    runner.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "Path(sys.argv[1]).write_text('1' if sys.prefix != sys.base_prefix else '0')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(controller, "PRIMARY_PYTHON", launcher)
    expected_python_sha256 = controller._python_executable_sha256()
    monkeypatch.setattr(controller, "_require_contiguous", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        controller,
        "_commands_for_stage",
        lambda *_args, **_kwargs: ([[os.fspath(launcher), os.fspath(runner), os.fspath(marker)]], None),
    )
    monkeypatch.setattr(controller, "_revalidate_compare_receipts", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(controller, "_stage_stop_paths", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(controller, "_seal", lambda *_args, **_kwargs: None)

    result = controller.run_stage(
        tmp_path,
        "compare",
        runner,
        "a" * 64,
        dry_run=False,
        expected_python_executable_sha256=expected_python_sha256,
        expected_label_prompt_sha256s={
            "gemini": {"clean_label": "b" * 64, "residual_label": "c" * 64},
            "grok": {"clean_label": "d" * 64, "residual_label": "e" * 64},
        },
        expected_custody_sha256="f" * 64,
        expected_label_manifest_sha256="1" * 64,
        expected_evidence_manifest_sha256="2" * 64,
        code_paths={"compare_runner": runner.resolve()},
    )

    assert result["ok"] is True
    assert marker.read_text(encoding="utf-8") == "1"


def test_controller_rejects_python_target_drift(
    controller: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_target = tmp_path / "python-first"
    second_target = tmp_path / "python-second"
    first_target.write_bytes(b"first interpreter")
    second_target.write_bytes(b"different interpreter")
    launcher = tmp_path / "venv/bin/python"
    launcher.parent.mkdir(mode=0o700, parents=True)
    launcher.symlink_to(first_target)
    monkeypatch.setattr(controller, "PRIMARY_PYTHON", launcher)
    expected_python_sha256 = controller._python_executable_sha256()

    launcher.unlink()
    launcher.symlink_to(second_target)

    with pytest.raises(controller.ControllerError, match="preflight_binding_drift"):
        controller._require_python_binding(expected_python_sha256)


def test_controller_rejects_invalid_inherited_descriptor(
    controller: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(controller.EXECUTION_LOCK_FD_ENV, "not-an-fd")
    with pytest.raises(controller.ControllerError, match="execution_lock_binding_drift"):
        controller._inherited_execution_lock_fd()


def test_prepare_with_bindings_invokes_provider_free_preflight(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="prepare")
    calls: list[tuple[str, int | None]] = []
    monkeypatch.setattr(guardian, "_config", lambda _args: config)
    monkeypatch.setattr(guardian, "_lock", lambda *_args: _temporary_file())
    monkeypatch.setattr(guardian, "_ensure_mounts", lambda *_args, **_kwargs: [{"name": name} for name in guardian.OUTPUT_ROOTS])
    monkeypatch.setattr(guardian, "_require_free_space", lambda *_args: 100)
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 100)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda _config, action, **kwargs: calls.append((action, kwargs.get("execution_fd")))
        or {"ok": True, "text_free": True},
    )
    arguments = [
        "prepare",
        "--package", "/package",
        "--backing-root", "/backing",
        "--guardian-lock", "/locks/guardian",
        "--controller-lock", "/locks/controller",
        "--execution-lock", "/locks/execution",
        "--controller", "/controller",
        "--preflight-receipt", "/preflight",
        "--gemini-canary-receipt", "/gemini",
        "--grok-canary-receipt", "/grok",
        "--agy-executable", "/tools/agy",
        "--grok-executable", "/tools/grok",
        "--owner-uid", "1",
        "--owner-gid", "1",
        "--min-free-bytes", "1",
    ]
    assert guardian.main(arguments) == 0
    assert len(calls) == 1
    assert calls[0][0] == "preflight"
    assert isinstance(calls[0][1], int)


def test_provider_free_prepare_accepts_no_provider_bindings(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(
        guardian,
        tmp_path,
        action="prepare",
        preflight_receipt=None,
        gemini_canary_receipt=None,
        grok_canary_receipt=None,
        agy_executable=None,
        grok_executable=None,
    )
    monkeypatch.setattr(guardian, "_config", lambda _args: config)
    monkeypatch.setattr(guardian, "_lock", lambda *_args: _temporary_file())
    monkeypatch.setattr(
        guardian,
        "_ensure_mounts",
        lambda *_args, **_kwargs: [{"name": name} for name in guardian.OUTPUT_ROOTS],
    )
    monkeypatch.setattr(guardian, "_require_free_space", lambda *_args: 100)
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 100)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: pytest.fail("prepare invoked controller"),
    )
    assert guardian.main(
        [
            "prepare",
            "--package", "/package",
            "--backing-root", "/backing",
            "--guardian-lock", "/locks/guardian",
            "--controller-lock", "/locks/controller",
            "--execution-lock", "/locks/execution",
            "--controller", "/controller",
            "--owner-uid", "1",
            "--owner-gid", "1",
            "--min-free-bytes", "1",
        ]
    ) == 0


@pytest.mark.parametrize("action", ["status", "plan"])
def test_provider_free_fresh_status_reports_gemini_without_controller(
    guardian: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    config = _config(
        guardian,
        tmp_path,
        action=action,
        through=None,
        preflight_receipt=None,
        gemini_canary_receipt=None,
        grok_canary_receipt=None,
        agy_executable=None,
        grok_executable=None,
    )
    (config.package / "control").mkdir(mode=0o700)
    for name in guardian.OUTPUT_ROOTS:
        (config.backing_root / name).mkdir(mode=0o700)
    monkeypatch.setattr(guardian, "_config", lambda _args: config)
    monkeypatch.setattr(guardian, "_lock", lambda *_args: _temporary_file())
    monkeypatch.setattr(
        guardian,
        "_ensure_mounts",
        lambda *_args, **_kwargs: [{"name": name} for name in guardian.OUTPUT_ROOTS],
    )
    monkeypatch.setattr(guardian, "_require_free_space", lambda *_args: 100)
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 100)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: pytest.fail("fresh provider-free status invoked controller"),
    )
    receipts: list[dict[str, Any]] = []
    monkeypatch.setattr(guardian, "print", lambda value: receipts.append(json.loads(value)), raising=False)
    assert guardian.main(
        [
            action,
            "--package", "/package",
            "--backing-root", "/backing",
            "--guardian-lock", "/locks/guardian",
            "--controller-lock", "/locks/controller",
            "--execution-lock", "/locks/execution",
            "--controller", "/controller",
            "--owner-uid", "1",
            "--owner-gid", "1",
            "--min-free-bytes", "1",
        ]
    ) == 0
    assert receipts == [
        {
            "action": action,
            "available_bytes": 100,
            "completed_stages": [],
            "min_free_bytes": 1,
            "mount_count": 6,
            "mounts": [{"name": name} for name in guardian.OUTPUT_ROOTS],
            "next_stage": "gemini",
            "ok": True,
            "ready": False,
            "recovered_temporary_count": 0,
            "schema_version": guardian.RECEIPT_SCHEMA,
            "text_free": True,
            "through": None,
        }
    ]


def test_provider_free_bootstrap_rejects_partial_bindings(guardian: ModuleType, tmp_path: Path) -> None:
    config = _config(
        guardian,
        tmp_path,
        preflight_receipt=None,
        gemini_canary_receipt=None,
        grok_canary_receipt=None,
        grok_executable=None,
    )
    with pytest.raises(guardian.GuardianError, match="provider_binding_incomplete"):
        guardian._provider_bindings_complete(config, required=False)


def test_resume_still_requires_complete_provider_preflight(guardian: ModuleType, tmp_path: Path) -> None:
    config = _config(
        guardian,
        tmp_path,
        preflight_receipt=None,
        gemini_canary_receipt=None,
        grok_canary_receipt=None,
        agy_executable=None,
        grok_executable=None,
    )
    with pytest.raises(guardian.GuardianError, match="provider_preflight_required"):
        guardian._provider_bindings_complete(config, required=True)


def test_provider_free_status_rejects_non_pristine_state(guardian: ModuleType, tmp_path: Path) -> None:
    config = _config(
        guardian,
        tmp_path,
        action="status",
        preflight_receipt=None,
        gemini_canary_receipt=None,
        grok_canary_receipt=None,
        agy_executable=None,
        grok_executable=None,
    )
    control = config.package / "control"
    control.mkdir(mode=0o700)
    for name in guardian.OUTPUT_ROOTS:
        (config.backing_root / name).mkdir(mode=0o700)
    (control / "stage-gemini.complete.json").write_text("{}", encoding="utf-8")
    with pytest.raises(guardian.GuardianError, match="provider_preflight_required"):
        guardian._fresh_provider_free_status(config, mounts=[])


def test_provider_free_status_rejects_active_worker(guardian: ModuleType, tmp_path: Path) -> None:
    config = _config(
        guardian,
        tmp_path,
        action="status",
        preflight_receipt=None,
        gemini_canary_receipt=None,
        grok_canary_receipt=None,
        agy_executable=None,
        grok_executable=None,
    )
    (config.package / "control").mkdir(mode=0o700)
    for name in guardian.OUTPUT_ROOTS:
        (config.backing_root / name).mkdir(mode=0o700)
    worker = guardian._lock(config.execution_lock, "active_worker")
    try:
        with pytest.raises(guardian.GuardianError, match="active_worker"):
            guardian._fresh_provider_free_status(config, mounts=[])
    finally:
        worker.close()


def test_plan_uses_status_only_and_reports_next_stage(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="plan", through=None)
    calls: list[tuple[str, str | None]] = []

    def invoke(_config: Any, action: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((action, kwargs.get("stage")))
        return {"ok": True, "completed_stages": ["gemini"], "ready": False, "text_free": True}

    monkeypatch.setattr(guardian, "_invoke_controller", invoke)
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 100)
    result = guardian._safe_status(config, mounts=[])
    assert result["next_stage"] == "grok"
    assert calls == [("status", None)]


def test_controller_command_forwards_explicit_provider_executables(
    guardian: ModuleType, tmp_path: Path
) -> None:
    config = _config(guardian, tmp_path, action="status")
    command = guardian._controller_command(config, "status")

    agy_index = command.index("--agy-executable")
    grok_index = command.index("--grok-executable")
    assert command[agy_index + 1] == str(config.agy_executable)
    assert command[grok_index + 1] == str(config.grok_executable)


def test_controller_status_drops_ambient_execution_descriptor(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="status")
    captured_environment: dict[str, str] = {}
    monkeypatch.setenv(guardian.EXECUTION_LOCK_FD_ENV, "999999")

    def run(*_args: Any, **kwargs: Any) -> Any:
        captured_environment.update(kwargs["env"])
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b'{"ok":true,"text_free":true}\n',
            stderr=b"",
        )

    monkeypatch.setattr(guardian.subprocess, "run", run)
    guardian._invoke_controller(config, "status")
    assert guardian.EXECUTION_LOCK_FD_ENV not in captured_environment


def test_controller_timeout_has_fixed_failure_code(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="status")
    monkeypatch.setattr(
        guardian.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("controller", 300)),
    )
    with pytest.raises(guardian.GuardianError, match="controller_timeout"):
        guardian._invoke_controller(config, "status")


def test_resume_stops_at_requested_boundary(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, through="grok")
    handle = _temporary_file()
    completed: list[str] = []
    calls: list[tuple[str, str | None]] = []

    monkeypatch.setattr(guardian, "_lock", lambda *_args: handle)
    monkeypatch.setattr(guardian, "_recover_guardian_temporaries", lambda *_args: 0)
    monkeypatch.setattr(guardian, "_reconcile_markers", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(guardian, "_require_free_space", lambda *_args: 100)

    def invoke(_config: Any, action: str, **kwargs: Any) -> dict[str, Any]:
        stage = kwargs.get("stage")
        calls.append((action, stage))
        if action == "run":
            completed.append(stage)
        return {"ok": True, "completed_stages": list(completed), "ready": False, "text_free": True}

    monkeypatch.setattr(guardian, "_invoke_controller", invoke)
    monkeypatch.setattr(
        guardian,
        "_safe_status",
        lambda *_args, **_kwargs: {
            "ok": True,
            "completed_stages": list(completed),
            "text_free": True,
        },
    )
    result = guardian._resume(config, mounts=[])
    assert result["completed_stages"] == ["gemini", "grok"]
    assert [stage for action, stage in calls if action == "run"] == ["gemini", "grok"]


def test_terminal_resume_is_noop(guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config(guardian, tmp_path, through="certify")
    handle = _temporary_file()
    run_calls = 0
    monkeypatch.setattr(guardian, "_lock", lambda *_args: handle)
    monkeypatch.setattr(guardian, "_recover_guardian_temporaries", lambda *_args: 0)
    monkeypatch.setattr(guardian, "_reconcile_markers", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(guardian, "_require_free_space", lambda *_args: 100)

    def invoke(_config: Any, action: str, **_kwargs: Any) -> dict[str, Any]:
        nonlocal run_calls
        if action == "run":
            run_calls += 1
        return {"ok": True, "completed_stages": list(guardian.STAGES), "ready": True, "text_free": True}

    monkeypatch.setattr(guardian, "_invoke_controller", invoke)
    monkeypatch.setattr(
        guardian,
        "_safe_status",
        lambda *_args, **_kwargs: {"ok": True, "completed_stages": list(guardian.STAGES), "text_free": True},
    )
    guardian._resume(config, mounts=[])
    assert run_calls == 0


def test_active_audit_marker_without_seal_stops_before_provider(
    guardian: ModuleType, tmp_path: Path
) -> None:
    config = _config(guardian, tmp_path)
    control = config.package / "control"
    control.mkdir()
    marker = guardian._marker(config, "audit")
    marker.write_text(json.dumps({"text_free": True}), encoding="utf-8")
    with pytest.raises(guardian.GuardianError, match="ambiguous_provider_attempt"):
        guardian._reconcile_markers(config, mutate=False)


def test_stale_marker_after_stage_seal_is_removed_durably(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path)
    control = config.package / "control"
    control.mkdir()
    marker = guardian._marker(config, "adjudicate")
    seal = guardian._stage_seal(config, "adjudicate")
    marker.write_text("{}", encoding="utf-8")
    seal.write_text("{}", encoding="utf-8")
    synced: list[Path] = []
    monkeypatch.setattr(guardian, "_fsync_directory", lambda path: synced.append(path))
    guardian._reconcile_markers(config, mutate=True)
    assert not marker.exists()
    assert synced == [control]


def test_guardian_receipt_rejects_non_text_free_controller_output(guardian: ModuleType) -> None:
    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=b'{"ok":true}\n', stderr=b"")
    with pytest.raises(guardian.GuardianError, match="controller_protocol_failure"):
        guardian._parse_controller_output(completed)


def test_preflight_receipt_rotation_is_chained_archived_and_idempotent(
    controller: ModuleType, tmp_path: Path
) -> None:
    package = tmp_path / "package"
    package.mkdir(mode=0o700)
    old_preflight = _signed_receipt(
        controller,
        schema_version="phase3_cycle007_preflight_receipt_v1",
        review_hashes={"superseded_preflight_receipt_sha256": "0" * 64},
        text_free=True,
    )
    old_gemini = _signed_receipt(controller, schema_version="gemini-old", text_free=True)
    grok = _signed_receipt(controller, schema_version="grok", text_free=True)
    controller._install_preflight_receipts(package, old_preflight, old_gemini, grok)

    old_raw = controller.canonical(old_preflight)
    new_preflight = _signed_receipt(
        controller,
        schema_version="phase3_cycle007_preflight_receipt_v1",
        review_hashes={"superseded_preflight_receipt_sha256": controller.digest(old_raw)},
        text_free=True,
    )
    new_gemini = _signed_receipt(controller, schema_version="gemini-new", text_free=True)
    controller._install_preflight_receipts(package, new_preflight, new_gemini, grok)
    controller._install_preflight_receipts(package, new_preflight, new_gemini, grok)

    control = package / "control"
    assert (control / "preflight-receipt.json").read_bytes() == controller.canonical(new_preflight)
    assert (control / "gemini-canary-receipt.json").read_bytes() == controller.canonical(new_gemini)
    archives = sorted((control / "superseded-receipts").iterdir())
    assert len(archives) == 2
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in archives)
    assert (control / "superseded-receipts").stat().st_mode & 0o777 == 0o700


def test_preflight_receipt_rotation_resumes_after_canary_replacement(
    controller: ModuleType, tmp_path: Path
) -> None:
    package = tmp_path / "package"
    package.mkdir(mode=0o700)
    old_preflight = _signed_receipt(
        controller,
        schema_version="phase3_cycle007_preflight_receipt_v1",
        review_hashes={"superseded_preflight_receipt_sha256": "0" * 64},
        text_free=True,
    )
    old_gemini = _signed_receipt(controller, schema_version="gemini-old", text_free=True)
    grok = _signed_receipt(controller, schema_version="grok", text_free=True)
    controller._install_preflight_receipts(package, old_preflight, old_gemini, grok)
    successor = _signed_receipt(
        controller,
        schema_version="phase3_cycle007_preflight_receipt_v1",
        review_hashes={
            "superseded_preflight_receipt_sha256": controller.digest(controller.canonical(old_preflight))
        },
        text_free=True,
    )
    new_gemini = _signed_receipt(controller, schema_version="gemini-new", text_free=True)
    control = package / "control"
    old_gemini_raw = controller.canonical(old_gemini)
    controller._archive_superseded_receipt(control, "gemini-canary", old_gemini_raw, old_gemini)
    controller._replace_atomic(control / "gemini-canary-receipt.json", new_gemini)

    controller._install_preflight_receipts(package, successor, new_gemini, grok)
    assert (control / "preflight-receipt.json").read_bytes() == controller.canonical(successor)
    assert len(list((control / "superseded-receipts").iterdir())) == 2


def test_preflight_receipt_rotation_rejects_wrong_chain_without_mutation(
    controller: ModuleType, tmp_path: Path
) -> None:
    package = tmp_path / "package"
    package.mkdir(mode=0o700)
    old_preflight = _signed_receipt(
        controller,
        schema_version="phase3_cycle007_preflight_receipt_v1",
        review_hashes={"superseded_preflight_receipt_sha256": "0" * 64},
        text_free=True,
    )
    old_gemini = _signed_receipt(controller, schema_version="gemini-old", text_free=True)
    grok = _signed_receipt(controller, schema_version="grok", text_free=True)
    controller._install_preflight_receipts(package, old_preflight, old_gemini, grok)
    wrong = _signed_receipt(
        controller,
        schema_version="phase3_cycle007_preflight_receipt_v1",
        review_hashes={"superseded_preflight_receipt_sha256": "f" * 64},
        text_free=True,
    )
    new_gemini = _signed_receipt(controller, schema_version="gemini-new", text_free=True)

    with pytest.raises(controller.ControllerError, match="preflight_rotation_not_authorized"):
        controller._install_preflight_receipts(package, wrong, new_gemini, grok)
    control = package / "control"
    assert (control / "preflight-receipt.json").read_bytes() == controller.canonical(old_preflight)
    assert (control / "gemini-canary-receipt.json").read_bytes() == controller.canonical(old_gemini)
    assert not (control / "superseded-receipts").exists()


def test_preflight_receipt_rotation_is_blocked_after_any_stage_seal(
    controller: ModuleType, tmp_path: Path
) -> None:
    package = tmp_path / "package"
    package.mkdir(mode=0o700)
    old = _signed_receipt(
        controller,
        schema_version="phase3_cycle007_preflight_receipt_v1",
        review_hashes={"superseded_preflight_receipt_sha256": "0" * 64},
        text_free=True,
    )
    canary = _signed_receipt(controller, schema_version="canary", text_free=True)
    controller._install_preflight_receipts(package, old, canary, canary)
    seal = package / "control/stage-gemini.complete.json"
    seal.write_text("{}", encoding="utf-8")
    successor = _signed_receipt(
        controller,
        schema_version="phase3_cycle007_preflight_receipt_v1",
        review_hashes={"superseded_preflight_receipt_sha256": controller.digest(controller.canonical(old))},
        text_free=True,
    )
    with pytest.raises(controller.ControllerError, match="preflight_rotation_blocked"):
        controller._install_preflight_receipts(package, successor, canary, canary)


def test_prepare_installs_preflight_under_execution_lock(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="prepare")
    execution = _temporary_file()
    calls: list[tuple[str, int | None]] = []
    monkeypatch.setattr(guardian, "_lock", lambda *_args: execution)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda _config, action, **kwargs: calls.append((action, kwargs.get("execution_fd")))
        or {"ok": True, "text_free": True},
    )
    monkeypatch.setattr(guardian, "_available_bytes", lambda _path: 123)
    result = guardian._prepare(config, [], provider_bindings=True)
    assert result["preflight_ready"] is True
    assert calls == [("preflight", calls[0][1])]
    assert isinstance(calls[0][1], int)


def test_prepare_without_bindings_is_provider_free(
    guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(guardian, tmp_path, action="prepare")
    monkeypatch.setattr(guardian, "_available_bytes", lambda _path: 123)
    result = guardian._prepare(config, [], provider_bindings=False)
    assert result["preflight_ready"] is False


def test_cli_help_is_available() -> None:
    completed = subprocess.run(
        [os.sys.executable, str(GUARDIAN_PATH), "--help"],
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0
    assert b"--execution-lock" in completed.stdout
    assert b"--through" in completed.stdout
