"""Backup systemd user units carry the required contract and pass verify."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.orchestration import install_backup_timer

PACKAGING = Path(__file__).resolve().parents[2] / "packaging" / "systemd"
UNITS = (
    "learn-ukrainian-backup.service",
    "learn-ukrainian-backup.timer",
    "learn-ukrainian-backup-retention.service",
    "learn-ukrainian-backup-retention.timer",
)
RENDERED_ROOT = "/srv/learn-ukrainian"


def _render(name: str) -> str:
    return (PACKAGING / name).read_text(encoding="utf-8").replace("@REPO_ROOT@", RENDERED_ROOT)


def test_backup_service_contract() -> None:
    service = _render("learn-ukrainian-backup.service")
    assert "Type=oneshot" in service
    assert "EnvironmentFile=%h/.secrets/learn-ukrainian-backup.env" in service
    assert f"WorkingDirectory={RENDERED_ROOT}" in service
    assert f"LU_BACKUP_TMPDIR={RENDERED_ROOT}/data/.backup-staging" in service
    assert "Nice=15" in service
    assert "IOSchedulingClass=idle" in service
    assert "TimeoutStartSec=" in service
    assert "run_scheduled_backup.sh" in service
    # #8804 guarded-start is not on main: the data-volume guard must remain a
    # visible TODO until the drop-in mechanism merges.
    assert "TODO(#8804)" in service


def test_backup_timer_contract() -> None:
    timer = _render("learn-ukrainian-backup.timer")
    assert "OnCalendar=*-*-* 03:30:00 UTC" in timer
    assert "Persistent=true" in timer
    assert "RandomizedDelaySec=15min" in timer
    assert "Unit=learn-ukrainian-backup.service" in timer


def test_retention_units_run_weekly_tag_scoped_forget() -> None:
    service = _render("learn-ukrainian-backup-retention.service")
    assert "Type=oneshot" in service
    assert "run_scheduled_backup.sh retention" in service
    assert "EnvironmentFile=%h/.secrets/learn-ukrainian-backup.env" in service
    timer = _render("learn-ukrainian-backup-retention.timer")
    assert timer.count("OnCalendar=") == 1
    assert "OnCalendar=Sun" in timer
    assert "Persistent=true" in timer


def test_installer_accepts_primary_checkout_and_rejects_linked_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    primary = tmp_path / "primary"
    primary.mkdir()
    (primary / ".git").mkdir()
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / ".git").write_text("gitdir: ../primary/.git/worktrees/linked\n", encoding="utf-8")
    monkeypatch.setattr(install_backup_timer, "verify_units", lambda *_args, **_kwargs: "verified")
    monkeypatch.setattr(install_backup_timer, "preview", lambda *_args: 0)

    assert install_backup_timer.main(["--repo-root", str(primary), "--unit-dir", str(tmp_path / "units")]) == 0
    with pytest.raises(install_backup_timer.InstallError, match="must be the primary checkout"):
        install_backup_timer.main(["--repo-root", str(linked), "--unit-dir", str(tmp_path / "units")])


@pytest.mark.skipif(shutil.which("systemd-analyze") is None, reason="systemd-analyze unavailable")
def test_rendered_units_pass_systemd_analyze_verify(tmp_path: Path) -> None:
    paths = []
    for name in UNITS:
        rendered = tmp_path / name
        rendered.write_text(_render(name), encoding="utf-8")
        paths.append(str(rendered))

    result = subprocess.run(
        ["systemd-analyze", "verify", *paths],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert "learn-ukrainian-backup" not in result.stderr
