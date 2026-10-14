"""Synthetic store proofs for the body-free pending probe (#10558)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import inbox_pending
from tests.helpers.agy_inbox_fixtures import BODY_MARKER, MESSAGE_ID, add_authority, add_legacy

pytest_plugins = ("tests.helpers.agy_inbox_fixtures",)
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("acknowledged", "consumed", "expected"), [(0, 0, 1), (1, 0, 0), (0, 1, 0), (1, 1, 0), (None, None, 1)]
)
def test_legacy_delivery_states(stores, acknowledged, consumed, expected):
    add_legacy(stores[0], acknowledged=acknowledged, consumed=consumed)
    assert inbox_pending.probe("gemini-infra") == {
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
        ("running", False, True, 0),
        ("acknowledged", False, False, 0),
        ("expired", False, False, 0),
        ("failed", False, False, 0),
        ("dead_lettered", False, False, 0),
    ],
)
def test_authority_delivery_states(stores, state, consumed, wake, expected):
    add_authority(stores[1], state=state, consumed=consumed, wake_consumed=wake)
    assert inbox_pending.probe("gemini-infra") == {
        "count": expected,
        "ids": [MESSAGE_ID] if expected else [],
        "truncated": False,
        "stores": {"legacy": 0, "authority": expected},
        "probe": "ok",
    }


@pytest.mark.parametrize("state", ["queued", "running"])
def test_expired_deadline_is_silent(stores, state):
    add_authority(stores[1], state=state, deadline="2000-01-01T00:00:00Z")
    assert inbox_pending.probe("gemini-infra")["count"] == 0


@pytest.mark.parametrize(
    "recipient",
    ["gemini-infra", "gemini", "unknown", "gemini-not-a-lane", "", "gemini-infra\n", "gemini-infra' OR 1=1--"],
)
def test_recipient_shapes(stores, recipient):
    add_legacy(stores[0], recipient="claude")
    add_legacy(stores[0], identifier=2)
    add_authority(stores[1], recipient="claude")
    result = inbox_pending.probe(recipient)
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
    assert inbox_pending.probe("gemini-infra")["probe"] == "unknown"


def test_counts_and_five_full_ids(stores):
    for identifier in range(1, 8):
        add_legacy(stores[0], identifier=identifier)
    add_authority(stores[1])
    assert inbox_pending.probe("gemini-infra") == {
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
        result = inbox_pending.probe("gemini-infra")
        assert result["count"] == 2
        assert BODY_MARKER not in json.dumps(result)
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in stores} == before
    assert set(tmp_path.iterdir()) == files


@pytest.mark.parametrize("store_index", [0, 1])
def test_missing_store_returns_unknown_without_creation(stores, store_index):
    stores[store_index].unlink()
    assert inbox_pending.probe("gemini-infra")["probe"] == "unknown"
    assert not stores[store_index].exists()


@pytest.mark.parametrize("store_index", [0, 1])
def test_locked_store_is_unknown(stores, store_index):
    with sqlite3.connect(stores[store_index]) as conn:
        conn.execute("BEGIN EXCLUSIVE")
        assert inbox_pending.probe("gemini-infra")["probe"] == "unknown"


@pytest.mark.parametrize("store_index", [0, 1])
def test_unreadable_store_is_unknown(stores, monkeypatch, store_index):
    original = inbox_pending.open_readonly

    def denied(path, **kwargs):
        if path == stores[store_index]:
            raise PermissionError(BODY_MARKER)
        return original(path, **kwargs)

    monkeypatch.setattr(inbox_pending, "open_readonly", denied)
    result = inbox_pending.probe("gemini-infra")
    assert result["probe"] == "unknown"
    assert BODY_MARKER not in json.dumps(result)


@pytest.mark.parametrize("store_index", [0, 1])
def test_schema_drift_and_corrupt_store_unknown(stores, store_index):
    stores[store_index].write_bytes(b"not sqlite " + BODY_MARKER.encode())
    assert inbox_pending.probe("gemini-infra")["probe"] == "unknown"


def test_invalid_stored_id_never_injects_data(stores):
    add_authority(stores[1], identifier=BODY_MARKER)
    result = inbox_pending.probe("gemini-infra")
    assert result["probe"] == "unknown"
    assert BODY_MARKER not in json.dumps(result)


def test_imported_authority_identifier(stores):
    identifier = "legacy-message-" + "a" * 32
    add_authority(stores[1], identifier=identifier)
    assert inbox_pending.probe("gemini-infra")["ids"] == [identifier]


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
    assert json.loads(result.stdout) == {
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
        assert result == {"injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]}
    else:
        assert result["probe"] == "unknown"


def test_hook_cli_does_not_echo_stdin(stores, monkeypatch, capsys):
    from io import StringIO

    monkeypatch.setattr(sys, "stdin", StringIO(BODY_MARKER))
    assert inbox_pending.main(["--agy-hook"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {"injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]}


def test_wal_reader_sees_latest_committed_order(stores):
    with sqlite3.connect(stores[0]) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO messages VALUES (1, 'gemini-infra', 0, 0, ?)", (BODY_MARKER,))
        writer.commit()
        assert inbox_pending.probe("gemini-infra")["ids"] == [1]


def test_retired_plane_and_relative_override_are_unknown(stores, monkeypatch, tmp_path):
    monkeypatch.delenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW")
    (tmp_path / "READ_ME_CANONICAL_ON_JOB_HOST.txt").write_text("retired")
    assert inbox_pending.probe("gemini-infra")["probe"] == "unknown"
    monkeypatch.setenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", "1")
    monkeypatch.setenv("AB_DB_PATH", "messages.db")
    assert inbox_pending.probe("gemini-infra")["probe"] == "unknown"


@pytest.mark.parametrize("count", [0, 1, 8])
def test_direct_renderer_behavior(stores, count):
    for identifier in range(1, count + 1):
        add_legacy(stores[0], identifier=identifier)
    result = inbox_pending.hook("{}", "gemini-infra")
    if not count:
        assert result == {}
    else:
        ids = "1" if count == 1 else "1,2,3,4,5; truncated"
        assert result == {
            "injectSteps": [
                {
                    "ephemeralMessage": f"PENDING ORDERS: {count} (ids {ids}); legacy: ai_agent_bridge inbox --for gemini-infra"
                }
            ]
        }


@pytest.mark.parametrize("payload", ["[]", '{"value": NaN}', BODY_MARKER])
def test_direct_invalid_payload_is_unknown(stores, payload):
    assert inbox_pending.hook(payload, "gemini-infra") == {
        "injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]
    }


def test_renderer_authority_length_budget(stores):
    add_authority(stores[1])
    add_legacy(stores[0])
    line = inbox_pending.hook("{}", "gemini-infra")["injectSteps"][0]["ephemeralMessage"]
    assert "PENDING ORDERS: 2" in line
    assert MESSAGE_ID in line
    assert len(line) <= 200


def test_direct_authority_truncation_and_store_failure(stores):
    add_authority(stores[1])
    for letter in ("b", "c"):
        add_authority(stores[1], identifier="authority-message_" + letter * 32, delivery_id=letter)
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in stores}
    assert inbox_pending.hook("{}", "gemini-infra") == {
        "injectSteps": [
            {
                "ephemeralMessage": f"PENDING ORDERS: 3 (ids {MESSAGE_ID}; truncated); authority: .venv/bin/python -m scripts.fleet_comms deliveries --help"
            }
        ]
    }
    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in stores} == before
    stores[1].unlink()
    assert inbox_pending.hook("{}", "gemini-infra") == {
        "injectSteps": [{"ephemeralMessage": inbox_pending.UNKNOWN_LINE}]
    }
    assert not stores[1].exists()
    assert hashlib.sha256(stores[0].read_bytes()).hexdigest() == before[stores[0]]


def test_negative_legacy_identifier_is_unknown(stores):
    add_legacy(stores[0], identifier=-1)
    assert inbox_pending.probe("gemini-infra")["probe"] == "unknown"


def test_main_success_metadata(stores, capsys):
    add_legacy(stores[0])
    assert inbox_pending.main(["--recipient", "gemini-infra"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "count": 1,
        "ids": [1],
        "truncated": False,
        "stores": {"legacy": 1, "authority": 0},
        "probe": "ok",
    }
