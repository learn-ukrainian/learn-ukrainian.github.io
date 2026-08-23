from __future__ import annotations

import plistlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.orchestration import install_mac_observer_launchd as launchd


def test_rendered_plist_runs_mac_observer_periodically(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"

    payload = plistlib.loads(
        launchd.render_plist(
            repo_root=repo,
            home=home,
            interval_minutes=8,
        )
    )

    assert payload["Label"] == launchd.LABEL
    assert payload["StartInterval"] == 480
    assert payload["RunAtLoad"] is True
    assert payload["ProgramArguments"][0] == launchd.STABLE_PROGRAM
    assert payload["ProgramArguments"] == [
        "/bin/bash",
        "--noprofile",
        "--norc",
        str(repo / "scripts" / "orchestration" / "run_mac_observer_heartbeat.sh"),
        "--repo-root",
        str(repo),
    ]
    assert "/opt/homebrew/bin" in payload["EnvironmentVariables"]["PATH"]
    assert not any(".venv/bin/python" in part for part in payload["ProgramArguments"])
    assert payload["StandardOutPath"] == str(home / ".codex" / "mac-observer" / "logs" / "stdout.log")
    assert payload["StandardErrorPath"] == str(home / ".codex" / "mac-observer" / "logs" / "stderr.log")


def test_status_rejects_modified_program_arguments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    destination = launchd.plist_path(home)
    destination.parent.mkdir(parents=True)
    payload = launchd.build_plist(
        repo_root=repo,
        home=home,
        interval_minutes=8,
    )
    payload["ProgramArguments"] = ["/bin/sh", "-c", "echo unsafe"]
    destination.write_bytes(plistlib.dumps(payload))

    class Result:
        returncode = 0
        stdout = "loaded"
        stderr = ""

    monkeypatch.setattr(launchd, "_loaded_readback", lambda: Result())

    result, return_code = launchd.status(
        repo_root=repo,
        home=home,
        interval_minutes=8,
    )

    assert return_code == 1
    assert result["loaded"] is True
    assert result["valid_plist"] is False


def test_install_is_verified_and_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    (repo / ".git").mkdir(parents=True)
    interpreter = repo / ".venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text("#!/bin/sh\n", encoding="utf-8")
    interpreter.chmod(0o755)
    script = repo / "scripts" / "orchestration" / "observer_heartbeat.py"
    script.parent.mkdir(parents=True)
    script.write_text("# heartbeat\n", encoding="utf-8")
    wrapper = repo / "scripts" / "orchestration" / "run_mac_observer_heartbeat.sh"
    wrapper.write_text("#!/bin/bash\n", encoding="utf-8")

    loaded_states = iter(
        [
            SimpleNamespace(returncode=1, stdout="", stderr="not loaded"),
            SimpleNamespace(returncode=0, stdout="loaded", stderr=""),
        ]
    )
    monkeypatch.setattr(launchd, "_loaded_readback", lambda: next(loaded_states))
    launchctl_calls: list[list[str]] = []

    def fake_launchctl(command: list[str]) -> SimpleNamespace:
        launchctl_calls.append(list(command))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(launchd, "_launchctl", fake_launchctl)

    first = launchd.install(
        repo_root=repo,
        home=home,
        interval_minutes=8,
    )

    assert first["changed"] is True
    assert first["loaded"] is True
    assert launchctl_calls == [
        [
            "bootstrap",
            launchd._domain(),
            str(launchd.plist_path(home)),
        ]
    ]
    expected = launchd.render_plist(
        repo_root=repo.resolve(),
        home=home,
        interval_minutes=8,
    )
    assert launchd.plist_path(home).read_bytes() == expected

    monkeypatch.setattr(
        launchd,
        "_loaded_readback",
        lambda: SimpleNamespace(returncode=0, stdout="loaded", stderr=""),
    )
    launchctl_calls.clear()

    second = launchd.install(
        repo_root=repo,
        home=home,
        interval_minutes=8,
    )

    assert second["changed"] is False
    assert second["wrote_plist"] is False
    assert launchctl_calls == []


def test_uninstall_removes_plist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    destination = launchd.plist_path(home)
    destination.parent.mkdir(parents=True)
    destination.write_text("plist", encoding="utf-8")

    class Result:
        returncode = 1
        stdout = ""
        stderr = "not loaded"

    monkeypatch.setattr(launchd, "_loaded_readback", lambda: Result())

    result = launchd.uninstall(home=home)

    assert result["loaded"] is False
    assert not destination.exists()


def test_status_rejects_venv_python_as_program(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mutation-check: putting .venv/bin/python back in Program must fail status."""
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    destination = launchd.plist_path(home)
    destination.parent.mkdir(parents=True)
    payload = launchd.build_plist(
        repo_root=repo,
        home=home,
        interval_minutes=8,
    )
    payload["ProgramArguments"][0] = str(repo / ".venv" / "bin" / "python")
    destination.write_bytes(plistlib.dumps(payload))

    class Result:
        returncode = 0
        stdout = "loaded"
        stderr = ""

    monkeypatch.setattr(launchd, "_loaded_readback", lambda: Result())

    result, return_code = launchd.status(
        repo_root=repo,
        home=home,
        interval_minutes=8,
    )

    assert return_code == 1
    assert result["valid_plist"] is False
    assert result["loaded"] is True


def test_positive_interval_validation() -> None:
    assert launchd.positive_interval("8") == 8
    with pytest.raises(Exception, match="positive integer"):
        launchd.positive_interval("0")
    with pytest.raises(Exception, match="positive integer"):
        launchd.positive_interval("-2")
    with pytest.raises(Exception, match="positive integer"):
        launchd.positive_interval("abc")
