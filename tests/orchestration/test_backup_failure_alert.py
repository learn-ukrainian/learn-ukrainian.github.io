"""Change-only Fleet Comms alerts for the backup units."""

from __future__ import annotations

import hashlib
import json
import os
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
        "last-run receipt: absent or unreadable\n"
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


def test_backup_alerts_carry_the_backed_up_database_count(tmp_path: Path) -> None:
    receipt = tmp_path / "batch_state" / "backups" / "last-run.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text(
        json.dumps({"exit_status": 1, "run_id": "r1", "databases_backed_up": 57}),
        encoding="utf-8",
    )
    publish = Recorder()

    _handle(tmp_path, "failed", BACKUP, publish, "2026-10-03T03:51:00Z")
    receipt.write_text(
        json.dumps({"exit_status": 0, "run_id": "r2", "databases_backed_up": 58}),
        encoding="utf-8",
    )
    _handle(tmp_path, "recovered", BACKUP, publish, "2026-10-04T03:51:00Z")

    assert "databases_backed_up=57" in publish.calls[0][0]
    assert "last-run receipt: exit_status=0 run_id=r2 databases_backed_up=58" in publish.calls[1][0]


def test_retention_recovery_does_not_read_the_backup_receipt(tmp_path: Path) -> None:
    publish = Recorder()

    _handle(tmp_path, "failed", RETENTION, publish, "2026-10-04T05:30:00Z")
    _handle(tmp_path, "recovered", RETENTION, publish, "2026-10-11T05:30:00Z")

    assert "last-run receipt" not in publish.calls[1][0]


def test_rejects_units_that_are_not_backup_units(tmp_path: Path) -> None:
    with pytest.raises(alert.AlertError, match="not a backup unit"):
        _handle(tmp_path, "failed", "learn-ukrainian-api.service", Recorder(), "2026-10-03T03:45:00Z")


def test_cli_publishes_through_fleet_comms_to_the_cto_channel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "publish" in command:
            seen["command"] = command
            seen.update(kwargs)
            payload = _publication(str(kwargs["input"]), command[-1])
        else:
            payload = _delivery()
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(alert.subprocess, "run", fake_run)
    monkeypatch.setenv("MONITOR_INVOCATION_ID", "abc")

    status = alert.main(["failed", RETENTION, "--project-root", str(tmp_path)])

    assert status == 0
    assert seen["command"] == [
        ".venv/bin/python",
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
        "--recipient",
        "claude-cto",
        "--correlation-id",
        f"lu-backup-alert:{RETENTION}:failed:abc",
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
    assert "fleet_comms delivery exited 2" in capsys.readouterr().err


def _publication(message: str, key: str) -> dict:
    return {
        "message_id": "message-test",
        "recipient": "claude-cto",
        "sender": "sre-timers",
        "kind": "report",
        "correlation_id": key,
        "content_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
        "delivery_ids": ["delivery-test"],
    }


def _delivery() -> dict:
    return {"delivery_id": "delivery-test", "message_id": "message-test", "recipient": "claude-cto"}


@pytest.mark.parametrize("event", ["failed", "recovered"])
@pytest.mark.parametrize(
    "bad_receipt",
    [
        "nonzero",
        "malformed",
        "empty",
        "wrong-recipient",
        "not-object",
        "missing-message",
        "wrong-body",
        "wrong-key",
        "wrong-sender",
        "wrong-kind",
        "invalid-deliveries",
        "blank-delivery",
        "duplicate-delivery",
        "delivery-nonzero",
        "delivery-malformed",
        "delivery-not-object",
        "delivery-wrong-recipient",
        "delivery-wrong-message",
        "delivery-wrong-id",
    ],
)
def test_invalid_delivery_never_advances_transition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    event: str,
    bad_receipt: str,
) -> None:
    if event == "recovered":
        _handle(tmp_path, "failed", BACKUP, Recorder(), "failed-at")
    path = alert.state_path(tmp_path / "alerts", BACKUP)
    before = path.read_bytes() if path.exists() else None

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        publishing = "publish" in command
        payload = _publication(str(kwargs["input"]), command[-1]) if publishing else _delivery()
        code = 0
        if publishing:
            changes = {
                "empty": {"delivery_ids": []},
                "wrong-recipient": {"recipient": "another-seat"},
                "missing-message": {"message_id": ""},
                "wrong-body": {"content_sha256": "wrong"},
                "wrong-key": {"correlation_id": "another-key"},
                "wrong-sender": {"sender": "another-seat"},
                "wrong-kind": {"kind": "message"},
                "invalid-deliveries": {"delivery_ids": [None]},
                "blank-delivery": {"delivery_ids": [" "]},
                "duplicate-delivery": {"delivery_ids": ["delivery-test", "delivery-test"]},
            }
            payload.update(changes.get(bad_receipt, {}))
            code = 1 if bad_receipt == "nonzero" else 0
        else:
            field = {
                "delivery-wrong-recipient": "recipient",
                "delivery-wrong-message": "message_id",
                "delivery-wrong-id": "delivery_id",
            }.get(bad_receipt)
            if field:
                payload[field] = "wrong"
            code = 2 if bad_receipt == "delivery-nonzero" else 0
        output = json.dumps(payload)
        if bad_receipt == ("malformed" if publishing else "delivery-malformed"):
            output = "not JSON"
        if bad_receipt == ("not-object" if publishing else "delivery-not-object"):
            output = "[]"
        return subprocess.CompletedProcess(command, code, stdout=output, stderr="private details")

    monkeypatch.setattr(alert.subprocess, "run", fake_run)
    with pytest.raises(alert.AlertError, match="fleet_comms"):
        _handle(tmp_path, event, BACKUP, alert.fleet_comms_publisher(tmp_path), "transition-at")
    assert (path.read_bytes() if path.exists() else None) == before

    # Boundary rejection leaves the same transition retryable.
    retry = Recorder()
    _handle(tmp_path, event, BACKUP, retry, "transition-at")
    assert len(retry.calls) == 1


@pytest.mark.parametrize("error", [OSError("private path"), subprocess.TimeoutExpired("private command", 120)])
def test_publisher_transport_failure_is_sanitized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise error

    monkeypatch.setattr(alert.subprocess, "run", fail)
    with pytest.raises(alert.AlertError, match=r"^fleet_comms delivery could not run$"):
        _handle(tmp_path, "failed", BACKUP, alert.fleet_comms_publisher(tmp_path), "now")
    assert not alert.state_path(tmp_path / "alerts", BACKUP).exists()


@pytest.fixture
def authority_publisher(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Real CLI/authority with all storage redirected before any publication."""
    from scripts.fleet_comms.authority import AuthorityService

    root = tmp_path / "authority"
    with AuthorityService(root=root) as service:
        channel = service.create_channel("cto")
        assert channel.subscribers == ()
    run = subprocess.run

    def isolated_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert command[0] == ".venv/bin/python"
        assert command[1:3] == ["-m", "scripts.fleet_comms"]
        # Only the test child uses sys.executable; no worktree venv is created.
        return run(
            [sys.executable, *command[1:], "--root", str(root)],
            **{
                **kwargs,
                "cwd": alert.PROJECT_ROOT,
                "env": {**os.environ, "FLEET_COMMS_ROOT": str(root)},
            },
        )

    monkeypatch.setattr(alert.subprocess, "run", isolated_run)
    return root, alert.fleet_comms_publisher(alert.PROJECT_ROOT)


def test_real_authority_failure_recovery_retry_and_idempotency(tmp_path: Path, authority_publisher) -> None:
    from scripts.fleet_comms.authority import AuthorityService

    root, publish = authority_publisher
    _handle(tmp_path, "failed", BACKUP, publish, "failed-at", MONITOR_INVOCATION_ID="failure-1")
    # Simulate a crash after authority committed but before suppression persisted.
    path = alert.state_path(tmp_path / "alerts", BACKUP)
    path.unlink()
    _handle(tmp_path, "failed", BACKUP, publish, "failed-at", MONITOR_INVOCATION_ID="failure-1")
    _handle(tmp_path, "failed", BACKUP, publish, "later", MONITOR_INVOCATION_ID="failure-2")
    _handle(tmp_path, "recovered", BACKUP, publish, "recovered-at", INVOCATION_ID="recovery-1")
    # Replayed recovery publication also binds to the same delivery.
    publish(
        alert.recovery_message(BACKUP, "recovered-at", "failed-at", tmp_path),
        f"lu-backup-alert:{BACKUP}:recovered:recovery-1",
    )
    assert not path.exists()
    with AuthorityService(root=root) as service:
        deliveries = service._conn.execute(
            "SELECT recipient, message_id FROM authority_deliveries ORDER BY created_at, delivery_id"
        ).fetchall()
        assert len(deliveries) == 2
        assert {row["recipient"] for row in deliveries} == {"claude-cto"}
        assert len({row["message_id"] for row in deliveries}) == 2
        assert service.get_channel("cto").subscribers == ()


@pytest.mark.parametrize("event", ["failed", "recovered"])
def test_real_authority_committed_publication_inspection_failure_retries_same_delivery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    authority_publisher,
    event: str,
) -> None:
    from scripts.fleet_comms.authority import AuthorityService

    root, publish = authority_publisher
    if event == "recovered":
        _handle(tmp_path, "failed", BACKUP, publish, "failed-at")
    path = alert.state_path(tmp_path / "alerts", BACKUP)
    before = path.read_bytes() if path.exists() else None
    run = alert.subprocess.run

    def fail_inspection(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "status" in command:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="unavailable")
        return run(command, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(alert.subprocess, "run", fail_inspection)
        with pytest.raises(alert.AlertError, match="exited 1"):
            _handle(tmp_path, event, BACKUP, publish, "transition-at", INVOCATION_ID="retry-1")
    assert (path.read_bytes() if path.exists() else None) == before
    with AuthorityService(root=root) as service:
        committed = [
            tuple(row)
            for row in service._conn.execute(
                "SELECT delivery_id, message_id, recipient FROM authority_deliveries ORDER BY delivery_id"
            )
        ]
    _handle(tmp_path, event, BACKUP, publish, "transition-at", INVOCATION_ID="retry-1")
    with AuthorityService(root=root) as service:
        assert [
            tuple(row)
            for row in service._conn.execute(
                "SELECT delivery_id, message_id, recipient FROM authority_deliveries ORDER BY delivery_id"
            )
        ] == committed
    assert all(row[2] == "claude-cto" for row in committed)
    assert len(committed) == (1 if event == "failed" else 2)


@pytest.mark.parametrize("event", ["failed", "recovered"])
def test_legacy_failed_record_requires_reconciliation_before_suppression_or_recovery(
    tmp_path: Path,
    event: str,
) -> None:
    path = alert.state_path(tmp_path / "alerts", BACKUP)
    alert.write_state(path, {"state": "failed", "since_utc": "old-time", "invocation": "old-invocation"})
    before = path.read_bytes()
    publish = Recorder()
    with pytest.raises(alert.AlertError, match="driver delivery reconciliation required"):
        _handle(tmp_path, event, BACKUP, publish, "now")
    assert publish.calls == []
    assert path.read_bytes() == before


def test_legacy_zero_delivery_key_cannot_be_upgraded_and_reconciliation_is_retryable(
    tmp_path: Path,
    authority_publisher,
) -> None:
    from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError

    root, publish = authority_publisher
    key = f"lu-backup-alert:{BACKUP}:failed:old-invocation"
    body = alert.failure_message(BACKUP, "old-time", {}, tmp_path)
    with AuthorityService(root=root) as service:
        old = service.publish_message(
            sender=alert.SENDER,
            kind=alert.KIND,
            channel="cto",
            body=body,
            idempotency_key=key,
        )
        assert old.delivery_ids == ()
        replay = service.publish_message(
            sender=alert.SENDER,
            kind=alert.KIND,
            channel="cto",
            body=body,
            idempotency_key=key,
        )
        assert replay.message_id == old.message_id and replay.delivery_ids == ()
        with pytest.raises(AuthorityServiceError, match="idempotency_key_reused_with_different_payload"):
            service.publish_message(
                sender=alert.SENDER,
                kind=alert.KIND,
                channel="cto",
                body=body,
                idempotency_key=key,
                recipients=("claude-cto",),
            )

    path = alert.state_path(tmp_path / "alerts", BACKUP)
    state = {"state": "failed", "since_utc": "old-time", "invocation": "old-invocation"}
    alert.write_state(path, state)
    with pytest.raises(alert.AlertError):
        _handle(tmp_path, "failed", BACKUP, publish, "now")
    with pytest.raises(alert.AlertError):
        publish(body, key)
    assert alert.read_state(path) == state

    # Driver reconciliation: immutable original body, explicit new key, validated
    # delivery BEFORE marking the existing suppression record as verified.
    reconciliation_key = f"{key}:recipient:{alert.RECIPIENT}"
    publish(body, reconciliation_key)
    publish(body, reconciliation_key)  # crash/retry before writing the marker
    alert.write_state(path, {**state, "delivery_recipient": alert.RECIPIENT})
    assert "not re-posting" in _handle(tmp_path, "failed", BACKUP, publish, "now")
    _handle(tmp_path, "recovered", BACKUP, publish, "recovered-at")
    with AuthorityService(root=root) as service:
        assert service.get_message(old.message_id).delivery_ids == ()
        rows = service._conn.execute("SELECT recipient FROM authority_deliveries").fetchall()
        assert [row["recipient"] for row in rows] == ["claude-cto", "claude-cto"]
