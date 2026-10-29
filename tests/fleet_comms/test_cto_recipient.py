"""`claude-cto` is the one durable CTO recipient; session identities only claim and acknowledge."""

from __future__ import annotations

import io
import json

import pytest

from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError
from scripts.fleet_comms.cli import EXIT_ERROR, EXIT_NOT_FOUND, EXIT_OK, main

SESSION = "claude-cto-27b21508"
LEGACY = "claude-cto-d465aa4b"


@pytest.fixture
def plane(tmp_path, monkeypatch):
    root = tmp_path / "plane"
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))
    monkeypatch.setenv("AB_DB_PATH", str(tmp_path / "unused-legacy.db"))
    return root


def run(capsys, *args, expected=EXIT_OK):
    assert main(list(args)) == expected
    return json.loads(capsys.readouterr().out)


def backlog(root):
    with AuthorityService(root=root) as service:
        return service.store.connection.execute(
            "SELECT recipient, state FROM authority_deliveries ORDER BY created_at"
        ).fetchall()


def delivery_recipients(service, message):
    rows = service.store.connection.execute(
        "SELECT recipient FROM authority_deliveries WHERE message_id = ?", (message.message_id,)
    ).fetchall()
    return [row["recipient"] for row in rows]


def escalate(recipient):
    return main([
        "channel", "publish", "cto", "-", "--sender", "claude/cto-7923-demo", "--source", "worker",
        "--recipient", recipient, "--kind", "request", "--idempotency-key", f"esc-{recipient}",
    ])


def test_worker_escalation_lands_at_claude_cto_and_the_session_claims_it(plane, capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("escalation body"))
    run(capsys, "channel", "create", "cto")
    monkeypatch.setattr("sys.stdin", io.StringIO("escalation body"))
    assert escalate("claude-cto") == EXIT_OK
    published = json.loads(capsys.readouterr().out)
    assert [tuple(row) for row in backlog(plane)] == [("claude-cto", "queued")]

    claimed = run(capsys, "deliveries", "claim", "--recipient", "claude-cto", "--worker-id", SESSION)
    assert claimed["message_id"] == published["message_id"]
    assert claimed["lease_owner"] == SESSION
    acked = run(
        capsys, "deliveries", "ack", claimed["delivery_id"],
        "--worker-id", SESSION, "--fence-token", str(claimed["fence_token"]),
    )
    assert acked["state"] == "acknowledged"
    run(capsys, "deliveries", "claim", "--recipient", "claude-cto", "--worker-id", SESSION,
        expected=EXIT_NOT_FOUND)


def test_publishing_to_a_session_specific_cto_name_is_refused_at_the_authority(plane, capsys):
    with AuthorityService(root=plane) as service:
        service.create_channel("cto")
        for name in (SESSION, "claude-cto-d465aa4b", " claude-cto-x "):
            with pytest.raises(AuthorityServiceError, match=r"session_cto_recipient_refused.*claude-cto"):
                service.publish_message(sender="codex", body="b", channel="cto", recipients=(name,))
            with pytest.raises(AuthorityServiceError, match="session_cto_recipient_refused"):
                service.publish_message(sender="codex", body="b", recipients=("claude-cto", name))
            with pytest.raises(AuthorityServiceError, match="session_cto_recipient_refused"):
                service.subscribe("cto", (name,))
        with pytest.raises(AuthorityServiceError, match="session_cto_recipient_refused"):
            service.create_channel("other", subscribers=(SESSION,))
    assert backlog(plane) == []


def test_cli_refusal_carries_the_pointer_and_writes_nothing(plane, capsys, monkeypatch):
    run(capsys, "channel", "create", "cto")
    monkeypatch.setattr("sys.stdin", io.StringIO("body"))
    assert escalate(SESSION) == EXIT_ERROR
    assert "session_cto_recipient_refused: address claude-cto," in capsys.readouterr().err
    assert backlog(plane) == []


def test_legacy_session_names_stay_claimable_and_stale_subscribers_reach_claude_cto(plane):
    with AuthorityService(root=plane) as service:
        # A delivery queued before the rule, as the legacy import replays it.
        with service._write_transaction():
            legacy = service._publish_message_tx(
                sender="codex", body="old escalation", channel=None, targets=None, kind="request",
                imported_recipients=(LEGACY,), imported_source="test-legacy",
                idempotency_key="legacy-1",
            )
        # A stored subscription under an old session name, replayed by the legacy import.
        service.create_channel("cto", subscribers=(LEGACY, "claude-epics"), legacy_import=True)
        fresh = service.publish_message(sender="codex", body="new", channel="cto")
        own = service.publish_message(sender=SESSION, body="note", channel="cto")

        assert sorted(delivery_recipients(service, fresh)) == ["claude-cto", "claude-epics"]
        assert delivery_recipients(service, own) == ["claude-epics"]
        lease = service.claim_next_delivery(LEGACY, SESSION)
        assert lease is not None and lease.delivery.message_id == legacy.message_id
        assert lease.delivery.fence_token == 1
        service.acknowledge_delivery(
            lease.delivery.delivery_id, worker_id=SESSION, fence_token=lease.delivery.fence_token
        )
        assert service.claim_next_delivery(LEGACY, SESSION) is None
