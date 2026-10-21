"""Once-per-crossing cto alert for the disk reap watermark (#10871)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.orchestration import backup_failure_alert as alerts
from scripts.orchestration import disk_watermark_alert as watermark
from scripts.orchestration import dispatch_admission as adm
from scripts.orchestration import scheduled_worktree_cleanup as cleanup

_GIB = 1024**3
_LIMITS = adm.Thresholds(max_live_write_workers=2, min_mem_available_gib=3.5, max_load_per_cpu=1.5)


def _disk(used_percent: float) -> adm.DiskProbe:
    used = int(400 * _GIB * used_percent / 100)
    return adm.DiskProbe(used_bytes=used, free_bytes=400 * _GIB - used)


class _Recorder:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[tuple[str, str]] = []
        self.fail = fail

    def __call__(self, message: str, key: str) -> None:
        if self.fail:
            raise alerts.AlertError("fleet_comms publish exited 1: plane unavailable")
        self.calls.append((message, key))


def _run(tmp_path: Path, used: float, publish: _Recorder, stamp: str) -> str:
    return watermark.check_and_alert(
        tmp_path / "state", tmp_path, limits=_LIMITS, probe=_disk(used), publish=publish, now=stamp
    )


def test_alerts_once_per_crossing_and_rearms_after_falling_below(tmp_path: Path) -> None:
    publish = _Recorder()

    assert "below the reap watermark" in _run(tmp_path, 84.0, publish, "2026-10-16T01:00:00Z")
    assert publish.calls == []  # below: nothing to say

    assert "reported to the cto channel" in _run(tmp_path, 85.0, publish, "2026-10-16T02:00:00Z")
    assert len(publish.calls) == 1
    message, key = publish.calls[0]
    assert message.startswith("[sre-timers] disk 85.0% used, 60.0 GiB free on the .worktrees filesystem")
    assert "reap watermark of 85%" in message and "refused at 90%" in message
    assert key == "lu-disk-watermark:2026-10-16T02:00:00Z"

    for hour, used in ((3, 86.0), (4, 91.0), (5, 85.0)):  # stays above, even past the refuse level
        assert "already reported" in _run(tmp_path, used, publish, f"2026-10-16T0{hour}:00:00Z")
    assert len(publish.calls) == 1

    assert "re-armed" in _run(tmp_path, 84.9, publish, "2026-10-16T06:00:00Z")
    assert not (tmp_path / "state" / watermark.STATE_NAME).exists()
    assert len(publish.calls) == 1

    _run(tmp_path, 88.0, publish, "2026-10-16T07:00:00Z")
    assert len(publish.calls) == 2
    assert publish.calls[1][1] == "lu-disk-watermark:2026-10-16T07:00:00Z"


def test_a_failed_publish_keeps_the_disk_unreported_so_the_next_run_retries(tmp_path: Path) -> None:
    with pytest.raises(alerts.AlertError, match="plane unavailable"):
        _run(tmp_path, 90.0, _Recorder(fail=True), "2026-10-16T02:00:00Z")
    assert not (tmp_path / "state" / watermark.STATE_NAME).exists()

    publish = _Recorder()
    _run(tmp_path, 90.0, publish, "2026-10-16T03:00:00Z")
    assert len(publish.calls) == 1


def test_an_unreadable_disk_changes_nothing(tmp_path: Path) -> None:
    state = tmp_path / "state" / watermark.STATE_NAME
    state.parent.mkdir()
    state.write_text(json.dumps({"state": "above", "since_utc": "x"}))
    publish = _Recorder()

    result = watermark.check_and_alert(
        state.parent, tmp_path, limits=_LIMITS, probe=adm.DiskProbe(skipped="unreadable"), publish=publish
    )

    assert "skipped" in result
    assert json.loads(state.read_text())["state"] == "above" and publish.calls == []


def test_invalid_thresholds_raise(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DISPATCH_DISK_REFUSE_USED_PERCENT", "80")
    with pytest.raises(adm.DiskWatermarkConfigError):
        watermark.check_and_alert(tmp_path, tmp_path, probe=_disk(95.0), publish=_Recorder())


def test_scheduled_apply_run_alerts_and_a_failed_alert_fails_the_run(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cleanup,
        "build_receipt",
        lambda *_a, **_k: {"observed_at": "2026-10-16T00:00:00Z", "summary": {"errors": 0}, "repositories": []},
    )
    monkeypatch.setattr(cleanup.home_session_retention_check, "build_report", lambda: {})
    monkeypatch.setattr(cleanup.home_session_retention_check, "warning_lines", lambda _report: [])
    monkeypatch.setattr(cleanup, "sweep_sessions", lambda **_k: {"summary": {"errors": 0}})
    publish = _Recorder()
    monkeypatch.setattr(adm, "probe_disk", lambda: _disk(88.0))
    monkeypatch.setattr(alerts, "fleet_comms_publisher", lambda _root: publish)
    monkeypatch.setattr(adm, "load_thresholds", lambda *_a, **_k: _LIMITS)
    args = [
        "--repo-root",
        str(tmp_path),
        "--receipt-dir",
        str(tmp_path / "r"),
        "--alert-state-dir",
        str(tmp_path / "a"),
    ]

    assert cleanup.main([*args, "--apply"]) == 0
    assert cleanup.main([*args, "--apply"]) == 0  # still above: quiet
    assert len(publish.calls) == 1

    (tmp_path / "a" / watermark.STATE_NAME).unlink()
    monkeypatch.setattr(alerts, "fleet_comms_publisher", lambda _root: _Recorder(fail=True))
    assert cleanup.main([*args, "--apply"]) == 1
    assert "disk watermark alert failed" in capsys.readouterr().err


def test_scheduled_dry_run_never_alerts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        cleanup,
        "build_receipt",
        lambda *_a, **_k: {"observed_at": "2026-10-16T00:00:00Z", "summary": {"errors": 0}, "repositories": []},
    )
    monkeypatch.setattr(cleanup.home_session_retention_check, "build_report", lambda: {})
    monkeypatch.setattr(cleanup.home_session_retention_check, "warning_lines", lambda _report: [])
    monkeypatch.setattr(cleanup, "sweep_sessions", lambda **_k: {"summary": {"errors": 0}})
    monkeypatch.setattr(adm, "probe_disk", lambda: pytest.fail("a dry run must not read the disk for the alert"))

    assert cleanup.main(["--repo-root", str(tmp_path), "--receipt-dir", str(tmp_path / "r")]) == 0
