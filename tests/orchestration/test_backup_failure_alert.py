"""Change-only Fleet Comms alerts for the backup units."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.orchestration import backup_failure_alert as alert

BACKUP = "learn-ukrainian-backup.service"
RETENTION = "learn-ukrainian-backup-retention.service"


class Recorder:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[tuple[str, str]] = []
        self.fail = fail

    def __call__(self, message: str, key: str) -> None:
        self.calls.append((message, key))
        if self.fail:
            raise alert.AlertError("fleet_comms publish exited 1: plane unavailable")


def _handle(tmp_path: Path, event: str, unit: str, publish: Recorder, now: str, **environment: str) -> str:
    return alert.handle(
        event,
        unit,
        state_dir=tmp_path / "alerts",
        project_root=tmp_path,
        publish=publish,
        environment=environment,
        now=now,
    )


def test_first_failure_posts_once_then_stays_quiet_until_recovery(tmp_path: Path) -> None:
    publish = Recorder()
    environment = {"MONITOR_SERVICE_RESULT": "exit-code", "MONITOR_EXIT_STATUS": "1", "MONITOR_INVOCATION_ID": "inv1"}

    first = _handle(tmp_path, "failed", BACKUP, publish, "2026-10-03T03:45:00Z", **environment)
    second = _handle(tmp_path, "failed", BACKUP, publish, "2026-10-04T03:45:00Z", MONITOR_INVOCATION_ID="inv2")

    assert "failure reported" in first
    assert "already reported failing since 2026-10-03T03:45:00Z" in second
    assert len(publish.calls) == 1
    message, key = publish.calls[0]
    assert message.startswith(f"[sre-timers] {BACKUP} FAILED at 2026-10-03T03:45:00Z.")
    assert "result=exit-code exit_status=1" in message
    assert f"journalctl --user -u {BACKUP}" in message
    assert key == f"lu-backup-alert:{BACKUP}:failed:inv1"

    recovered = _handle(tmp_path, "recovered", BACKUP, publish, "2026-10-07T18:40:00Z", INVOCATION_ID="inv3")
    assert "recovery reported" in recovered
    assert publish.calls[1][0] == (
        f"[sre-timers] {BACKUP} RECOVERED at 2026-10-07T18:40:00Z (failing since 2026-10-03T03:45:00Z).\n"
    )
    assert publish.calls[1][1] == f"lu-backup-alert:{BACKUP}:recovered:inv3"
    assert not alert.state_path(tmp_path / "alerts", BACKUP).exists()

    # Healthy runs post nothing; the next failure is a fresh change.
    assert "nothing to report" in _handle(tmp_path, "recovered", BACKUP, publish, "2026-10-08T03:45:00Z")
    assert len(publish.calls) == 2
    _handle(tmp_path, "failed", BACKUP, publish, "2026-10-09T03:45:00Z")
    assert len(publish.calls) == 3


def test_units_are_tracked_independently(tmp_path: Path) -> None:
    publish = Recorder()
    _handle(tmp_path, "failed", BACKUP, publish, "2026-10-03T03:45:00Z")
    _handle(tmp_path, "failed", RETENTION, publish, "2026-10-04T05:25:00Z")

    assert [call[0].split(" ")[1] for call in publish.calls] == [BACKUP, RETENTION]
    assert "last-run receipt" not in publish.calls[1][0]


def test_failed_publish_keeps_state_so_the_next_failure_retries(tmp_path: Path) -> None:
    with pytest.raises(alert.AlertError, match="plane unavailable"):
        _handle(tmp_path, "failed", BACKUP, Recorder(fail=True), "2026-10-03T03:45:00Z")
    assert not alert.state_path(tmp_path / "alerts", BACKUP).exists()

    publish = Recorder()
    _handle(tmp_path, "failed", BACKUP, publish, "2026-10-04T03:45:00Z")
    assert len(publish.calls) == 1


def test_failed_recovery_publish_keeps_the_failed_record(tmp_path: Path) -> None:
    _handle(tmp_path, "failed", BACKUP, Recorder(), "2026-10-03T03:45:00Z")
    with pytest.raises(alert.AlertError):
        _handle(tmp_path, "recovered", BACKUP, Recorder(fail=True), "2026-10-04T03:45:00Z")
    state = json.loads(alert.state_path(tmp_path / "alerts", BACKUP).read_text(encoding="utf-8"))
    assert state["state"] == "failed"


def test_unreadable_state_does_not_silence_a_failure(tmp_path: Path) -> None:
    path = alert.state_path(tmp_path / "alerts", BACKUP)
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    publish = Recorder()

    _handle(tmp_path, "failed", BACKUP, publish, "2026-10-03T03:45:00Z")

    assert len(publish.calls) == 1


def test_backup_failure_includes_last_run_receipt_status(tmp_path: Path) -> None:
    receipt = tmp_path / "batch_state" / "backups" / "last-run.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(
        json.dumps({"status": "failed", "exit_status": 1, "run_id": "r1", "finished_at_utc": "2026-10-03T03:50:00Z"}),
        encoding="utf-8",
    )
    publish = Recorder()

    _handle(tmp_path, "failed", BACKUP, publish, "2026-10-03T03:51:00Z")

    assert (
        "last-run receipt: status=failed exit_status=1 run_id=r1 finished_at_utc=2026-10-03T03:50:00Z"
        in (publish.calls[0][0])
    )


def test_rejects_units_that_are_not_backup_units(tmp_path: Path) -> None:
    with pytest.raises(alert.AlertError, match="not a backup unit"):
        _handle(tmp_path, "failed", "learn-ukrainian-api.service", Recorder(), "2026-10-03T03:45:00Z")


def test_cli_publishes_through_fleet_comms_to_the_cto_channel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen["command"] = command
        seen.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(alert.subprocess, "run", fake_run)
    monkeypatch.setenv("MONITOR_INVOCATION_ID", "abc")

    status = alert.main(["failed", RETENTION, "--project-root", str(tmp_path)])

    assert status == 0
    assert seen["command"] == [
        sys.executable,
        "-m",
        "scripts.fleet_comms",
        "channel",
        "publish",
        "cto",
        "-",
        "--sender",
        "sre-timers",
        "--kind",
        "report",
        "--idempotency-key",
        f"lu-backup-alert:{RETENTION}:failed:abc",
    ]
    assert seen["cwd"] == tmp_path.resolve()
    assert str(seen["input"]).startswith(f"[sre-timers] {RETENTION} FAILED at ")
    assert alert.state_path(tmp_path / "batch_state" / "backups" / "alerts", RETENTION).exists()


def test_cli_exits_non_zero_when_publish_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        alert.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(command, 2, stdout="", stderr="no such channel"),
    )

    status = alert.main(["failed", BACKUP, "--project-root", str(tmp_path)])

    assert status == 1
    assert "fleet_comms publish exited 2: no such channel" in capsys.readouterr().err
