"""Shared synthetic inbox stores for pending-order tests (#10558)."""

from __future__ import annotations

import sqlite3
import sys

import pytest

from scripts.fleet_comms.migrations import apply_migrations

BODY_MARKER = "UNIQUE_PRIVATE_BODY_MUST_NEVER_LEAVE_STORE_10558"
MESSAGE_ID = "authority-message_" + "a" * 32


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
):
    # Full production migrations above ensure columns and constraints stay real.
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO comms_messages(message_id, conversation_id, kind, sender, body_inline, created_at) VALUES (?, 'conversation-1', 'supervisory-request', 'supervisor', ?, '')",
            (identifier, BODY_MARKER),
        )
        conn.execute(
            "INSERT INTO authority_deliveries(delivery_id, message_id, recipient, state, deadline_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("delivery-1", identifier, recipient, state, deadline, "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        if state == "running":
            conn.execute(
                "UPDATE authority_deliveries SET lease_owner='synthetic-driver', lease_expires_at='2099-01-01T00:00:00Z', fence_token=1, attempt_count=1"
            )
        if consumed:
            conn.execute(
                "INSERT INTO authority_idempotency VALUES (?, '1', 'digest', 'generation', '2026-01-01T00:00:00Z')",
                ("supervisory-consumption:delivery-1",),
            )
        if wake_consumed:
            conn.execute(
                "INSERT INTO authority_wake_receipts(wake_id, delivery_id, recipient, state, emitted_at) VALUES ('wake-1', 'delivery-1', ?, 'consumed', '2026-01-01T00:00:00Z')",
                (recipient,),
            )
