"""Synthetic store proofs for the body-free pending probe (#10558)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts import inbox_pending
from scripts.fleet_comms.authority import AuthorityService
from tests.helpers.agy_inbox_fixtures import (
    BODY_MARKER,
    CLI_BOOTSTRAP,
    MESSAGE_ID,
    add_authority,
    add_legacy,
    snapshot,
)
from tests.helpers.agy_inbox_fixtures import (
    run_cli as raw_cli,
)

pytest_plugins = ("tests.helpers.agy_inbox_fixtures",)
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_UNKNOWN_NOTICE = (
    "PENDING ORDERS: unknown; legacy: ai_agent_bridge inbox for the registered handoff slot; "
    "authority: .venv/bin/python -m scripts.fleet_comms deliveries --help"
)


def check_metadata(result):
    authority = result["authority"]
    assert authority["content_included"] is False
    assert "deliveries claim --recipient" in authority["drain_command"]
    assert "$SESSION_STREAM_SESSION_ID" in authority["drain_command"]
    if result["probe"] == "ok":
        assert authority["probe"] == "ok"
        assert authority["count"] == result["stores"]["authority"]
        assert sum(group["count"] for group in authority["by_correlation"]) == authority["count"]
        assert (
            authority["oldest_age_seconds"] is None
            if not authority["count"]
            else isinstance(authority["oldest_age_seconds"], int)
        )
    else:
        assert authority["count"] is None
        assert authority["oldest_age_seconds"] is None
        assert result["count"] is None
    return {key: value for key, value in result.items() if key != "authority"}


def checked_probe(recipient):
    return check_metadata(inbox_pending.probe(recipient))


def run_cli(recipient):
    return check_metadata(raw_cli(recipient))


def check_notice(notice, *, count, authority_count, recipient="lane:infra"):
    line = notice["injectSteps"][0]["ephemeralMessage"]
    assert len(line) <= 200 and line.isascii()
    assert re.fullmatch(
        rf"PENDING ORDERS: {count}; authority {authority_count}, oldest (?:[0-9]+s|none); "
        + re.escape(
            f'.venv/bin/python -m scripts.fleet_comms deliveries claim --recipient {recipient} --worker-id "$SESSION_STREAM_SESSION_ID"'
        ),
        line,
    )
    assert BODY_MARKER not in line


@pytest.mark.parametrize(
    ("acknowledged", "consumed", "expected"), [(0, 0, 1), (1, 0, 0), (0, 1, 0), (1, 1, 0), (None, None, 1)]
)
def test_legacy_delivery_states(stores, acknowledged, consumed, expected):
    add_legacy(stores[0], acknowledged=acknowledged, consumed=consumed)
    assert checked_probe("gemini-infra") == {
        "count": expected,
        "ids": [1] if expected else [],
        "truncated": False,
        "stores": {"legacy": expected, "authority": 0},
        "probe": "ok",
    }


@pytest.mark.parametrize(
    ("state", "consumed", "wake", "expected"),
    [
        ("queued", False, False, 1),
        ("running", False, False, 1),
        ("running", True, False, 0),
        ("running", False, True, 1),
        ("acknowledged", False, False, 0),
        ("expired", False, False, 0),
        ("failed", False, False, 0),
        ("dead_lettered", False, False, 0),
    ],
)
def test_authority_delivery_states(stores, state, consumed, wake, expected):
    add_authority(stores[1], state=state, consumed=consumed, wake_consumed=wake)
    assert checked_probe("gemini-infra") == {
        "count": expected,
        "ids": [MESSAGE_ID] if expected else [],
        "truncated": False,
        "stores": {"legacy": 0, "authority": expected},
        "probe": "ok",
    }


def test_h26_wake_observation_is_not_supervisory_consumption(stores, roster, monkeypatch):
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.model import LeaseHolder
    from agents_extensions.shared.session_streams.store import SessionStreamStore

    session_store = SessionStreamStore(SessionStreamDatabase(stores[1].parent / "sessions.sqlite3"))
    holder = session_store.open_session(
        stream_id="epic:6943",
        holder=LeaseHolder(agent="codex", harness="codex", instance_id="h26", process_id=os.getpid()),
        lineage_id="h26",
        ttl_seconds=30,
        session_id="h26-worker",
        now=datetime.now(UTC),
    )
    fields = {
        "ID": holder.stream_id,
        "SESSION_ID": holder.session_id,
        "LEASE_ID": holder.lease_id,
        "GENERATION": str(holder.generation),
        "FENCING_TOKEN": str(holder.fencing_token),
        "AGENT": holder.holder.agent,
        "HARNESS": holder.holder.harness,
        "INSTANCE_ID": holder.holder.instance_id,
        "PROCESS_ID": str(holder.holder.process_id),
    }
    for key, value in fields.items():
        monkeypatch.setenv("SESSION_STREAM_" + key, value)
    monkeypatch.delenv("SESSION_STREAM_TASK_ID", raising=False)
    monkeypatch.delenv("LU_MONITOR_HOST_ID", raising=False)
    with AuthorityService(root=stores[1].parent, session_store=session_store) as service:
        message = service.enqueue_supervisory_request(
            sender="supervisor",
            recipient="gemini-infra",
            body=BODY_MARKER,
            correlation_id="h26",
            idempotency_key="h26",
        )
        delivery_id = message.delivery_ids[0]
        lease = service.claim_next_delivery("gemini-infra", "h26-worker")
        assert lease is not None
        service.record_wake_receipt(delivery_id, fence_token=lease.fence_token, state="consumed")
        expected_metadata = {
            "count": 1,
            "ids": [message.message_id],
            "truncated": False,
            "stores": {"legacy": 0, "authority": 1},
            "probe": "ok",
        }
        before = snapshot(stores)
        metadata = run_cli("gemini-infra")
        hook_proc = subprocess.run(
            ["sh", str(ROOT / "scripts/agy_hooks/pending_orders_inject.sh")],
            input="{}",
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert hook_proc.returncode == 0
        assert hook_proc.stderr == ""
        assert BODY_MARKER not in hook_proc.stdout
        notice = json.loads(hook_proc.stdout)
        status = service.supervisory_delivery_status(delivery_id)
        print(
            "H26 actual before authority consumption:",
            json.dumps({"status": status, "metadata": metadata, "hook": notice}),
        )
        assert snapshot(stores) == before
        assert status == "delivered"
        assert metadata == expected_metadata
        check_notice(notice, count=1, authority_count=1)

        service.record_supervisory_consumption(
            delivery_id,
            worker_id="h26-worker",
            fence_token=lease.fence_token,
            driver_generation="h26-generation",
        )
        status = service.supervisory_delivery_status(delivery_id)
        assert status == "live_driver_consumed"
        before = snapshot(stores)
        metadata = run_cli("gemini-infra")
        assert metadata == {
            "count": 0,
            "ids": [],
            "truncated": False,
            "stores": {"legacy": 0, "authority": 0},
            "probe": "ok",
        }
        hook_proc = subprocess.run(
            ["sh", str(ROOT / "scripts/agy_hooks/pending_orders_inject.sh")],
            input="{}",
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert hook_proc.returncode == 0
        assert hook_proc.stderr == ""
        notice = json.loads(hook_proc.stdout)
        assert notice == {}
        assert snapshot(stores) == before
        print(
            "H26 actual after authority consumption:",
            json.dumps({"status": status, "metadata": metadata, "hook": notice, "stores_unchanged": True}),
        )


@pytest.mark.parametrize("state", ["queued", "running"])
def test_expired_deadline_is_silent(stores, state):
    add_authority(stores[1], state=state, deadline="2000-01-01T00:00:00Z")
    assert checked_probe("gemini-infra")["count"] == 0


@pytest.mark.parametrize(
    "recipient",
    ["gemini-infra", "gemini", "unknown", "gemini-not-a-lane", "", "gemini-infra\n", "gemini-infra' OR 1=1--"],
)
def test_recipient_shapes(stores, recipient):
    add_legacy(stores[0], recipient="claude")
    add_legacy(stores[0], identifier=2)
    add_authority(stores[1], recipient="claude")
    result = checked_probe(recipient)
    if recipient == "gemini-infra":
        assert result == {
            "count": 1,
            "ids": [2],
            "truncated": False,
            "stores": {"legacy": 1, "authority": 0},
            "probe": "ok",
        }
    else:
        assert result["probe"] == "unknown"
        assert result["ids"] == []


def test_registry_unavailable_is_unknown(stores, roster):
    roster.unlink()
    assert checked_probe("gemini-infra")["probe"] == "unknown"


def test_counts_and_five_full_ids(stores):
    for identifier in range(1, 8):
        add_legacy(stores[0], identifier=identifier)
    add_authority(stores[1])
    assert checked_probe("gemini-infra") == {
        "count": 8,
        "ids": [1, 2, 3, 4, 5],
        "truncated": True,
        "stores": {"legacy": 7, "authority": 1},
        "probe": "ok",
    }


def test_readonly_hashes_and_no_body_or_artifacts(stores, tmp_path):
    add_legacy(stores[0])
    add_authority(stores[1], state="running")
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in stores}
    files = set(tmp_path.iterdir())
    for _ in range(2):
        result = checked_probe("gemini-infra")
        assert result["count"] == 2
        assert BODY_MARKER not in json.dumps(result)
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in stores} == before
    assert set(tmp_path.iterdir()) == files


@pytest.mark.parametrize("store_index", [0, 1])
def test_missing_store_returns_unknown_without_creation(stores, store_index):
    stores[store_index].unlink()
    assert checked_probe("gemini-infra")["probe"] == "unknown"
    assert not stores[store_index].exists()


@pytest.mark.parametrize("store_index", [0, 1])
def test_locked_store_is_unknown(stores, store_index):
    with sqlite3.connect(stores[store_index]) as conn:
        conn.execute("BEGIN EXCLUSIVE")
        assert checked_probe("gemini-infra")["probe"] == "unknown"


@pytest.mark.parametrize("store_index", [0, 1])
def test_unreadable_store_is_unknown(stores, monkeypatch, store_index):
    original = inbox_pending.open_readonly

    def denied(path, **kwargs):
        if path == stores[store_index]:
            raise PermissionError(BODY_MARKER)
        return original(path, **kwargs)

    monkeypatch.setattr(inbox_pending, "open_readonly", denied)
    monkeypatch.setattr("scripts.fleet_comms.lane_mailbox.open_readonly", denied)
    result = checked_probe("gemini-infra")
    assert result["probe"] == "unknown"
    assert BODY_MARKER not in json.dumps(result)


@pytest.mark.parametrize("store_index", [0, 1])
def test_schema_drift_and_corrupt_store_unknown(stores, store_index):
    stores[store_index].write_bytes(b"not sqlite " + BODY_MARKER.encode())
    assert checked_probe("gemini-infra")["probe"] == "unknown"


@pytest.mark.parametrize("schema_fault", ["table", "delivery_id", "state"])
@pytest.mark.parametrize("pending", [False, True])
def test_wake_schema_drift_is_unknown(stores, roster, schema_fault, pending):
    if pending:
        add_authority(stores[1])
    with sqlite3.connect(stores[1]) as conn:
        if schema_fault == "table":
            conn.execute("DROP TABLE authority_wake_receipts")
        else:
            conn.execute(f"ALTER TABLE authority_wake_receipts RENAME COLUMN {schema_fault} TO unavailable")
    before = snapshot(stores)
    assert run_cli("gemini-infra") == {
        "count": None,
        "ids": [],
        "truncated": False,
        "stores": {"legacy": None, "authority": None},
        "probe": "unknown",
    }
    assert inbox_pending.hook("{}", "gemini-infra") == {"injectSteps": [{"ephemeralMessage": EXPECTED_UNKNOWN_NOTICE}]}
    assert snapshot(stores) == before


def test_invalid_stored_id_never_injects_data(stores):
    add_authority(stores[1], identifier=BODY_MARKER)
    result = checked_probe("gemini-infra")
    assert result["probe"] == "unknown"
    assert BODY_MARKER not in json.dumps(result)


def test_imported_authority_identifier(stores):
    identifier = "legacy-message-" + "a" * 32
    add_authority(stores[1], identifier=identifier)
    assert checked_probe("gemini-infra")["ids"] == [identifier]


def test_cli_returns_only_metadata(stores):
    add_legacy(stores[0])
    result = subprocess.run(
        [sys.executable, "-m", "scripts.inbox_pending", "--recipient", "gemini-infra"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    assert check_metadata(json.loads(result.stdout)) == {
        "count": 1,
        "ids": [1],
        "truncated": False,
        "stores": {"legacy": 1, "authority": 0},
        "probe": "ok",
    }
    assert BODY_MARKER not in result.stdout


def test_cli_help(capsys):
    assert inbox_pending.main(["--help"]) == 0
    assert "Outputs:" in capsys.readouterr().out


@pytest.mark.parametrize("hook_mode", [False, True])
def test_cli_bad_arguments_hide_error_data(capsys, hook_mode):
    args = ["--" + BODY_MARKER]
    if hook_mode:
        args.append("--agy-hook")
    assert inbox_pending.main(args) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert BODY_MARKER not in captured.out
    result = json.loads(captured.out)
    if hook_mode:
        assert result == {"injectSteps": [{"ephemeralMessage": EXPECTED_UNKNOWN_NOTICE}]}
    else:
        assert result["probe"] == "unknown"


def test_hook_cli_does_not_echo_stdin(stores, monkeypatch, capsys):
    from io import StringIO

    monkeypatch.setattr(sys, "stdin", StringIO(BODY_MARKER))
    assert inbox_pending.main(["--agy-hook"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {"injectSteps": [{"ephemeralMessage": EXPECTED_UNKNOWN_NOTICE}]}


@pytest.mark.parametrize(
    ("failure", "store_index", "pending"),
    [
        ("missing-store", 0, True),
        ("missing-store", 1, True),
        ("malformed-schema", 0, False),
        ("malformed-schema", 0, True),
        ("malformed-schema", 1, False),
        ("malformed-schema", 1, True),
        ("garbage-stdin", None, True),
        ("missing-slot", None, True),
    ],
)
def test_unknown_cli_notice_guides_both_drains(stores, roster, tmp_path, monkeypatch, failure, store_index, pending):
    if pending:
        add_legacy(stores[0])
        add_authority(stores[1], state="running")
    if failure == "missing-store":
        stores[store_index].unlink()
    elif failure == "malformed-schema":
        with sqlite3.connect(stores[store_index]) as conn:
            conn.execute("DROP TABLE messages" if store_index == 0 else "DROP TABLE authority_wake_receipts")
    elif failure == "missing-slot":
        monkeypatch.delenv("SESSION_HANDOFF_AGENT")
    existing_stores = [path for path in stores if path.exists()]
    before = snapshot(existing_stores)
    files = set(tmp_path.rglob("*"))
    proc = subprocess.run(
        [sys.executable, "-c", CLI_BOOTSTRAP, "--agy-hook"],
        input=BODY_MARKER if failure == "garbage-stdin" else "{}",
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert proc.returncode == 0
    assert proc.stderr == ""
    assert BODY_MARKER not in proc.stdout
    result = json.loads(proc.stdout)
    assert result == {"injectSteps": [{"ephemeralMessage": EXPECTED_UNKNOWN_NOTICE}]}
    line = result["injectSteps"][0]["ephemeralMessage"]
    assert len(line) <= 200
    assert line.isascii() and all(32 <= ord(char) < 127 for char in line)
    assert snapshot(existing_stores) == before
    assert set(tmp_path.rglob("*")) == files


def test_wal_reader_sees_latest_committed_order(stores):
    with sqlite3.connect(stores[0]) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO messages VALUES (1, 'gemini-infra', 0, 0, ?)", (BODY_MARKER,))
        writer.commit()
        assert checked_probe("gemini-infra")["ids"] == [1]


def test_retired_plane_and_relative_override_are_unknown(stores, monkeypatch, tmp_path):
    monkeypatch.delenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW")
    (tmp_path / "READ_ME_CANONICAL_ON_JOB_HOST.txt").write_text("retired")
    assert checked_probe("gemini-infra")["probe"] == "unknown"
    monkeypatch.setenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", "1")
    monkeypatch.setenv("AB_DB_PATH", "messages.db")
    assert checked_probe("gemini-infra")["probe"] == "unknown"


@pytest.mark.parametrize("count", [0, 1, 8])
def test_direct_renderer_behavior(stores, count):
    for identifier in range(1, count + 1):
        add_legacy(stores[0], identifier=identifier)
    result = inbox_pending.hook("{}", "gemini-infra")
    if not count:
        assert result == {}
    else:
        check_notice(result, count=count, authority_count=0)


@pytest.mark.parametrize("payload", ["[]", '{"value": NaN}', BODY_MARKER])
def test_direct_invalid_payload_is_unknown(stores, payload):
    assert inbox_pending.hook(payload, "gemini-infra") == {
        "injectSteps": [{"ephemeralMessage": EXPECTED_UNKNOWN_NOTICE}]
    }


def test_negative_legacy_identifier_is_unknown(stores):
    add_legacy(stores[0], identifier=-1)
    assert checked_probe("gemini-infra")["probe"] == "unknown"
