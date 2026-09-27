"""Linux-native systemd templates must supervise listeners, not oneshot services.sh."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.storage import install_data_volume_dropins as installer

PACKAGING = Path(__file__).resolve().parents[2] / "packaging" / "systemd"
UNITS = (
    "learn-ukrainian-api.service",
    "learn-ukrainian-sources.service",
    "learn-ukrainian-work.service",
    "learn-ukrainian-astro.service",
)
DROPINS = PACKAGING / "dropins"


def test_systemd_templates_are_type_simple() -> None:
    for name in UNITS:
        text = (PACKAGING / name).read_text(encoding="utf-8")
        assert "Type=simple" in text
        assert "Type=oneshot" not in text
        assert "RemainAfterExit" not in text
        assert "services.sh start" not in text
        if name != "learn-ukrainian-work.service":
            assert "127.0.0.1" in text


def test_api_supervisor_is_gated_for_linux() -> None:
    text = Path(__file__).resolve().parents[2].joinpath("services.sh").read_text(encoding="utf-8")
    assert "_api_supervisor_available" in text
    assert "SVC_API_SUPERVISOR_BIN" in text
    assert "command -v launchctl >/dev/null 2>&1" in text
    assert text.count("_api_supervisor_available") >= 3


def test_systemd_templates_have_no_host_facts() -> None:
    forbidden = ("atlas-runner", "hramatka", "46.", "HostName")
    for path in PACKAGING.iterdir():
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} leaked {token!r}"


@pytest.mark.repo_wide
def test_data_volume_dropins_cover_all_services_and_preserve_commands() -> None:
    timers = {path.stem + ".service" for path in PACKAGING.glob("*.timer")}
    expected = set(UNITS) | timers
    actual = {path.parent.name.removesuffix(".d") for path in DROPINS.glob("*.service.d/data-volume.conf")}
    assert actual == expected
    for unit in expected:
        original = (PACKAGING / unit).read_text(encoding="utf-8")
        command = next(
            line.removeprefix("ExecStart=") for line in original.splitlines() if line.startswith("ExecStart=")
        )
        dropin = (DROPINS / f"{unit}.d/data-volume.conf").read_text(encoding="utf-8")
        assert "ExecStart=\n" in dropin
        if unit == "learn-ukrainian-project-state-reporter.service":
            command = command.replace("%h/projects/learn-ukrainian", "@REPO_ROOT@")
            assert "WorkingDirectory=@REPO_ROOT@" in dropin
        assert f"/data_volume_guard.sh -- {command}" in dropin
        assert "RestartPreventExitStatus=78" in dropin


def test_data_volume_dropin_installer_previews(tmp_path: Path) -> None:
    destination = tmp_path / "user"
    command = [
        sys.executable,
        str(PACKAGING.parents[1] / "scripts/storage/install_data_volume_dropins.py"),
        "--destination",
        str(destination),
    ]
    preview = subprocess.run(command, text=True, capture_output=True, check=True, timeout=30)
    assert "data_volume_guard.sh" in preview.stdout
    assert not destination.exists()
    assert "@REPO_ROOT@" not in preview.stdout


def test_data_volume_dropin_installer_refuses_dispatch_worktree_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    destination = tmp_path / "user"
    worktree_root = Path(".worktrees") / "dispatch" / "codex" / "task" / "repo"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(installer, "REPO_ROOT", worktree_root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["install_data_volume_dropins.py", "--destination", str(destination), "--apply"],
    )

    with pytest.raises(SystemExit) as exc_info:
        installer.main()

    assert exc_info.value.code == 2
    assert "--apply must run from the primary checkout" in capsys.readouterr().err
    assert not destination.exists()


def test_data_volume_dropin_installer_applies_from_primary_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "user"
    monkeypatch.chdir(tmp_path)
    primary_root = Path("primary")
    (primary_root / ".git").mkdir(parents=True)
    monkeypatch.setattr(installer, "REPO_ROOT", primary_root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["install_data_volume_dropins.py", "--destination", str(destination), "--apply"],
    )
    assert installer.main() == 0
    files = list(destination.glob("*.service.d/data-volume.conf"))
    assert len(files) == 10
    assert all("@REPO_ROOT@" not in file.read_text(encoding="utf-8") for file in files)
