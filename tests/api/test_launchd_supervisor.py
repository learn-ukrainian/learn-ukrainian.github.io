"""Tests for persistent Monitor API launchd supervision."""

from __future__ import annotations

import json
import os
import plistlib
import subprocess
from pathlib import Path

from scripts.api import launchd_supervisor as supervisor

_ROOT = Path(__file__).resolve().parents[2]
_VENV_PYTHON = _ROOT / ".venv" / "bin" / "python"


def test_rendered_plist_uses_throttled_abnormal_exit_restart(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    payload = plistlib.loads(supervisor.render_plist(repo_root=repo))

    assert payload["Label"] == supervisor.LABEL
    assert payload["KeepAlive"] == {"SuccessfulExit": False}
    assert payload["ThrottleInterval"] == supervisor.THROTTLE_INTERVAL_SECONDS
    assert payload["RunAtLoad"] is True
    assert payload["ProgramArguments"] == [
        str(repo / ".venv" / "bin" / "python"),
        "-m",
        "scripts.api.launchd_supervisor",
        "run",
        "--repo-root",
        str(repo),
    ]


def test_install_and_uninstall_preserve_crash_evidence(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    interpreter = repo / ".venv" / "bin" / "python"
    implementation = repo / "scripts" / "api" / "launchd_supervisor.py"
    interpreter.parent.mkdir(parents=True)
    implementation.parent.mkdir(parents=True)
    interpreter.write_text("#!/bin/sh\n", encoding="utf-8")
    interpreter.chmod(0o755)
    implementation.write_text("# installed by test\n", encoding="utf-8")
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


def test_unexpected_exit_records_signal_and_stderr_tail(tmp_path: Path) -> None:
    repo = tmp_path / "repo"

    def fake_prepare(
        _repo: Path,
        _live: bool,
        _port: int,
    ) -> tuple[list[str], Path, dict[str, str], str]:
        return (
            [
                str(_VENV_PYTHON),
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
        return [str(_VENV_PYTHON), "-c", "raise SystemExit(0)"], repo, os.environ.copy(), "test launch"

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
