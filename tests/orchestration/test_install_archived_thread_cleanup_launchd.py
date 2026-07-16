from __future__ import annotations

import plistlib
from pathlib import Path

from scripts.orchestration import install_archived_thread_cleanup_launchd as launchd


def test_rendered_plist_invokes_code_directly_once_per_week(tmp_path: Path) -> None:
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
    assert payload["ProgramArguments"] == [
        str(repo / ".venv" / "bin" / "python"),
        str(repo / "scripts" / "orchestration" / "archived_thread_cleanup.py"),
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
    assert payload["StartCalendarInterval"] == {"Hour": 3, "Minute": 0, "Weekday": 0}
    assert "prompt" not in str(payload).lower()


def test_atomic_write_is_idempotent(tmp_path: Path) -> None:
    destination = tmp_path / "LaunchAgents" / "job.plist"

    assert launchd.atomic_write(destination, b"first") is True
    assert launchd.atomic_write(destination, b"first") is False
    assert launchd.atomic_write(destination, b"second") is True
    assert destination.read_bytes() == b"second"


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
