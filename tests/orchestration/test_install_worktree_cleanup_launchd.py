from __future__ import annotations

import plistlib
from pathlib import Path
from types import SimpleNamespace

from scripts.orchestration import install_worktree_cleanup_launchd as launchd


def test_rendered_plist_runs_both_repositories_every_fifteen_minutes(
    tmp_path: Path,
) -> None:
    public = tmp_path / "public"
    private = tmp_path / "private"
    home = tmp_path / "home"

    payload = plistlib.loads(
        launchd.render_plist(
            public_repo=public,
            private_repo=private,
            home=home,
            interval_minutes=15,
        )
    )

    assert payload["Label"] == launchd.LABEL
    assert payload["StartInterval"] == 900
    assert payload["RunAtLoad"] is True
    assert payload["ProgramArguments"] == [
        str(public / ".venv" / "bin" / "python"),
        str(public / "scripts" / "orchestration" / "scheduled_worktree_cleanup.py"),
        "--apply",
        "--repo-root",
        str(public),
        "--repo-root",
        str(private),
        "--receipt-dir",
        str(home / ".codex" / "worktree-cleanup" / "receipts" / "v1"),
    ]
    assert "/opt/homebrew/bin" in payload["EnvironmentVariables"]["PATH"]


def test_status_rejects_modified_program_arguments(tmp_path: Path, monkeypatch) -> None:
    public = tmp_path / "public"
    private = tmp_path / "private"
    home = tmp_path / "home"
    destination = launchd.plist_path(home)
    destination.parent.mkdir(parents=True)
    payload = launchd.build_plist(
        public_repo=public,
        private_repo=private,
        home=home,
        interval_minutes=15,
    )
    payload["ProgramArguments"] = ["/bin/sh", "-c", "echo unsafe"]
    destination.write_bytes(plistlib.dumps(payload))

    class Result:
        returncode = 0
        stdout = "loaded"
        stderr = ""

    monkeypatch.setattr(launchd, "_loaded_readback", lambda: Result())

    result, return_code = launchd.status(
        public_repo=public,
        private_repo=private,
        home=home,
        interval_minutes=15,
    )

    assert return_code == 1
    assert result["loaded"] is True
    assert result["valid_plist"] is False


def test_install_is_verified_and_idempotent(tmp_path: Path, monkeypatch) -> None:
    public = tmp_path / "public"
    private = tmp_path / "private"
    home = tmp_path / "home"
    for repo in (public, private):
        (repo / ".git").mkdir(parents=True)
    interpreter = public / ".venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text("#!/bin/sh\n", encoding="utf-8")
    interpreter.chmod(0o755)
    script = public / "scripts" / "orchestration" / "scheduled_worktree_cleanup.py"
    script.parent.mkdir(parents=True)
    script.write_text("# cleanup\n", encoding="utf-8")
    monkeypatch.setattr(
        launchd.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="main\n",
            stderr="",
        ),
    )

    loaded_states = iter(
        [
            SimpleNamespace(returncode=1, stdout="", stderr="not loaded"),
            SimpleNamespace(returncode=0, stdout="loaded", stderr=""),
        ]
    )
    monkeypatch.setattr(launchd, "_loaded_readback", lambda: next(loaded_states))
    launchctl_calls: list[list[str]] = []

    def fake_launchctl(command):
        launchctl_calls.append(list(command))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(launchd, "_launchctl", fake_launchctl)

    first = launchd.install(
        public_repo=public,
        private_repo=private,
        home=home,
        interval_minutes=15,
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
        public_repo=public.resolve(),
        private_repo=private.resolve(),
        home=home,
        interval_minutes=15,
    )
    assert launchd.plist_path(home).read_bytes() == expected

    monkeypatch.setattr(
        launchd,
        "_loaded_readback",
        lambda: SimpleNamespace(returncode=0, stdout="loaded", stderr=""),
    )
    launchctl_calls.clear()

    second = launchd.install(
        public_repo=public,
        private_repo=private,
        home=home,
        interval_minutes=15,
    )

    assert second["changed"] is False
    assert second["wrote_plist"] is False
    assert launchctl_calls == []


def test_uninstall_preserves_receipts(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    destination = launchd.plist_path(home)
    destination.parent.mkdir(parents=True)
    destination.write_text("plist", encoding="utf-8")
    receipt = launchd.state_dir(home) / "receipts" / "v1" / "receipt.json"
    receipt.parent.mkdir(parents=True)
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


def test_positive_interval_rejects_zero() -> None:
    try:
        launchd.positive_interval("0")
    except Exception as exc:
        assert "positive integer" in str(exc)
    else:
        raise AssertionError("zero interval unexpectedly accepted")
