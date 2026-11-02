"""Exercise the seat CLI against a real isolated authority store."""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys

import pytest

from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError
from scripts.fleet_comms.cli import EXIT_ERROR, EXIT_NOT_FOUND, EXIT_OK, main


@pytest.fixture
def plane(tmp_path, monkeypatch):
    root = tmp_path / "plane"
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))
    # Delivery operations must not depend on the legacy broker.
    monkeypatch.setenv("AB_DB_PATH", str(tmp_path / "unused-legacy.db"))
    return root


def publish(root, *, kind="message"):
    with AuthorityService(root=root) as service:
        return service.publish_message(
            sender="operator", body="private body sentinel", recipients=("codex",),
            kind=kind, idempotency_key="delivery-cli-test",
        )


def test_path_only_report_would_be_lost_when_its_file_is_deleted(plane, capsys, monkeypatch):
    path = plane.parent / "report.txt"
    path.write_text("Report content belongs in the message body.")
    body = f" \t{path}:12\n"
    assert main(["channel", "create", "reports"]) == EXIT_OK
    capsys.readouterr()
    monkeypatch.setattr("sys.stdin", io.StringIO(body))
    assert main([
        "channel", "publish", "reports", "-", "--sender", "operator", "--source", "test",
        "--recipient", "codex", "--idempotency-key", "path-only-report",
    ]) == EXIT_ERROR
    output = capsys.readouterr()
    assert "message_body_path_only: put the content in the message body" in output.err
    with AuthorityService(root=plane) as service:
        with pytest.raises(AuthorityServiceError, match="message_body_path_only"):
            service.publish_message(sender="operator", body=body, recipients=("codex",))
        assert service.store.connection.execute("SELECT COUNT(*) FROM comms_messages").fetchone()[0] == 0
        assert service.claim_next_delivery("codex", "seat-1") is None

    report = f" \nReport complete; evidence is in {path}:12.\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(report))
    assert main([
        "channel", "publish", "reports", "-", "--sender", "operator", "--source", "test",
        "--recipient", "codex", "--idempotency-key", "report-with-citation",
    ]) == EXIT_OK
    capsys.readouterr()
    path.unlink()
    delivery = claim(capsys)
    assert read_body(capsys, delivery)["body"] == report


def invoke(capsys, *args, expected=EXIT_OK):
    assert main(["deliveries", *args]) == expected
    output = capsys.readouterr()
    assert output.err == ""
    assert "private body sentinel" not in output.out
    payload = json.loads(output.out)
    assert payload["content_included"] is False
    return payload


def claim(capsys, *, worker="seat-1", recipient="codex", expected=EXIT_OK):
    return invoke(
        capsys, "claim", "--recipient", recipient, "--worker-id", worker, expected=expected,
    )


def fenced(operation, delivery, *, worker="seat-1", token=None):
    return [
        operation, delivery["delivery_id"], "--worker-id", worker,
        "--fence-token", str(delivery["fence_token"] if token is None else token),
    ]


def test_delivery_claim_status_ack_and_idempotent_ack(plane, capsys):
    message = publish(plane)
    delivery = claim(capsys)
    assert delivery["delivery_id"] == message.delivery_ids[0]
    assert delivery["message_id"] == message.message_id
    assert delivery["body_artifact_id"] == message.body_artifact_id
    assert delivery["content_sha256"] == hashlib.sha256(b"private body sentinel").hexdigest()
    assert delivery["fence_token"] == 1
    assert delivery["lease_owner"] == "seat-1"
    assert delivery["state"] == "running"
    status = invoke(capsys, "status", delivery["delivery_id"])
    assert status["state"] == "running"
    first = invoke(capsys, *fenced("ack", delivery))
    assert first["state"] == "acknowledged"
    assert invoke(capsys, *fenced("ack", delivery)) == first
    assert invoke(capsys, "status", delivery["delivery_id"]) == first
    assert claim(capsys, expected=EXIT_NOT_FOUND)["delivery"] is None
    assert not (plane.parent / "unused-legacy.db").exists()


def test_delivery_recipient_and_worker_mismatch_fail_closed(plane, capsys):
    message = publish(plane)
    assert claim(capsys, recipient="other", expected=EXIT_NOT_FOUND)["delivery"] is None
    assert invoke(capsys, "status", message.delivery_ids[0])["state"] == "queued"
    delivery = claim(capsys)
    assert claim(capsys, worker="other", expected=EXIT_NOT_FOUND)["delivery"] is None
    result = invoke(capsys, *fenced("ack", delivery, worker="other"), expected=EXIT_ERROR)
    assert result["error"] == "stale_delivery_lease"
    assert invoke(capsys, "status", delivery["delivery_id"])["state"] == "running"


def test_delivery_ack_artifact_and_conflicting_replay(plane, capsys):
    message = publish(plane)
    delivery = claim(capsys)
    args = [*fenced("ack", delivery), "--acknowledgment-artifact-id"]
    result = invoke(capsys, *args, "missing", expected=EXIT_ERROR)
    assert result["error"] == "artifact_not_found"
    first = invoke(capsys, *args, message.body_artifact_id)
    assert first["acknowledgment_artifact_id"] == message.body_artifact_id
    assert first["terminal_sha256"] == message.content_sha256
    assert invoke(capsys, *args, message.body_artifact_id) == first
    result = invoke(capsys, *fenced("ack", delivery), expected=EXIT_ERROR)
    assert result["error"] == "terminalization_conflict"


def test_delivery_stale_fence_after_reclaim(plane, capsys):
    publish(plane)
    # An expired real lease avoids sleeps and proves a previous worker is fenced.
    with AuthorityService(root=plane) as service:
        old = service.claim_next_delivery("codex", "old-seat", now="2000-01-01T00:00:00Z")
    current = claim(capsys)
    assert current["fence_token"] > old.fence_token
    result = invoke(
        capsys, *fenced("ack", current, worker="old-seat", token=old.fence_token),
        expected=EXIT_ERROR,
    )
    assert result["error"] == "stale_delivery_lease"
    result = invoke(capsys, *fenced("ack", current, token=old.fence_token), expected=EXIT_ERROR)
    assert result["error"] == "stale_delivery_lease"
    assert invoke(capsys, *fenced("ack", current))["state"] == "acknowledged"


def test_supervisory_delivery_requires_current_consumption(plane, capsys):
    publish(plane, kind="supervisory-request")
    delivery = claim(capsys)
    result = invoke(capsys, *fenced("ack", delivery), expected=EXIT_ERROR)
    assert result["error"] == "supervisory_consumption_required"
    for overrides in ({"worker": "other"}, {"token": 0}):
        invoke(
            capsys, *fenced("consume", delivery, **overrides),
            "--driver-generation", "gen-1", expected=EXIT_ERROR,
        )
    result = invoke(capsys, *fenced("ack", delivery), expected=EXIT_ERROR)
    assert result["error"] == "supervisory_consumption_required"
    consumption = [*fenced("consume", delivery), "--driver-generation", "gen-1"]
    receipt = invoke(capsys, *consumption)
    assert receipt["driver_generation"] == "gen-1"
    assert receipt["replay"] is False
    assert receipt["reconciliation"] is False
    assert invoke(capsys, *consumption)["replay"] is True
    first = invoke(capsys, *fenced("ack", delivery))
    assert first["state"] == "acknowledged"
    assert invoke(capsys, *fenced("ack", delivery)) == first


def test_supervisory_delivery_successor_must_reconcile_and_consume(plane, capsys):
    publish(plane, kind="supervisory-request")
    with AuthorityService(root=plane) as service:
        old = service.claim_next_delivery("codex", "old-seat", now="2000-01-01T00:00:00Z")
        service.record_supervisory_consumption(
            old.delivery.delivery_id, worker_id="old-seat", fence_token=old.fence_token,
            driver_generation="old-gen", now="2000-01-01T00:00:01Z",
        )
    current = claim(capsys)
    result = invoke(capsys, *fenced("ack", current), expected=EXIT_ERROR)
    assert result["error"] == "supervisory_consumption_required"
    receipt = invoke(capsys, *fenced("consume", current), "--driver-generation", "new-gen")
    assert receipt["reconciliation"] is True
    assert receipt["reconciled_generation"] == "old-gen"
    assert invoke(capsys, *fenced("ack", current))["state"] == "acknowledged"


def test_delivery_consume_rejects_ordinary_message(plane, capsys):
    publish(plane)
    delivery = claim(capsys)
    result = invoke(
        capsys, *fenced("consume", delivery), "--driver-generation", "gen-1", expected=EXIT_ERROR,
    )
    assert result["error"] == "not_supervisory_delivery"


def test_delivery_control_plane_refusal_is_sanitized(plane, monkeypatch, capsys):
    from scripts.control_plane.storage import ControlPlaneUnsupportedComponentError

    def refuse(*_args, **_kwargs):
        raise ControlPlaneUnsupportedComponentError("private storage configuration")

    monkeypatch.setattr("scripts.fleet_comms.authority.assert_component_supported", refuse)
    result = invoke(capsys, "status", "missing", expected=EXIT_ERROR)
    assert result["error"] == "delivery_store_unavailable"
    assert "private storage" not in json.dumps(result)


@pytest.mark.parametrize("operation", ["status", "ack", "consume"])
def test_delivery_missing_id(plane, capsys, operation):
    args = [operation, "missing"]
    if operation != "status":
        args += ["--worker-id", "seat-1", "--fence-token", "1"]
    if operation == "consume":
        args += ["--driver-generation", "gen-1"]
    assert invoke(capsys, *args, expected=EXIT_NOT_FOUND)["error"] == "delivery_not_found"


@pytest.mark.parametrize("flag", ["--lease-seconds", "--max-attempts"])
def test_delivery_claim_invalid_limits(plane, capsys, flag):
    publish(plane)
    result = invoke(
        capsys, "claim", "--recipient", "codex", "--worker-id", "seat-1", flag, "0",
        expected=EXIT_ERROR,
    )
    assert result["error"] == "lease_and_max_attempts_must_be_positive"
    assert claim(capsys)["attempt_count"] == 1


def test_delivery_storage_error_does_not_leak_path(tmp_path, capsys):
    root = tmp_path / "private-path-sentinel"
    root.write_text("not a directory")
    result = invoke(capsys, "status", "missing", "--root", str(root), expected=EXIT_ERROR)
    assert result["error"] == "delivery_store_unavailable"
    assert "private-path-sentinel" not in json.dumps(result)


@pytest.mark.parametrize("operation", [None, "claim", "status", "consume", "ack"])
def test_delivery_cli_help(operation):
    args = [sys.executable, "-m", "scripts.fleet_comms", "deliveries"]
    if operation:
        args.append(operation)
    result = subprocess.run([*args, "--help"], capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == 0
    for section in ("Examples:", "Outputs:", "Exit codes:", "Related:"):
        assert section in result.stdout
    assert result.stderr == ""


def test_delivery_cli_subprocess_claim_ack_and_usage(plane):
    message = publish(plane)
    command = [sys.executable, "-m", "scripts.fleet_comms", "deliveries"]
    env = {**os.environ, "FLEET_COMMS_ROOT": str(plane.parent / "wrong-root")}
    result = subprocess.run(
        [*command, "claim", "--recipient", "codex", "--worker-id", "seat-1", "--root", str(plane)],
        env=env, capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == EXIT_OK
    delivery = json.loads(result.stdout)
    assert delivery["delivery_id"] == message.delivery_ids[0]
    result = subprocess.run(
        [*command, *fenced("ack", delivery), "--root", str(plane)],
        env=env, capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == EXIT_OK
    assert json.loads(result.stdout)["state"] == "acknowledged"
    for operation, args in (("claim", []), ("ack", [message.delivery_ids[0]]),
                            ("consume", fenced("consume", delivery)[1:])):
        result = subprocess.run([*command, operation, *args], capture_output=True, text=True, check=False, timeout=30)
        assert result.returncode == 2
        assert "required" in result.stderr


def read_body(capsys, delivery, *, worker="seat-1", token=None, expected=EXIT_OK):
    assert main(["deliveries", *fenced("read", delivery, worker=worker, token=token)]) == expected
    output = capsys.readouterr()
    assert output.err == ""
    return json.loads(output.out)


def test_delivery_read_returns_body_only_to_the_current_lease_holder(plane, capsys):
    publish(plane)
    delivery = claim(capsys)
    for overrides in ({"worker": "other"}, {"token": delivery["fence_token"] + 1}):
        result = read_body(capsys, delivery, expected=EXIT_ERROR, **overrides)
        assert result == {"content_included": False, "error": "stale_delivery_lease"}
    held = read_body(capsys, delivery)
    assert held["body"] == "private body sentinel"
    assert held["content_included"] is True
    invoke(capsys, *fenced("ack", delivery))
    result = read_body(capsys, delivery, expected=EXIT_ERROR)
    assert result == {"content_included": False, "error": "stale_delivery_lease"}


def test_delivery_read_missing_body_file_is_storage_error(plane, capsys):
    publish(plane)
    delivery = claim(capsys)
    body_files = [path for path in (plane / "blobs").rglob("*") if path.is_file()]
    assert body_files
    for path in body_files:
        path.unlink()
    result = read_body(capsys, delivery, expected=EXIT_ERROR)
    assert result == {"content_included": False, "error": "delivery_store_unavailable"}
    assert "body" not in result
    assert "private body sentinel" not in json.dumps(result)


def test_lost_claim_output_receive_recovers_same_lease_without_burning_attempts(plane, capsys):
    """A discarded flat claim must not make a coordinator reply look absent."""
    with AuthorityService(root=plane) as service:
        message = service.publish_message(
            sender="claude-cto", body="Apply option B", recipients=("worker-task",),
        )
    claimed = claim(capsys, recipient="worker-task")
    assert claimed.get("delivery") is None  # The old loop mistook this success for an empty inbox.
    args = ["receive", "--recipient", "worker-task", "--worker-id", "seat-1"]
    for _ in range(2):
        assert main(["deliveries", *args]) == EXIT_OK
        output = capsys.readouterr()
        assert output.err == ""
        received = json.loads(output.out)
        assert received["content_included"] is True
        delivery = received["delivery"]
        assert delivery["body"] == "Apply option B"
        assert delivery["sender"] == "claude-cto"
        assert delivery["kind"] == "message"
        assert delivery["delivery_id"] == message.delivery_ids[0]
        assert delivery["fence_token"] == claimed["fence_token"]
        assert delivery["attempt_count"] == 1
        assert delivery["lease_expires_at"] == claimed["lease_expires_at"]
        assert delivery["state"] == "running"
    assert main(["deliveries", "receive", "--recipient", "worker-task", "--worker-id", "other"]) == EXIT_NOT_FOUND
    assert json.loads(capsys.readouterr().out) == {"delivery": None, "content_included": False}
    assert invoke(capsys, *fenced("ack", delivery))["state"] == "acknowledged"
    assert main(["deliveries", *args]) == EXIT_NOT_FOUND
    assert json.loads(capsys.readouterr().out) == {"delivery": None, "content_included": False}


def test_unreadable_coordinator_reply_reports_typed_error_to_both_parties_once(plane, capsys):
    """Read failure cannot leave only a worker-local error and an eventual silent dead letter."""
    with AuthorityService(root=plane) as service:
        message = service.publish_message(
            sender="claude-cto", body="private body sentinel", recipients=("worker-task",),
        )
        service.store.get(message.body_artifact_id).blob_path.unlink()
    delivery = claim(capsys, recipient="worker-task")
    for args in (
        fenced("read", delivery),
        ["receive", "--recipient", "worker-task", "--worker-id", "seat-1"],
    ):
        assert invoke(capsys, *args, expected=EXIT_ERROR) == {
            "content_included": False, "error": "coordinator_reply_read_failed",
        }
    with AuthorityService(root=plane) as service:
        # Subsequent exhaustion must not send a second notice for the same original delivery.
        service.reclaim_expired_deliveries(now="2099-01-01T00:00:00Z", max_attempts=1)
        notices = service.store.connection.execute(
            "SELECT message_id FROM comms_messages WHERE kind = 'delivery-error'",
        ).fetchall()
        assert len(notices) == 1
        notice = service.get_message(notices[0]["message_id"])
        assert notice.sender == "fleet-comms"
        assert notice.in_reply_to == message.message_id
        assert json.loads(service.read_message_body(notice.message_id)) == {
            "error": "coordinator_reply_delivery_failed",
            "reason_code": "read_failed",
            "delivery_id": delivery["delivery_id"],
            "message_id": message.message_id,
            "recipient": "worker-task",
        }
        assert {service.get_delivery(d).recipient for d in notice.delivery_ids} == {
            "worker-task", "claude-cto",
        }


def test_exhausted_unacknowledged_reply_notifies_once_without_recursive_alerts(plane, capsys):
    """An abandoned reply must produce one notice to both parties, even if notices are abandoned."""
    with AuthorityService(root=plane) as service:
        message = service.publish_message(
            sender="claude-cto", body="Apply option B", recipients=("worker-task",),
        )
        for minute in (0, 5, 10):
            lease = service.claim_next_delivery(
                "worker-task", "seat-1", now=f"2000-01-01T00:{minute:02}:00Z",
            )
            assert lease.delivery.delivery_id == message.delivery_ids[0]
        assert service.reclaim_expired_deliveries(now="2000-01-01T00:15:00Z") == 1
        assert service.reclaim_expired_deliveries(now="2000-01-01T00:15:00Z") == 0
        assert service.get_delivery(message.delivery_ids[0]).state == "dead_lettered"
        assert service.store.connection.execute(
            "SELECT COUNT(*) FROM comms_messages WHERE kind = 'delivery-error'",
        ).fetchone()[0] == 1
    for recipient in ("worker-task", "claude-cto"):
        assert main([
            "deliveries", "receive", "--recipient", recipient, "--worker-id", recipient,
        ]) == EXIT_OK
        notice = json.loads(capsys.readouterr().out)["delivery"]
        assert notice["kind"] == "delivery-error"
        assert json.loads(notice["body"]) == {
            "error": "coordinator_reply_delivery_failed",
            "reason_code": "attempts_exhausted",
            "delivery_id": message.delivery_ids[0],
            "message_id": message.message_id,
            "recipient": "worker-task",
        }
    with AuthorityService(root=plane) as service:
        assert service.reclaim_expired_deliveries(now="2099-01-01T00:00:00Z", max_attempts=1) == 2
        assert service.store.connection.execute(
            "SELECT COUNT(*) FROM comms_messages WHERE kind = 'delivery-error'",
        ).fetchone()[0] == 1
