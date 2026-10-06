"""Every unit installer refuses symlinked destinations and never writes through a link (#9875).

Each installer gets the same matrix: a symlinked unit directory, a symlinked
unit file and a symlinked ancestor between home and the unit directory are each
refused in the installer's read-only mode and in its write mode, with the
outside target untouched; and a link planted at the unit name just before the
rename is replaced by the real unit, never written through.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.common import safe_unit_install
from scripts.common.safe_unit_install import InstallError
from scripts.orchestration import (
    install_archived_thread_cleanup_launchd,
    install_backup_timer,
    install_data_tier_timer,
    install_mac_observer_launchd,
    install_mac_project_state_launchd,
    install_tmp_sweep_timer,
    install_worktree_cleanup_launchd,
)
from scripts.storage import install_data_volume_dropins

MODES = ("check", "apply")


@dataclass
class Installer:
    module: object
    unit: Path  # the unit file whose directory and ancestors are attacked
    ancestor: Path  # a directory strictly between home and the unit directory
    invoke: Callable[[str], object]  # run the installer in "check" or "apply" mode


def _primary(tmp_path: Path) -> Path:
    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True, exist_ok=True)
    return primary


def _executable(path: Path, text: str = "#!/bin/sh\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def _launchctl_ok(*_args: object, **_kwargs: object) -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout="", stderr="")


def _tmp_sweep(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Installer:
    module = install_tmp_sweep_timer
    unit_dir = home / ".config" / "systemd" / "user"
    monkeypatch.setattr(module, "verify_units", lambda _rendered: None)
    monkeypatch.setattr(module, "systemctl_user", lambda *_args: None)
    flags = ["--repo-root", str(_primary(tmp_path)), "--unit-dir", str(unit_dir)]
    return Installer(module, unit_dir / module.UNITS[0], home / ".config", lambda mode: module.main([*flags, f"--{mode}"]))


def _data_tier(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Installer:
    module = install_data_tier_timer
    unit_dir = home / ".config" / "systemd" / "user"
    monkeypatch.setattr(module, "verify_units", lambda _rendered: None)
    monkeypatch.setattr(module, "systemctl_user", lambda *_args: None)
    flags = ["--repo-root", str(_primary(tmp_path)), "--unit-dir", str(unit_dir)]
    return Installer(module, unit_dir / module.UNITS[0], home / ".config", lambda mode: module.main([*flags, f"--{mode}"]))


def _backup(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Installer:
    module = install_backup_timer
    unit_dir = home / ".config" / "systemd" / "user"
    monkeypatch.setattr(module, "verify_units", lambda *_args, **_kwargs: "verified")
    monkeypatch.setattr(
        module, "systemctl_user", lambda *_args: subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    )
    flags = ["--repo-root", str(_primary(tmp_path)), "--unit-dir", str(unit_dir)]
    # The backup installer's read-only mode is its default preview.
    return Installer(
        module,
        unit_dir / module.UNIT_NAMES[0],
        home / ".config",
        lambda mode: module.main([*flags, "--apply"] if mode == "apply" else flags),
    )


def _dropins(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Installer:
    module = install_data_volume_dropins
    destination = home / ".config" / "systemd" / "user"
    first = sorted(module.TEMPLATE_ROOT.glob("*.service.d/data-volume.conf"))[0]
    monkeypatch.setattr(module, "REPO_ROOT", _primary(tmp_path))

    def invoke(mode: str) -> object:
        argv = ["install_data_volume_dropins.py", "--destination", str(destination)]
        monkeypatch.setattr(sys, "argv", [*argv, "--apply"] if mode == "apply" else argv)
        return module.main()

    # The drop-in installer's read-only mode is its default preview.
    return Installer(module, destination / first.parent.name / first.name, home / ".config", invoke)


def _archived(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Installer:
    module = install_archived_thread_cleanup_launchd
    repo = _primary(tmp_path)
    _executable(repo / ".venv" / "bin" / "python")
    _executable(repo / "scripts" / "orchestration" / "archived_thread_cleanup.py")
    _executable(module.wrapper_path(repo))
    codex = tmp_path / "bin" / "codex"
    _executable(codex)
    loaded = iter([SimpleNamespace(returncode=1, stdout="", stderr="not loaded")])
    monkeypatch.setattr(module, "_loaded_readback", lambda: next(loaded, _launchctl_ok()))
    monkeypatch.setattr(module, "_launchctl", _launchctl_ok)
    install = ["install", "--home", str(home), "--repo-root", str(repo), "--codex-binary", str(codex)]
    return Installer(
        module,
        module.plist_path(home),
        home / "Library",
        lambda mode: module.main(install if mode == "apply" else ["status", "--home", str(home)]),
    )


def _observer(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Installer:
    module = install_mac_observer_launchd
    repo = _primary(tmp_path)
    _executable(repo / ".venv" / "bin" / "python")
    _executable(repo / "scripts" / "orchestration" / "observer_heartbeat.py")
    _executable(module.wrapper_path(repo))
    loaded = iter([SimpleNamespace(returncode=1, stdout="", stderr="not loaded")])
    monkeypatch.setattr(module, "_loaded_readback", lambda: next(loaded, _launchctl_ok()))
    monkeypatch.setattr(module, "_launchctl", _launchctl_ok)
    flags = ["--repo-root", str(repo), "--home", str(home)]
    return Installer(
        module,
        module.plist_path(home),
        home / "Library",
        lambda mode: module.main([*flags, "install" if mode == "apply" else "status"]),
    )


def _project_state(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Installer:
    module = install_mac_project_state_launchd
    monkeypatch.setattr(module, "_launchctl", _launchctl_ok)
    flags = ["--repo-root", str(_primary(tmp_path)), "--home", str(home)]
    # The project-state installer's read-only mode is --dry-run.
    return Installer(
        module,
        module.plist_path(home),
        home / "Library",
        lambda mode: module.main(flags if mode == "apply" else [*flags, "--dry-run"]),
    )


def _worktree(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Installer:
    module = install_worktree_cleanup_launchd
    public = _primary(tmp_path)
    private = tmp_path / "private"
    (private / ".git").mkdir(parents=True)
    monkeypatch.setattr(module, "_validate_primary", lambda *_args, **_kwargs: None)
    loaded = iter([SimpleNamespace(returncode=1, stdout="", stderr="not loaded")])
    monkeypatch.setattr(module, "_loaded_readback", lambda: next(loaded, _launchctl_ok()))
    monkeypatch.setattr(module, "_launchctl", _launchctl_ok)
    flags = ["--public-repo", str(public), "--private-repo", str(private), "--home", str(home)]
    return Installer(
        module,
        module.plist_path(home),
        home / "Library",
        lambda mode: module.main([*flags, "install" if mode == "apply" else "status"]),
    )


INSTALLERS = {
    "tmp_sweep": _tmp_sweep,
    "data_tier": _data_tier,
    "backup": _backup,
    "data_volume_dropins": _dropins,
    "archived_thread_cleanup": _archived,
    "mac_observer": _observer,
    "mac_project_state": _project_state,
    "worktree_cleanup": _worktree,
}


@pytest.fixture(params=sorted(INSTALLERS))
def installer(request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Installer:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return INSTALLERS[request.param](tmp_path, home, monkeypatch)


def _refusal(installer: Installer, mode: str, capsys: pytest.CaptureFixture[str]) -> str:
    """Run the installer and return its refusal message; fail if it succeeded."""
    capsys.readouterr()
    try:
        result = installer.invoke(mode)
    except InstallError as error:
        return str(error)
    except SystemExit as error:  # the drop-in installer exits 1 with the reason on stderr
        assert error.code == 1
        return capsys.readouterr().err
    # The archived-thread installer reports failures as a JSON error and exit status 1.
    assert result == 1
    return json.loads(capsys.readouterr().out.strip().splitlines()[-1])["error"]


def _snapshot(root: Path) -> list[tuple[str, str, int]]:
    return sorted(
        (str(path.relative_to(root)), path.read_text() if path.is_file() else "", path.lstat().st_mode)
        for path in [root, *root.rglob("*")]
    )


@pytest.mark.parametrize("mode", MODES)
def test_symlinked_unit_directory_is_refused(
    installer: Installer, mode: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    outside = tmp_path / "outside-units"
    outside.mkdir()
    (outside / installer.unit.name).write_text("outside unit")
    installer.unit.parent.parent.mkdir(parents=True, exist_ok=True)
    installer.unit.parent.symlink_to(outside, target_is_directory=True)
    before = _snapshot(outside)

    message = _refusal(installer, mode, capsys)

    assert "symlinked path component" in message and installer.unit.parent.name in message
    assert _snapshot(outside) == before
    assert installer.unit.parent.is_symlink()


@pytest.mark.parametrize("mode", MODES)
def test_symlinked_unit_file_is_refused(
    installer: Installer, mode: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    outside = tmp_path / "outside-unit"
    outside.write_text("outside unit")
    outside.chmod(0o400)
    installer.unit.parent.mkdir(parents=True, exist_ok=True)
    installer.unit.symlink_to(outside)

    message = _refusal(installer, mode, capsys)

    assert "symlinked unit file" in message
    assert outside.read_text() == "outside unit" and outside.stat().st_mode & 0o777 == 0o400
    assert installer.unit.is_symlink()
    assert [path.name for path in installer.unit.parent.iterdir()] == [installer.unit.name]


@pytest.mark.parametrize("mode", MODES)
def test_symlinked_ancestor_is_refused(
    installer: Installer, mode: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    outside = tmp_path / "outside-ancestor"
    real_unit = outside / installer.unit.relative_to(installer.ancestor)
    real_unit.parent.mkdir(parents=True)
    real_unit.write_text("outside unit")
    installer.ancestor.symlink_to(outside, target_is_directory=True)
    before = _snapshot(outside)

    message = _refusal(installer, mode, capsys)

    assert "symlinked path component" in message and str(installer.ancestor) in message
    assert _snapshot(outside) == before
    assert installer.ancestor.is_symlink()


def test_link_raced_in_before_rename_is_replaced(
    installer: Installer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A link planted at the unit name after the check is replaced by the rename, never written through."""
    outside = tmp_path / "outside-unit"
    outside.write_text("outside unit")
    outside.chmod(0o644)
    real_write = safe_unit_install.write_unit
    raced: list[str] = []

    def racing_write(dir_fd: int, name: str, content: bytes, *, mode: int) -> None:
        os.symlink(outside, name, dir_fd=dir_fd)
        raced.append(name)
        real_write(dir_fd, name, content, mode=mode)

    monkeypatch.setattr(safe_unit_install, "write_unit", racing_write)
    if hasattr(installer.module, "write_unit"):
        monkeypatch.setattr(installer.module, "write_unit", racing_write)

    result = installer.invoke("apply")

    assert result == 0, capsys.readouterr()
    assert installer.unit.name in raced
    assert outside.read_text() == "outside unit" and outside.stat().st_mode & 0o777 == 0o644
    assert not installer.unit.is_symlink() and installer.unit.is_file()
    assert installer.unit.read_bytes() != b"outside unit"
    assert not [path.name for path in installer.unit.parent.iterdir() if path.name.endswith(".tmp")]
