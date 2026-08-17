from __future__ import annotations

import os
import plistlib
import stat
import subprocess
from pathlib import Path

from scripts.orchestration import install_archived_thread_cleanup_launchd as launchd

_WRAPPER = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "orchestration"
    / "run_archived_thread_cleanup.sh"
)


def test_rendered_plist_uses_bash_wrapper_once_per_week(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    codex_binary = tmp_path / "bin" / "codex"
    codex_binary.parent.mkdir()
    codex_binary.write_text("#!/bin/sh\n", encoding="utf-8")
    codex_binary.chmod(0o755)

    payload = plistlib.loads(
        launchd.render_plist(
            repo_root=repo,
            home=home,
            codex_binary=codex_binary,
            weekday="sunday",
            hour=3,
        )
    )

    assert payload["Label"] == launchd.LABEL
    assert payload["ProgramArguments"][0] == launchd.STABLE_PROGRAM
    assert payload["ProgramArguments"] == [
        "/bin/bash",
        "--noprofile",
        "--norc",
        str(repo / "scripts" / "orchestration" / "run_archived_thread_cleanup.sh"),
        "--apply",
        "--repo-root",
        str(repo),
        "--retention-days",
        "30",
        "--observation-interval-days",
        "7",
        "--codex-binary",
        str(codex_binary),
    ]
    assert not any(".venv/bin/python" in part for part in payload["ProgramArguments"])
    assert payload["StartCalendarInterval"] == {"Hour": 3, "Minute": 0, "Weekday": 0}
    assert "prompt" not in str(payload).lower()


def test_atomic_write_is_idempotent(tmp_path: Path) -> None:
    destination = tmp_path / "LaunchAgents" / "job.plist"

    assert launchd.atomic_write(destination, b"first") is True
    assert launchd.atomic_write(destination, b"first") is False
    assert launchd.atomic_write(destination, b"second") is True
    assert destination.read_bytes() == b"second"
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600


def test_uninstall_preserves_cleanup_receipts(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "home"
    destination = launchd.plist_path(home)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"plist")
    receipts = launchd.state_dir(home) / "receipts" / "v1"
    receipts.mkdir(parents=True)
    receipt = receipts / "receipt.json"
    receipt.write_text("{}", encoding="utf-8")

    class Result:
        returncode = 1
        stdout = ""
        stderr = "not loaded"

    monkeypatch.setattr(launchd, "_loaded_readback", lambda: Result())

    result = launchd.uninstall(home=home)

    assert result["loaded"] is False
    assert not destination.exists()
    assert receipt.exists()


def test_status_rejects_loaded_plist_that_does_not_run_cleanup_code(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "home"
    destination = launchd.plist_path(home)
    destination.parent.mkdir(parents=True)
    payload = launchd.build_plist(
        repo_root=tmp_path / "repo",
        home=home,
        codex_binary=tmp_path / "bin" / "codex",
        weekday="sunday",
        hour=3,
    )
    payload["ProgramArguments"] = ["/bin/sh", "-c", "echo prompt"]
    destination.write_bytes(plistlib.dumps(payload))

    class Result:
        returncode = 0
        stdout = "loaded"
        stderr = ""

    monkeypatch.setattr(launchd, "_loaded_readback", lambda: Result())

    status, return_code = launchd.status(home=home)

    assert return_code == 1
    assert status["loaded"] is True
    assert status["valid_plist"] is False


def test_status_rejects_venv_python_as_program(tmp_path: Path, monkeypatch) -> None:
    """Mutation-check: putting .venv/bin/python back in Program must fail status."""
    home = tmp_path / "home"
    destination = launchd.plist_path(home)
    destination.parent.mkdir(parents=True)
    payload = launchd.build_plist(
        repo_root=tmp_path / "repo",
        home=home,
        codex_binary=tmp_path / "bin" / "codex",
        weekday="sunday",
        hour=3,
    )
    payload["ProgramArguments"][0] = str(tmp_path / "repo" / ".venv" / "bin" / "python")
    destination.write_bytes(plistlib.dumps(payload))

    class Result:
        returncode = 0
        stdout = "loaded"
        stderr = ""

    monkeypatch.setattr(launchd, "_loaded_readback", lambda: Result())

    status, return_code = launchd.status(home=home)

    assert return_code == 1
    assert status["valid_plist"] is False
    assert status["loaded"] is True


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
            "--apply",
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
    marker = tmp_path / "ran"
    python.write_text(
        "#!/bin/sh\n"
        f'echo "$1" > "{marker}"\n'
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
            "--apply",
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
    assert marker.read_text(encoding="utf-8").strip().endswith("archived_thread_cleanup.py")
    assert "--apply" in proc.stdout
    assert str(primary) in proc.stdout
