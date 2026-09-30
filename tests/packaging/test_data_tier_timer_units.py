"""Nightly data-tier user units and installer contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.orchestration import install_data_tier_timer


def test_data_tier_service_and_timer_contract() -> None:
    service = (install_data_tier_timer.TEMPLATE_DIR / install_data_tier_timer.UNITS[0]).read_text()
    timer = (install_data_tier_timer.TEMPLATE_DIR / install_data_tier_timer.UNITS[1]).read_text()
    assert "Type=oneshot" in service
    assert "WorkingDirectory=@REPO_ROOT@" in service
    assert "@REPO_ROOT@/.venv/bin/python -m scripts.ci.data_tier run" in service
    assert "TimeoutStartSec=" in service
    assert "TimeoutStopSec=900" in service
    assert "After=network.target" not in service
    assert "OnCalendar=*-*-* 02:15:00 UTC" in timer
    assert "Persistent=true" in timer
    assert "Unit=learn-ukrainian-data-tier.service" in timer
    assert "WantedBy=timers.target" in timer


def test_installer_check_apply_and_enable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / ".git").write_text("gitdir: linked")
    unit_dir = tmp_path / "units"
    calls = []
    monkeypatch.setattr(install_data_tier_timer, "verify_units", lambda _rendered: None)
    monkeypatch.setattr(install_data_tier_timer, "systemctl_user", lambda *args: calls.append(args))
    flags = ["--repo-root", str(primary), "--unit-dir", str(unit_dir)]
    assert install_data_tier_timer.main([*flags, "--check"]) == 1
    assert install_data_tier_timer.main([*flags, "--apply"]) == 0
    assert install_data_tier_timer.main([*flags, "--check"]) == 0
    assert install_data_tier_timer.main([*flags, "--apply", "--enable"]) == 0
    assert calls == [("daemon-reload",), ("daemon-reload",), ("enable", "--now", "learn-ukrainian-data-tier.timer")]
    assert all((unit_dir / name).stat().st_mode & 0o777 == 0o600 for name in install_data_tier_timer.UNITS)
    with pytest.raises(install_data_tier_timer.InstallError, match="primary checkout"):
        install_data_tier_timer.main(["--repo-root", str(linked), "--check"])
    with pytest.raises(install_data_tier_timer.InstallError, match="requires --apply"):
        install_data_tier_timer.main([*flags, "--enable"])


def test_rendered_units_pass_systemd_analyze(tmp_path: Path) -> None:
    rendered = install_data_tier_timer.render_units(Path(sys.executable).parents[2])
    if not install_data_tier_timer.shutil.which("systemd-analyze"):
        pytest.skip("systemd-analyze unavailable")
    paths = []
    for name, text in rendered.items():
        file = tmp_path / name
        file.write_text(text)
        paths.append(str(file))
    result = subprocess.run(
        ["systemd-analyze", "verify", *paths], capture_output=True, text=True, check=False, timeout=60
    )
    assert result.returncode == 0, result.stderr
