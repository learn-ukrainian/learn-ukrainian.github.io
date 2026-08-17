"""Tests for the worktree-cleanup launchd red-run probe (#6937)."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.audit.check_worktree_cleanup_integrity import (
    STALE_AFTER,
    check_worktree_cleanup_integrity,
    latest_receipt_observed_at,
    parse_launchd_snapshot,
)
from scripts.orchestration import install_worktree_cleanup_launchd as launchd

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "orchestration" / "run_scheduled_worktree_cleanup.sh"


def _events(state_dir: Path) -> list[dict]:
    path = state_dir / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _write_plist(home: Path) -> Path:
    destination = launchd.plist_path(home)
    destination.parent.mkdir(parents=True)
    destination.write_text("plist", encoding="utf-8")
    return destination


def _write_receipt(home: Path, observed_at: datetime) -> Path:
    receipts = home / ".codex" / "worktree-cleanup" / "receipts" / "v2"
    receipts.mkdir(parents=True)
    stamp = observed_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = receipts / f"{stamp}-deadbeefcafe.json"
    path.write_text(
        json.dumps({"observed_at": observed_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}),
        encoding="utf-8",
    )
    return path


def test_parse_launchd_snapshot_reads_exit_78_and_lwcr_flag() -> None:
    snapshot = parse_launchd_snapshot(
        "state = not running\n"
        "last exit code = 78: EX_CONFIG\n"
        "properties = runatload | needs LWCR update | managed LWCR | has LWCR\n"
    )
    assert snapshot["last_exit"] == 78
    assert snapshot["needs_lwcr_update"] is True
    assert snapshot["lwcr_init_failure"] is False


def test_parse_launchd_snapshot_reads_lwcr_init_log_line() -> None:
    snapshot = parse_launchd_snapshot(
        "Service could not initialize: Unable to get updated LWCR for "
        "(A630D90B-7E3C-433C-9340-21C494BE92AF, "
        "/Users/example/Library/LaunchAgents/com.learn-ukrainian.worktree-cleanup.plist, "
        "501), error 0x3 - No such process"
    )
    assert snapshot["lwcr_init_failure"] is True
    assert snapshot["last_exit"] is None


def test_skips_when_job_is_not_installed(tmp_path: Path) -> None:
    ok, message = check_worktree_cleanup_integrity(
        tmp_path / "repo",
        home=tmp_path / "home",
        state_dir=tmp_path / "state",
        platform="darwin",
        launchctl_text=None,
    )
    assert ok is True
    assert "not installed" in message
    assert _events(tmp_path / "state") == []


def test_skips_on_non_darwin_even_with_installed_plist(tmp_path: Path) -> None:
    home = tmp_path / "home"
    _write_plist(home)
    ok, message = check_worktree_cleanup_integrity(
        tmp_path / "repo",
        home=home,
        state_dir=tmp_path / "state",
        platform="linux",
        launchctl_text="last exit code = 78: EX_CONFIG",
    )
    assert ok is True
    assert "not macOS" in message
    assert _events(tmp_path / "state") == []


def test_exit_78_alerts_even_with_fresh_receipt(tmp_path: Path) -> None:
    home = tmp_path / "home"
    _write_plist(home)
    now = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    _write_receipt(home, now - timedelta(minutes=10))

    ok, message = check_worktree_cleanup_integrity(
        tmp_path / "repo",
        home=home,
        state_dir=tmp_path / "state",
        now=now,
        platform="darwin",
        launchctl_text="last exit code = 78: EX_CONFIG\nproperties = needs LWCR update",
    )
    assert ok is False
    assert "LWCR" in message
    alerts = [event for event in _events(tmp_path / "state") if event["event"] == "worktree_cleanup_integrity_alert"]
    assert len(alerts) == 1
    assert alerts[0]["last_exit"] == 78
    assert alerts[0]["needs_lwcr_update"] is True


def test_stale_receipt_alerts_when_launchd_exit_is_zero(tmp_path: Path) -> None:
    home = tmp_path / "home"
    _write_plist(home)
    now = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    _write_receipt(home, now - STALE_AFTER - timedelta(minutes=1))

    ok, message = check_worktree_cleanup_integrity(
        tmp_path / "repo",
        home=home,
        state_dir=tmp_path / "state",
        now=now,
        platform="darwin",
        launchctl_text="last exit code = 0",
    )
    assert ok is False
    assert "stale" in message
    assert _events(tmp_path / "state")


def test_fresh_receipt_under_stale_bar_is_ok(tmp_path: Path) -> None:
    """Mutation-check: a receipt just inside the 8h bar must not alert."""
    home = tmp_path / "home"
    _write_plist(home)
    now = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    _write_receipt(home, now - STALE_AFTER + timedelta(minutes=5))

    ok, message = check_worktree_cleanup_integrity(
        tmp_path / "repo",
        home=home,
        state_dir=tmp_path / "state",
        now=now,
        platform="darwin",
        launchctl_text="last exit code = 0",
    )
    assert ok is True
    assert "ok" in message
    assert _events(tmp_path / "state") == []


def test_missing_receipt_with_installed_job_is_red(tmp_path: Path) -> None:
    home = tmp_path / "home"
    _write_plist(home)
    ok, message = check_worktree_cleanup_integrity(
        tmp_path / "repo",
        home=home,
        state_dir=tmp_path / "state",
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        platform="darwin",
        launchctl_text="last exit code = 0",
    )
    assert ok is False
    assert "no successful receipt" in message


def test_latest_receipt_ignores_corrupt_files(tmp_path: Path) -> None:
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    (receipts / "broken.json").write_text("{not-json", encoding="utf-8")
    (receipts / "20260815T144310Z-ok.json").write_text(
        json.dumps({"observed_at": "2026-08-15T14:43:10Z"}),
        encoding="utf-8",
    )
    assert latest_receipt_observed_at(receipts) == datetime(2026, 8, 15, 14, 43, 10, tzinfo=UTC)


def test_wrapper_exits_78_without_repo_root() -> None:
    proc = subprocess.run(
        ["/bin/bash", "--noprofile", "--norc", str(WRAPPER)],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 78
    assert "missing --repo-root" in proc.stderr


def test_wrapper_exits_78_when_interpreter_missing(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            "/bin/bash",
            "--noprofile",
            "--norc",
            str(WRAPPER),
            "--repo-root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 78
    assert "missing interpreter" in proc.stderr
    assert str(tmp_path / ".venv" / "bin" / "python") in proc.stderr


def test_wrapper_execs_primary_interpreter(tmp_path: Path) -> None:
    """Mutation-check: the wrapper must exec primary .venv python, not PATH python."""
    primary = tmp_path / "primary"
    python = primary / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    marker = tmp_path / "ran"
    python.write_text(
        "#!/bin/sh\n"
        f'echo "$1" > "{marker}"\n'
        "printf '%s\\n' \"$@\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    python.chmod(python.stat().st_mode | stat.S_IXUSR)
    # The wrapper execs the cleanup script next to itself; provide a real file
    # so the existence guard passes. The fake python records argv[1].
    proc = subprocess.run(
        [
            "/bin/bash",
            "--noprofile",
            "--norc",
            str(WRAPPER),
            "--apply",
            "--repo-root",
            str(primary),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env={**os.environ, "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0
    assert marker.read_text(encoding="utf-8").strip().endswith("scheduled_worktree_cleanup.py")
    assert "--apply" in proc.stdout
    assert str(primary) in proc.stdout
