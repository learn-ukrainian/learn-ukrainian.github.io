"""B0 handler-contract trace for #10667 D02 and D05.

Each test asserts the same semantics the frozen design requires before any UI
claim: a real field or an explicit unknown, never a fabricated healthy value.
D01, D03, D04, D10, D12 and D13 have dedicated tests beside their handlers.
"""

from __future__ import annotations

import json
import sqlite3

from scripts.api import claude_account_usage
from scripts.api.fleet_router import _message_item
from scripts.api.route_contracts import contract_for_route


def test_d02_unknown_account_windows_are_explicit_unknown() -> None:
    """A missing per-account probe never becomes zero capacity or a preference."""
    claude_account_usage._reset_for_tests()
    try:
        fields = claude_account_usage.routing_budget_fields()
    finally:
        claude_account_usage._reset_for_tests()
    rows = fields["claude_accounts"]
    assert set(rows) == {"claude:a", "claude:b"}
    for row in rows.values():
        assert row["status"] == "unknown"
        assert row["age_s"] is None
        assert row["stale"] is False
        assert row["reason"] == "not_probed"
        for window in ("session5h", "weekly"):
            assert row[window] == {
                "left_pct": None,
                "resets_at": None,
                "pace": None,
                "pace_delta_pct": None,
                "leftover_pct": None,
            }
    assert fields["preferred_claude_account"] is None


def test_d02_routing_contract_declares_its_source() -> None:
    contract = contract_for_route("/api/state/routing-budget")
    assert contract is not None
    assert contract.mutates is False
    assert contract.locality == "host_affine"


def test_d05_message_metadata_never_fabricates_a_posted_blocker_or_decision() -> None:
    """D05 stays unmet rather than turning arbitrary metadata into authority."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE messages (
            message_id TEXT, conversation_id TEXT, in_reply_to TEXT, kind TEXT,
            sender TEXT, recipient TEXT, request_state TEXT, created_at TEXT,
            body_inline TEXT, body_artifact_id TEXT, metadata_json TEXT,
            authority_provenance_json TEXT, conversation_source TEXT
        )
        """
    )
    connection.execute(
        "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "msg-1",
            "conv-1",
            None,
            "blocker",
            "worker",
            "operator",
            "pending",
            "2026-10-20T10:00:00Z",
            "private body text",
            None,
            json.dumps({"blocker": {"owner": "private-owner"}, "operator_decision": {"required": True}}),
            None,
            None,
        ),
    )
    row = connection.execute("SELECT * FROM messages").fetchone()
    message = _message_item(row)

    assert message["body_available"] is True
    assert message["body_preview"] == "private body text"
    assert "blocker" not in message["metadata"]
    assert "operator_decision" not in message["metadata"]
    assert "posted_blocker" not in message
    assert "operator_decision" not in message
