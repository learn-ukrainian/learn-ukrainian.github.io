"""The deletion backstop is daily and cannot start during a check."""

from pathlib import Path

import pytest

from scripts.common.safe_unit_install import InstallError
from scripts.orchestration import install_preserved_retention_timer as installer


def test_daily_backstop_expires_24h_only_after_explicit_install_and_enable(tmp_path, monkeypatch):
    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    units = tmp_path / "units"
    calls = []
    monkeypatch.setattr(installer, "verify_units", lambda _: None)
    monkeypatch.setattr(installer, "systemctl_user", lambda *args: calls.append(args))
    args = ["--repo-root", str(primary), "--unit-dir", str(units)]
    assert installer.main(args) == 1
    assert not units.exists() and calls == []
    assert installer.main([*args, "--apply"]) == 0
    assert calls == [("daemon-reload",)]
    assert installer.main([*args, "--check"]) == 0
    assert installer.main([*args, "--apply", "--enable"]) == 0
    assert calls[-1] == ("enable", "--now", installer.UNITS[1])
    service, timer = [Path(units / name).read_text() for name in installer.UNITS]
    assert "--expire-older-than-hours 24 --allow-empty-keep-list --apply" in service
    assert "OnCalendar=*-*-* 04:45:00 UTC" in timer and "Persistent=true" in timer
    assert all((units / name).stat().st_mode & 0o777 == 0o600 for name in installer.UNITS)
    with pytest.raises(SystemExit):
        installer.main([*args, "--enable"])


def test_backstop_installer_never_writes_through_symlink(tmp_path):
    victim = tmp_path / "victim"
    victim.write_text("unchanged")
    units = tmp_path / "units"
    units.mkdir()
    (units / installer.UNITS[0]).symlink_to(victim)
    with pytest.raises(InstallError):
        installer.install(installer.render_units(tmp_path), units, apply=True, enable=False)
    assert victim.read_text() == "unchanged"


def test_vanished_unit_directory_cannot_redirect_backstop_units(tmp_path, monkeypatch):
    monkeypatch.setattr(installer, "open_unit_dir", lambda *a, **kw: None)
    with pytest.raises(InstallError, match="vanished"):
        installer.install(installer.render_units(tmp_path), tmp_path / "units", apply=True, enable=False)
