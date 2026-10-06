"""Daily temp-sweep user units and installer contract (#9737)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.orchestration import install_tmp_sweep_timer as installer


def test_service_and_timer_contract() -> None:
    service = (installer.TEMPLATE_DIR / installer.UNITS[0]).read_text()
    timer = (installer.TEMPLATE_DIR / installer.UNITS[1]).read_text()
    assert "Type=oneshot" in service
    assert "WorkingDirectory=@REPO_ROOT@" in service
    starts = [line for line in service.splitlines() if line.startswith("ExecStart=")]
    assert starts == [
        "ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.hygiene.batch_state_retention",
        "ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --apply --summary",
    ]
    assert "PrivateTmp" not in service  # the sweep must see the real system temp area
    assert "OnCalendar=*-*-* 05:30:00 UTC" in timer
    assert "Persistent=true" in timer
    assert "Unit=learn-ukrainian-tmp-sweep.service" in timer
    assert "WantedBy=timers.target" in timer


def test_installer_check_apply_and_enable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / ".git").write_text("gitdir: linked")
    unit_dir = tmp_path / "units"
    calls = []
    monkeypatch.setattr(installer, "verify_units", lambda _rendered: None)
    monkeypatch.setattr(installer, "systemctl_user", lambda *args: calls.append(args))
    flags = ["--repo-root", str(primary), "--unit-dir", str(unit_dir)]
    assert installer.main([*flags, "--check"]) == 1
    assert installer.main([*flags, "--apply"]) == 0
    assert installer.main([*flags, "--check"]) == 0
    assert installer.main([*flags, "--apply", "--enable"]) == 0
    assert calls == [("daemon-reload",), ("daemon-reload",), ("enable", "--now", "learn-ukrainian-tmp-sweep.timer")]
    assert all((unit_dir / name).stat().st_mode & 0o777 == 0o600 for name in installer.UNITS)
    assert f"WorkingDirectory={primary.resolve()}" in (unit_dir / installer.UNITS[0]).read_text()
    with pytest.raises(installer.InstallError, match="primary checkout"):
        installer.main(["--repo-root", str(linked), "--check"])
    with pytest.raises(installer.InstallError, match="requires --apply"):
        installer.main([*flags, "--enable"])
    with pytest.raises(installer.InstallError, match="mutually exclusive"):
        installer.main([*flags, "--check", "--apply"])


def test_rendered_units_pass_systemd_analyze(tmp_path: Path) -> None:
    rendered = installer.render_units(Path(sys.executable).parents[2])
    if not shutil.which("systemd-analyze"):
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
