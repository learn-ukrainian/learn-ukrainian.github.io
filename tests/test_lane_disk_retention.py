"""Tests for the read-only lane disk retention scanner (#4956)."""

from __future__ import annotations

import time
from pathlib import Path

from scripts.hygiene.lane_disk_retention import scan_dispatch_worktrees


def test_scan_dispatch_worktrees_empty(tmp_path: Path) -> None:
    assert scan_dispatch_worktrees(repo_root=tmp_path) == []


def test_scan_dispatch_worktrees_reports_stale(tmp_path: Path, monkeypatch) -> None:
    wt = tmp_path / ".worktrees" / "dispatch" / "grok" / "old-task"
    wt.mkdir(parents=True)
    (wt / ".git").mkdir()
    # Pretend git commands
    def fake_git(args, *, cwd):
        if args[:2] == ["rev-parse", "--abbrev-ref"]:
            return "grok/old-task"
        if args[0] == "status":
            return " M file.py"
        if args[0] == "rev-list":
            return "0\t2"
        return ""

    monkeypatch.setattr("scripts.hygiene.lane_disk_retention._git", fake_git)
    old = time.time() - (80 * 3600)
    # set mtime via os.utime
    import os

    os.utime(wt, (old, old))
    reports = scan_dispatch_worktrees(repo_root=tmp_path, stale_hours=72)
    assert len(reports) == 1
    assert reports[0].dirty is True
    assert reports[0].ahead_of_remote is True
    assert "stale" in reports[0].recommendation
