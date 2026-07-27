"""Hermetic contract and unit tests for Taxonomy Step 4b — slot addressing and slot->holder resolution."""

from __future__ import annotations

import contextlib
import sqlite3
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.ai_agent_bridge import _channels, _inbox
from scripts.orchestration.slot_routing import resolve_slot_holder

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AREA_ASSIGNMENTS_YAML = _REPO_ROOT / "scripts" / "config" / "area_assignments.yaml"


# ---------------------------------------------------------------------------
# 1. Slot Roster Acceptance & Validation Tests
# ---------------------------------------------------------------------------


def test_static_tuple_members_unchanged() -> None:
    """Verify that static tuple members remain untouched and present in valid agents."""
    valids = _channels.get_valid_agents()
    for member in _channels.STATIC_VALID_AGENTS:
        assert member in valids
    assert "claude-infra" in _channels.STATIC_VALID_AGENTS


def test_roster_slots_accepted_by_validation() -> None:
    """Verify every slot configured in area_assignments.yaml is accepted by validation."""
    all_valids = _channels.get_valid_agents(assignments_path=_AREA_ASSIGNMENTS_YAML)
    assert "grok-infra" in all_valids
    assert "claude-atlas" in all_valids
    assert "codex-devops" in all_valids
    assert "kimi-hramatka" in all_valids
    assert "claude-folk" in all_valids
    assert "codex-corpus" in all_valids

    # Verify _validate_agent, _validate_post_agent, _validate_recipient_agent do not raise
    _channels._validate_agent("grok-infra", assignments_path=_AREA_ASSIGNMENTS_YAML)
    _channels._validate_post_agent("claude-atlas", assignments_path=_AREA_ASSIGNMENTS_YAML)
    _channels._validate_recipient_agent("codex-devops", assignments_path=_AREA_ASSIGNMENTS_YAML)
    _inbox._validate_agent("grok-infra")


def test_unknown_slot_rejected_naming_valids() -> None:
    """Verify unknown slot 'claude-nosucharea' is rejected with an error message listing valid agents."""
    with pytest.raises(ValueError) as exc_info:
        _channels._validate_agent("claude-nosucharea", assignments_path=_AREA_ASSIGNMENTS_YAML)

    err_msg = str(exc_info.value)
    assert "Unknown agent 'claude-nosucharea'" in err_msg
    assert "claude-infra" in err_msg
    assert "grok-infra" in err_msg

    with pytest.raises(ValueError):
        _inbox._validate_agent("claude-nosucharea")


def test_registry_absent_or_unreadable_fallback_to_static_tuple(tmp_path: Path) -> None:
    """Verify fallback to STATIC_VALID_AGENTS when area_assignments.yaml is missing or corrupt.

    MUTATION-CHECK: If fallback is removed/broken, get_valid_agents fails or crashes.
    """
    missing_file = tmp_path / "non_existent_area_assignments.yaml"
    valids_missing = _channels.get_valid_agents(assignments_path=missing_file)
    assert valids_missing == _channels.STATIC_VALID_AGENTS

    corrupt_file = tmp_path / "corrupt_area_assignments.yaml"
    corrupt_file.write_text("invalid: yaml: ::: [[", encoding="utf-8")
    valids_corrupt = _channels.get_valid_agents(assignments_path=corrupt_file)
    assert valids_corrupt == _channels.STATIC_VALID_AGENTS


def test_cache_invalidation_on_registry_edit(tmp_path: Path) -> None:
    """Verify cache invalidation when area_assignments.yaml is edited (mtime/size changed).

    MUTATION-CHECK: A static/bare LRU cache without mtime check fails to see new slots.
    """
    test_file = tmp_path / "area_assignments.yaml"
    test_file.write_text(
        """schema_version: 1
assignments:
  infra:
    slots:
      - custom-slot-v1
""",
        encoding="utf-8",
    )

    valids1 = _channels.get_valid_agents(assignments_path=test_file)
    assert "custom-slot-v1" in valids1

    # Sleep slightly or modify time to ensure mtime changes
    time.sleep(0.01)
    test_file.write_text(
        """schema_version: 1
assignments:
  infra:
    slots:
      - custom-slot-v1
      - custom-slot-v2
""",
        encoding="utf-8",
    )

    valids2 = _channels.get_valid_agents(assignments_path=test_file)
    assert "custom-slot-v2" in valids2


# ---------------------------------------------------------------------------
# 2. Slot->Holder Resolution Helper Tests (resolve_slot_holder)
# ---------------------------------------------------------------------------


@pytest.fixture
def session_db_fixture(tmp_path: Path) -> Path:
    """Create a temporary schema-conformant session-streams.sqlite3 database."""
    db_path = tmp_path / "session-streams.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY,
            stream_id TEXT NOT NULL,
            state TEXT NOT NULL
        );

        CREATE TABLE stream_leases (
            stream_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            holder_agent TEXT NOT NULL,
            holder_harness TEXT,
            generation INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            state TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
    return db_path


def test_resolve_slot_holder_live_holder(session_db_fixture: Path) -> None:
    """Verify resolve_slot_holder returns holder facts for an active, non-expired lease."""
    db_path = session_db_fixture
    future_time = (datetime.now(UTC) + timedelta(hours=2)).isoformat()

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sessions (session_id, stream_id, state) VALUES (?, ?, ?)",
        ("sess_atlas_123", "epic:4387", "open"),
    )
    conn.execute(
        """INSERT INTO stream_leases
           (stream_id, session_id, holder_agent, holder_harness, generation, expires_at, state)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("epic:4387", "sess_atlas_123", "claude-infra", "claude", 1, future_time, "active"),
    )
    conn.commit()
    conn.close()

    res = resolve_slot_holder("claude-atlas", session_db_path=db_path)
    assert res.has_holder is True
    assert res.slot == "claude-atlas"
    assert res.area_id == "atlas"
    assert res.stream_id == "epic:4387"
    assert res.session_id == "sess_atlas_123"
    assert res.holder_agent == "claude-infra"
    assert res.holder_harness == "claude"
    assert res.generation == 1
    assert res.expires_at == future_time
    assert res.queue_location == ".agent/wake/claude-atlas"


def test_resolve_slot_holder_no_holder(session_db_fixture: Path) -> None:
    """Verify resolve_slot_holder returns has_holder=False when no active lease exists."""
    res = resolve_slot_holder("grok-infra", session_db_path=session_db_fixture)
    assert res.has_holder is False
    assert res.slot == "grok-infra"
    assert res.area_id == "infra"
    assert res.queue_location == ".agent/wake/grok-infra"
    assert res.reason == "no-live-holder"


def test_resolve_slot_holder_expired_lease_treated_as_no_live_holder(session_db_fixture: Path) -> None:
    """Verify expired lease (expires_at in past) is treated as no-live-holder."""
    db_path = session_db_fixture
    past_time = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sessions (session_id, stream_id, state) VALUES (?, ?, ?)",
        ("sess_devops_456", "epic:5703", "open"),
    )
    conn.execute(
        """INSERT INTO stream_leases
           (stream_id, session_id, holder_agent, holder_harness, generation, expires_at, state)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("epic:5703", "sess_devops_456", "codex-infra", "codex", 1, past_time, "active"),
    )
    conn.commit()
    conn.close()

    res = resolve_slot_holder("codex-devops", session_db_path=db_path)
    assert res.has_holder is False
    assert res.slot == "codex-devops"
    assert res.area_id == "devops"
    assert res.reason == "no-live-holder"


def test_resolve_slot_holder_unknown_area_slot() -> None:
    """Verify resolve_slot_holder returns unknown-area reason for unmapped area slot."""
    res = resolve_slot_holder("claude-nosucharea")
    assert res.has_holder is False
    assert res.slot == "claude-nosucharea"
    assert res.reason == "unknown-area"


def test_resolve_slot_holder_alias_slot(session_db_fixture: Path) -> None:
    """Verify alias slot resolution (e.g. claude-folk -> area seminars -> epic:2836)."""
    db_path = session_db_fixture
    future_time = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO sessions (session_id, stream_id, state) VALUES (?, ?, ?)",
        ("sess_folk_789", "epic:2836", "rolling"),
    )
    conn.execute(
        """INSERT INTO stream_leases
           (stream_id, session_id, holder_agent, holder_harness, generation, expires_at, state)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("epic:2836", "sess_folk_789", "grok-infra", "grok", 2, future_time, "active"),
    )
    conn.commit()
    conn.close()

    res = resolve_slot_holder("claude-folk", session_db_path=db_path)
    assert res.has_holder is True
    assert res.slot == "claude-folk"
    assert res.area_id == "seminars"
    assert res.stream_id == "epic:2836"
    assert res.holder_agent == "grok-infra"


# ---------------------------------------------------------------------------
# 3. Bounce Visibility Warning in Post
# ---------------------------------------------------------------------------


def test_post_to_slot_with_no_live_holder_warns_and_queues(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify post to a valid slot with no live holder prints a stderr warning while still queuing delivery."""
    with contextlib.suppress(Exception):
        _channels.init_db()

    with contextlib.suppress(ValueError):
        _channels.create_channel("test-slot", description="test channel")

    result = _channels.post("test-slot", "user", "Hello slot", to_agents=["grok-infra"], auto_snapshot=False)
    captured = capsys.readouterr()

    assert "⚠️ channel-bridge: recipient slot 'grok-infra' has no live holder" in captured.err
    assert ".agent/wake/grok-infra" in captured.err
    assert len(result["delivery_ids"]) == 1
