"""Shared synthetic inbox stores for pending-order tests (#10558)."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.fleet_comms.migrations import apply_migrations

BODY_MARKER = "UNIQUE_PRIVATE_BODY_MUST_NEVER_LEAVE_STORE_10558"
MESSAGE_ID = "authority-message_" + "a" * 32
MONITOR_PROVIDERS = ("claude", "codex", "gemini", "agy", "grok", "cursor")
ROOT = Path(__file__).resolve().parents[2]
CLI_BOOTSTRAP = (
    "import os, runpy; from pathlib import Path; "
    "from scripts.ai_agent_bridge import _channels; "
    "_channels.ASSIGNMENTS_PATH = Path(os.environ['TEST_INBOX_ROSTER']); "
    "runpy.run_module('scripts.inbox_pending', run_name='__main__')"
)


@pytest.fixture
def roster(tmp_path, monkeypatch):
    """Replace only the roster file and executable boundary, never alias logic."""
    from scripts.ai_agent_bridge import _channels

    path = tmp_path / "assignments.yaml"
    path.write_text("assignments:\n  infra:\n    slots: [gemini-infra, codex-core]\n  monitor:\n    slots: []\n")
    monkeypatch.setattr(_channels, "ASSIGNMENTS_PATH", path)
    monkeypatch.setenv("TEST_INBOX_ROSTER", str(path))
    interpreter = tmp_path / "roster-interpreter"
    interpreter.write_text(
        f"#!{sys.executable}\nimport os, sys\n"
        f"if sys.argv[1:3] == ['-m', 'scripts.inbox_pending']:\n"
        f" os.execv({sys.executable!r}, [{sys.executable!r}, '-c', {CLI_BOOTSTRAP!r}, *sys.argv[3:]])\n"
        f"os.execv({sys.executable!r}, [{sys.executable!r}, *sys.argv[1:]])\n"
    )
    interpreter.chmod(0o700)
    monkeypatch.setenv("LU_DRIVER_STATE_PYTHON", str(interpreter))
    return path


def run_cli(recipient):
    command = (
        [sys.executable, "-c", CLI_BOOTSTRAP]
        if "TEST_INBOX_ROSTER" in os.environ
        else [sys.executable, "-m", "scripts.inbox_pending"]
    )
    proc = subprocess.run([*command, "--recipient", recipient], cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert proc.returncode == 0
    assert proc.stderr == ""
    assert BODY_MARKER not in proc.stdout
    return json.loads(proc.stdout)


def snapshot(stores):
    """Full SQLite rows, including bodies, leases and receipts, plus file bytes."""
    result = []
    for path in stores:
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as conn:
            result.append((tuple(conn.iterdump()), path.read_bytes()))
    return result


@pytest.fixture
def stores(tmp_path, monkeypatch):
    legacy = tmp_path / "messages.db"
    authority = tmp_path / "comms.sqlite3"
    with sqlite3.connect(legacy) as conn:
        conn.execute(
            "CREATE TABLE messages(id INTEGER PRIMARY KEY, to_llm TEXT, acknowledged INTEGER, consumed_by_live_driver INTEGER, content TEXT)"
        )
    with sqlite3.connect(authority) as conn:
        apply_migrations(conn)
    monkeypatch.setenv("AB_DB_PATH", str(legacy))
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path))
    monkeypatch.setenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", "1")
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "gemini-infra")
    monkeypatch.setenv("LU_DRIVER_STATE_PYTHON", sys.executable)
    return legacy, authority


def add_legacy(path, *, recipient="gemini-infra", acknowledged=0, consumed=0, identifier=1):
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (identifier, recipient, acknowledged, consumed, BODY_MARKER)
        )


def add_authority(
    path,
    *,
    state="queued",
    recipient="gemini-infra",
    consumed=False,
    wake_consumed=False,
    deadline=None,
    identifier=MESSAGE_ID,
    delivery_id="delivery-1",
):
    # Full production migrations above ensure columns and constraints stay real.
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO comms_messages(message_id, conversation_id, kind, sender, body_inline, created_at) VALUES (?, 'conversation-1', 'supervisory-request', 'supervisor', ?, '')",
            (identifier, BODY_MARKER),
        )
        conn.execute(
            "INSERT INTO authority_deliveries(delivery_id, message_id, recipient, state, deadline_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (delivery_id, identifier, recipient, state, deadline, "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        if state == "running":
            conn.execute(
                "UPDATE authority_deliveries SET lease_owner='synthetic-driver', lease_expires_at='2099-01-01T00:00:00Z', fence_token=1, attempt_count=1 WHERE delivery_id=?",
                (delivery_id,),
            )
        if consumed:
            conn.execute(
                "INSERT INTO authority_idempotency VALUES (?, '1', 'digest', 'generation', '2026-01-01T00:00:00Z')",
                (f"supervisory-consumption:{delivery_id}",),
            )
        if wake_consumed:
            conn.execute(
                "INSERT INTO authority_wake_receipts(wake_id, delivery_id, recipient, state, emitted_at) VALUES (?, ?, ?, 'consumed', '2026-01-01T00:00:00Z')",
                (f"wake-{delivery_id}", delivery_id, recipient),
            )
