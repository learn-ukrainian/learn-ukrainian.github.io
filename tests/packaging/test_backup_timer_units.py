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
    "learn-ukrainian-backup-alert@.service",
)
RENDERED_ROOT = "/srv/learn-ukrainian"


def _render(name: str) -> str:
    return (PACKAGING / name).read_text(encoding="utf-8").replace("@REPO_ROOT@", RENDERED_ROOT)


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


def test_installer_writes_owner_only_units_and_repairs_existing_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    existing = unit_dir / "learn-ukrainian-backup.service"
    existing.write_text("unchanged", encoding="utf-8")
    existing.chmod(0o644)
    monkeypatch.setattr(
        install_backup_timer,
        "systemctl_user",
        lambda *_args: subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
    )

    assert install_backup_timer.apply({existing.name: "unchanged"}, unit_dir, enable=False) == 0
    assert existing.stat().st_mode & 0o777 == 0o600

    assert install_backup_timer.apply({"learn-ukrainian-backup.timer": "new"}, unit_dir, enable=False) == 0
    assert (unit_dir / "learn-ukrainian-backup.timer").stat().st_mode & 0o777 == 0o600


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
