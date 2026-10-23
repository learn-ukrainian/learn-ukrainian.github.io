"""Daily timer renders, verifies and installs safely without live activation."""

import pytest

from scripts.common.safe_unit_install import InstallError
from scripts.orchestration import install_issue_quality_report_timer as installer


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
