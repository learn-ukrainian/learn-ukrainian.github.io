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
    )

    assert commands[0][0] == os.fspath(launcher)
    assert commands[0][0] != os.fspath(target)
    assert expected_python_sha256 == controller._python_executable_sha256()
    assert controller._require_python_binding(expected_python_sha256) == target


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


def test_prepare_path_never_invokes_controller(guardian: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config(guardian, tmp_path, action="prepare")
    monkeypatch.setattr(guardian, "_config", lambda _args: config)
    monkeypatch.setattr(guardian, "_lock", lambda *_args: _temporary_file())
    monkeypatch.setattr(guardian, "_ensure_mounts", lambda *_args, **_kwargs: [{"name": name} for name in guardian.OUTPUT_ROOTS])
    monkeypatch.setattr(guardian, "_require_free_space", lambda *_args: 100)
    monkeypatch.setattr(guardian, "_available_bytes", lambda *_args: 100)
    monkeypatch.setattr(
        guardian,
        "_invoke_controller",
        lambda *_args, **_kwargs: pytest.fail("prepare invoked controller"),
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
