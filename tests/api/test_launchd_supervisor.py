"""Tests for persistent Monitor API launchd supervision."""

from __future__ import annotations

import json
import os
import plistlib
import stat
import subprocess
import sys
from pathlib import Path

from scripts.api import launchd_supervisor as supervisor


def test_rendered_plist_uses_throttled_abnormal_exit_restart(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    payload = plistlib.loads(supervisor.render_plist(repo_root=repo))

    assert payload["Label"] == supervisor.LABEL
    assert payload["KeepAlive"] == {"SuccessfulExit": False}
    assert payload["ThrottleInterval"] == supervisor.THROTTLE_INTERVAL_SECONDS
    assert payload["EnvironmentVariables"] == {
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    }
    assert payload["RunAtLoad"] is True
    assert payload["ProgramArguments"][0] == supervisor.STABLE_PROGRAM
    assert payload["ProgramArguments"] == [
        "/bin/bash",
        "--noprofile",
        "--norc",
        str(repo.resolve() / "scripts" / "api" / "run_monitor_api_supervisor.sh"),
        "run",
        "--repo-root",
        str(repo.resolve()),
    ]
    assert not any(".venv/bin/python" in part for part in payload["ProgramArguments"])


def test_api_child_disables_bytecode_writes(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "0")

    command, launch_dir, environment, release_line = supervisor._prepare_api_command(
        repo,
        live_mode=True,
        port=8765,
    )

    assert command[:4] == [
        str(repo / ".venv" / "bin" / "python"),
        "-B",
        "-m",
        "uvicorn",
    ]
    assert launch_dir == repo
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert release_line == "WARNING: API live mode enabled; serving mutable checkout code"

    inherited = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "import json, os, sys; "
                "print(json.dumps({'env': os.environ['PYTHONDONTWRITEBYTECODE'], "
                "'dont_write': sys.dont_write_bytecode}))"
            ),
        ],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True, timeout=30,
    )
    assert json.loads(inherited.stdout) == {"env": "1", "dont_write": True}


def test_install_and_uninstall_preserve_crash_evidence(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    interpreter = repo / ".venv" / "bin" / "python"
    implementation = repo / "scripts" / "api" / "launchd_supervisor.py"
    interpreter.parent.mkdir(parents=True)
    implementation.parent.mkdir(parents=True)
    interpreter.write_text("#!/bin/sh\n", encoding="utf-8")
    interpreter.chmod(0o755)
    implementation.write_text("# installed by test\n", encoding="utf-8")
    wrapper = repo / "scripts" / "api" / "run_monitor_api_supervisor.sh"
    wrapper.write_text("#!/bin/bash\n", encoding="utf-8")
    home = tmp_path / "home"

    installed = supervisor.install(repo_root=repo, home=home)
    evidence = supervisor.crash_record_path(repo)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text('{"exit_code": 9}\n', encoding="utf-8")
    monkeypatch.setattr(supervisor, "stop", lambda **_kwargs: {"loaded": False})

    removed = supervisor.uninstall(home=home)

    assert installed["changed"] is True
    assert removed["crash_evidence_preserved"] is True
    assert not supervisor.plist_path(home).exists()
    assert evidence.exists()


def test_status_rejects_plist_without_required_environment(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    destination = supervisor.plist_path(home)
    destination.parent.mkdir(parents=True)
    legacy_payload = supervisor.build_plist(repo_root=repo)
    legacy_payload.pop("EnvironmentVariables")
    destination.write_bytes(plistlib.dumps(legacy_payload))
    monkeypatch.setattr(
        supervisor,
        "_loaded_readback",
        lambda: subprocess.CompletedProcess(["launchctl", "print"], 0, "", ""),
    )

    stale_status, stale_exit = supervisor.status(home=home)

    assert stale_status["valid_plist"] is False
    assert stale_exit == 1

    destination.write_bytes(supervisor.render_plist(repo_root=repo))
    current_status, current_exit = supervisor.status(home=home)

    assert current_status["valid_plist"] is True
    assert current_exit == 0


def test_stop_disables_before_bootout(tmp_path: Path, monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_launchctl(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[0] == "print":
            return subprocess.CompletedProcess(command, 0 if len(commands) == 2 else 1, "", "not loaded")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(supervisor, "_launchctl", fake_launchctl)

    result = supervisor.stop(home=tmp_path / "home")

    assert result["loaded"] is False
    assert [command[0] for command in commands] == ["disable", "print", "bootout", "print"]


def test_stop_waits_for_delayed_launchd_unload(tmp_path: Path, monkeypatch) -> None:
    commands: list[list[str]] = []
    sleeps: list[float] = []
    print_results = iter([0, 0, 1])

    def fake_launchctl(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        returncode = next(print_results) if command[0] == "print" else 0
        return subprocess.CompletedProcess(command, returncode, "", "not loaded" if returncode else "")

    monkeypatch.setattr(supervisor, "_launchctl", fake_launchctl)
    monkeypatch.setattr(supervisor, "_sleep", sleeps.append)

    result = supervisor.stop(home=tmp_path / "home")

    assert result["loaded"] is False
    assert [command[0] for command in commands] == ["disable", "print", "bootout", "print", "print"]
    assert sleeps == [supervisor._STOP_UNLOAD_POLL_SECONDS]


def test_stop_fails_after_bounded_launchd_unload_wait(tmp_path: Path, monkeypatch) -> None:
    commands: list[list[str]] = []
    sleeps: list[float] = []
    clock = iter([100.0, 100.0, 112.0])

    def fake_launchctl(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, "service remains registered", "")

    monkeypatch.setattr(supervisor, "_launchctl", fake_launchctl)
    monkeypatch.setattr(supervisor, "_monotonic", lambda: next(clock))
    monkeypatch.setattr(supervisor, "_sleep", sleeps.append)

    try:
        supervisor.stop(home=tmp_path / "home")
    except supervisor.LaunchdError as exc:
        message = str(exc)
    else:
        raise AssertionError("stop() should fail when launchd never unloads the service")

    assert f"within {supervisor._STOP_UNLOAD_TIMEOUT_SECONDS:.1f}s after bootout" in message
    assert supervisor._target() in message
    assert "last launchctl print exit 0" in message
    assert [command[0] for command in commands] == ["disable", "print", "bootout", "print", "print"]
    assert sleeps == [supervisor._STOP_UNLOAD_POLL_SECONDS]


def test_unexpected_exit_records_signal_and_stderr_tail(tmp_path: Path) -> None:
    repo = tmp_path / "repo"

    def fake_prepare(
        _repo: Path,
        _live: bool,
        _port: int,
    ) -> tuple[list[str], Path, dict[str, str], str]:
        return (
            [
                sys.executable,
                "-c",
                "import os, sys; sys.stderr.write('fatal before kill\\n'); sys.stderr.flush(); os.kill(os.getpid(), 9)",
            ],
            repo,
            os.environ.copy(),
            "test launch",
        )

    assert supervisor.run_managed_api(repo_root=repo, prepare_command=fake_prepare) == 1

    record = json.loads(supervisor.crash_record_path(repo).read_text(encoding="utf-8"))
    assert record["exit_code"] == 137
    assert record["signal"] == "SIGKILL"
    assert record["stderr_tail"] == ["fatal before kill"]
    assert (repo / "logs" / "api.stderr.log").read_text(encoding="utf-8") == "fatal before kill\n"


def test_unexpected_clean_exit_is_recorded_and_restarted_by_launchd_contract(tmp_path: Path) -> None:
    repo = tmp_path / "repo"

    def fake_prepare(
        _repo: Path,
        _live: bool,
        _port: int,
    ) -> tuple[list[str], Path, dict[str, str], str]:
        return [sys.executable, "-c", "raise SystemExit(0)"], repo, os.environ.copy(), "test launch"

    assert supervisor.run_managed_api(repo_root=repo, prepare_command=fake_prepare) == 1

    record = json.loads(supervisor.crash_record_path(repo).read_text(encoding="utf-8"))
    assert record["exit_code"] == 0
    assert record["signal"] is None


def test_runner_rotates_api_log_before_each_launch(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "api.log"
    log_path.parent.mkdir(parents=True)
    log_path.write_bytes(b"A" * (supervisor._LOG_ROTATE_BYTES + 1))

    supervisor._rotate_log(log_path)

    rotated = log_path.with_name("api.log.1")
    assert rotated.exists()
    assert rotated.stat().st_size == supervisor._LOG_ROTATE_BYTES + 1


def test_status_rejects_venv_python_as_program(tmp_path: Path, monkeypatch) -> None:
    """Mutation-check: putting .venv/bin/python back in Program must fail status."""
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    destination = supervisor.plist_path(home)
    destination.parent.mkdir(parents=True)
    payload = supervisor.build_plist(repo_root=repo)
    payload["ProgramArguments"][0] = str(repo / ".venv" / "bin" / "python")
    destination.write_bytes(plistlib.dumps(payload))
    monkeypatch.setattr(
        supervisor,
        "_loaded_readback",
        lambda: subprocess.CompletedProcess(["launchctl", "print"], 0, "loaded", ""),
    )

    result, return_code = supervisor.status(home=home)

    assert return_code == 1
    assert result["valid_plist"] is False
    assert result["loaded"] is True


_WRAPPER = Path(__file__).resolve().parents[2] / "scripts" / "api" / "run_monitor_api_supervisor.sh"


def test_wrapper_exits_78_without_repo_root() -> None:
    proc = subprocess.run(
        ["/bin/bash", "--noprofile", "--norc", str(_WRAPPER)],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 78
    assert "missing --repo-root" in proc.stderr


def test_wrapper_exits_78_when_interpreter_missing(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            "/bin/bash",
            "--noprofile",
            "--norc",
            str(_WRAPPER),
            "run",
            "--repo-root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 78
    assert "missing interpreter" in proc.stderr
    assert str(tmp_path / ".venv" / "bin" / "python") in proc.stderr


def test_wrapper_execs_primary_interpreter(tmp_path: Path) -> None:
    """Mutation-check: the wrapper must exec primary .venv python, not PATH python."""
    primary = tmp_path / "primary"
    python = primary / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$@\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    python.chmod(python.stat().st_mode | stat.S_IXUSR)
    proc = subprocess.run(
        [
            "/bin/bash",
            "--noprofile",
            "--norc",
            str(_WRAPPER),
            "run",
            "--repo-root",
            str(primary),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env={**os.environ, "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0
    assert "-m" in proc.stdout
    assert "scripts.api.launchd_supervisor" in proc.stdout
    assert "run" in proc.stdout
    assert str(primary) in proc.stdout
