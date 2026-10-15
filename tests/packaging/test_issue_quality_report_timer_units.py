"""Daily timer renders, verifies and installs safely without live activation."""

import pytest

from scripts.common.safe_unit_install import InstallError
from scripts.orchestration import install_issue_quality_report_timer as installer


def test_timer_renders_and_verifies(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".venv/bin").mkdir(parents=True)
    interpreter = repo / ".venv/bin/python"
    interpreter.write_text("#!/bin/sh\nexit 0\n")
    interpreter.chmod(0o755)
    rendered = installer.render_units(repo)
    assert len(rendered) == 2
    assert all("@REPO_ROOT@" not in text for text in rendered.values())
    service = rendered[installer.UNITS[0]]
    timer = rendered[installer.UNITS[1]]
    assert "scripts.orchestration.issue_quality_report --publish --sender devops" in service
    assert "OnCalendar=*-*-* 07:00:00 UTC" in timer
    assert "Persistent=true" in timer
    installer.verify_units(rendered)


def test_install_preview_apply_idempotence_and_symlink_refusal(tmp_path, monkeypatch):
    units = tmp_path / "units"
    rendered = installer.render_units(tmp_path / "repo")
    assert installer.check(rendered, units) == 1
    assert not units.exists()
    calls = []
    monkeypatch.setattr(installer, "systemctl_user", lambda *a: calls.append(a))
    assert installer.apply(rendered, units, enable=False) == 0
    assert calls == [("daemon-reload",)]
    assert installer.check(rendered, units) == 0
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in units.iterdir())
    assert installer.apply(rendered, units, enable=False) == 0
    target = units / installer.UNITS[0]
    target.unlink()
    target.symlink_to(tmp_path / "elsewhere")
    with pytest.raises(InstallError):
        installer.apply(rendered, units, enable=False)


def test_installer_cli_constraints(tmp_path):
    with pytest.raises(SystemExit) as caught:
        installer.main(["--enable"])
    assert caught.value.code == 2
    with pytest.raises(SystemExit):
        installer.main(["--repo-root", str(tmp_path)])


def test_installer_main_checks_and_applies_only_fixture_units(tmp_path, monkeypatch):
    root = tmp_path / "primary"
    (root / ".git").mkdir(parents=True)
    destination = tmp_path / "user"
    calls = []
    monkeypatch.setattr(installer, "verify_units", lambda rendered: calls.append("verify"))
    monkeypatch.setattr(installer, "systemctl_user", lambda *a: calls.append(a))
    options = ["--repo-root", str(root), "--unit-dir", str(destination)]
    assert installer.main([*options, "--check"]) == 1
    assert installer.main([*options, "--apply", "--enable"]) == 0
    assert calls[-2:] == [("daemon-reload",), ("enable", "--now", installer.UNITS[1])]
    assert installer.main([*options, "--check"]) == 0
