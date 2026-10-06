"""Tests for persistent Monitor API launchd supervision."""

from __future__ import annotations

import json
import os
import plistlib
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.api import launchd_supervisor as supervisor


def test_rendered_plist_uses_throttled_abnormal_exit_restart(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    payload = plistlib.loads(supervisor.render_plist(repo_root=repo))

    assert payload["Label"] == supervisor.LABEL
    assert payload["KeepAlive"] == {"SuccessfulExit": False}
    assert payload["ThrottleInterval"] == supervisor.THROTTLE_INTERVAL_SECONDS
    assert payload["EnvironmentVariables"] == {"PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
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
        text=True,
        timeout=30,
    )
    assert json.loads(inherited.stdout) == {"env": "1", "dont_write": True}


def _runtime_repo(tmp_path: Path) -> Path:
    """Create the interpreter, supervisor and wrapper that ``install`` validates."""
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
    return repo


def test_install_and_uninstall_preserve_crash_evidence(tmp_path: Path, monkeypatch) -> None:
    repo = _runtime_repo(tmp_path)
    home = tmp_path / "home"
    home.mkdir()

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


def test_install_writes_owner_only_plist_and_repairs_its_mode(tmp_path: Path) -> None:
    repo = _runtime_repo(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    destination = supervisor.plist_path(home)

    assert supervisor.install(repo_root=repo, home=home)["changed"] is True
    assert destination.read_bytes() == supervisor.render_plist(repo_root=repo)
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert supervisor.install(repo_root=repo, home=home)["changed"] is False
    destination.chmod(0o644)
    assert supervisor.install(repo_root=repo, home=home)["changed"] is True
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600


@pytest.mark.parametrize("linked", ["home", "Library", "LaunchAgents", "plist"])
def test_install_refuses_symlinked_plist_destinations(tmp_path: Path, monkeypatch, linked: str) -> None:
    """The plist never lands through a link at home, an ancestor, ``LaunchAgents`` or the plist itself (#9875)."""
    repo = _runtime_repo(tmp_path)
    home = tmp_path / "home"
    outside = tmp_path / "outside"
    outside.mkdir()
    link = {
        "home": home,
        "Library": home / "Library",
        "LaunchAgents": home / "Library" / "LaunchAgents",
        "plist": supervisor.plist_path(home),
    }[linked]
    link.parent.mkdir(parents=True, exist_ok=True)
    if linked == "plist":
        (outside / link.name).write_text("outside plist")
        link.symlink_to(outside / link.name)
    else:
        link.symlink_to(outside, target_is_directory=True)
    calls: list[object] = []
    monkeypatch.setattr(supervisor, "_launchctl", lambda command: calls.append(command))
    before = sorted(
        (path.relative_to(outside), path.read_bytes() if path.is_file() else b"") for path in outside.rglob("*")
    )

    for invoke in (
        lambda: supervisor.install(repo_root=repo, home=home),
        lambda: supervisor.start(repo_root=repo, home=home, live_mode=False),
    ):
        with pytest.raises(supervisor.InstallError, match="symlinked"):
            invoke()
    assert supervisor.main(["install", "--repo-root", str(repo), "--home", str(home)]) == 1

    after = sorted(
        (path.relative_to(outside), path.read_bytes() if path.is_file() else b"") for path in outside.rglob("*")
    )
    assert after == before
    assert calls == []
    assert link.is_symlink()


@pytest.mark.parametrize("linked", ["home", "Library", "LaunchAgents", "plist"])
def test_status_and_uninstall_refuse_symlinked_plist_destinations(
    tmp_path: Path, monkeypatch, capsys, linked: str
) -> None:
    """Status and uninstall refuse a link at home, an ancestor, ``LaunchAgents`` or the plist (#9875).

    The link target holds a valid plist either operation would otherwise read
    or delete; it stays byte-for-byte unchanged and launchctl is never called,
    so uninstall cannot disable or boot out the service first.
    """
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    outside = tmp_path / "outside"
    outside.mkdir()
    link = {
        "home": home,
        "Library": home / "Library",
        "LaunchAgents": home / "Library" / "LaunchAgents",
        "plist": supervisor.plist_path(home),
    }[linked]
    link.parent.mkdir(parents=True, exist_ok=True)
    # The file the operation would reach through the link.
    reached = Path(link.name) if linked == "plist" else supervisor.plist_path(home).relative_to(link)
    target = outside / reached
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(supervisor.render_plist(repo_root=repo))
    if linked == "plist":
        link.symlink_to(target)
    else:
        link.symlink_to(outside, target_is_directory=True)
    calls: list[object] = []
    monkeypatch.setattr(
        supervisor,
        "_launchctl",
        lambda command: calls.append(command) or subprocess.CompletedProcess(command, 0, "", ""),
    )

    def snapshot() -> list[tuple[Path, bytes]]:
        return sorted(
            (path.relative_to(outside), path.read_bytes() if path.is_file() else b"") for path in outside.rglob("*")
        )

    before = snapshot()

    for invoke in (lambda: supervisor.status(home=home), lambda: supervisor.uninstall(home=home)):
        with pytest.raises(supervisor.InstallError, match="symlinked"):
            invoke()
    for command in ("status", "uninstall"):
        assert supervisor.main([command, "--home", str(home)]) == 1
        assert "symlinked" in capsys.readouterr().err

    assert snapshot() == before
    assert calls == []
    assert link.is_symlink()


def test_status_reports_an_unreadable_plist(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    destination = supervisor.plist_path(home)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(supervisor.render_plist(repo_root=tmp_path / "repo"))
    destination.chmod(0)
    monkeypatch.setattr(
        supervisor,
        "_loaded_readback",
        lambda: subprocess.CompletedProcess(["launchctl", "print"], 0, "", ""),
    )
    if os.access(destination, os.R_OK):
        pytest.skip("permission bits do not restrict this user")

    result, returncode = supervisor.status(home=home)

    assert result["installed"] is True
    assert result["valid_plist"] is False
    assert "Permission denied" in str(result["parse_error"])
    assert returncode == 1


def test_uninstall_removes_the_plist_after_stopping(tmp_path: Path, monkeypatch) -> None:
    repo = _runtime_repo(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    supervisor.install(repo_root=repo, home=home)
    order: list[str] = []
    monkeypatch.setattr(
        supervisor,
        "stop",
        lambda **_kwargs: order.append("stop" if supervisor.plist_path(home).exists() else "late") or {},
    )

    assert supervisor.uninstall(home=home)["plist_existed"] is True
    assert order == ["stop"]
    assert not supervisor.plist_path(home).exists()
    assert supervisor.uninstall(home=home)["plist_existed"] is False


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
        "#!/bin/sh\nprintf '%s\\n' \"$@\"\nexit 0\n",
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


def test_launchctl_passes_timeout() -> None:
    fake = subprocess.CompletedProcess(["/bin/launchctl", "print", "gui/501/test"], 0, "", "")
    with patch("subprocess.run", return_value=fake) as run_mock:
        res = supervisor._launchctl(["print", "gui/501/test"])

    assert res == fake
    assert run_mock.call_args.kwargs.get("timeout") == supervisor.LAUNCHCTL_TIMEOUT_SECONDS


def test_launchctl_timeout_raises_launchd_error() -> None:
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["/bin/launchctl", "print"], supervisor.LAUNCHCTL_TIMEOUT_SECONDS),
    ):
        with pytest.raises(supervisor.LaunchdError, match=r"/bin/launchctl print timed out after 15\.0s"):
            supervisor._launchctl(["print"])


def test_prepare_api_command_passes_timeout(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    fake = subprocess.CompletedProcess(["git", "rev-parse"], 0, "a" * 40 + "\n", "")
    with (
        patch("subprocess.run", return_value=fake) as run_mock,
        patch.object(supervisor, "build_release", return_value=(repo / "releases" / "v1", False)),
        patch.object(supervisor, "prune_releases", return_value=type("PruneResult", (), {"removed": []})()),
    ):
        supervisor._prepare_api_command(repo, live_mode=False, port=8765)

    assert run_mock.call_args.kwargs.get("timeout") == supervisor.GIT_REV_PARSE_TIMEOUT_SECONDS


def test_prepare_api_command_timeout_raises_launchd_error(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "rev-parse"], supervisor.GIT_REV_PARSE_TIMEOUT_SECONDS),
    ):
        with pytest.raises(supervisor.LaunchdError, match=r"git rev-parse HEAD timed out after 15\.0s in"):
            supervisor._prepare_api_command(repo, live_mode=False, port=8765)
