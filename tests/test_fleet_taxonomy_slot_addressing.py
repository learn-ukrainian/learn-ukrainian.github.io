"""Hermetic contract and unit tests for Taxonomy Step 4b — slot addressing and slot->holder resolution."""

from __future__ import annotations

import contextlib
import sqlite3
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


def test_roster_slots_accepted_by_validation() -> None:
    """Verify every slot configured in area_assignments.yaml is accepted by validation."""
    all_valids = _channels.get_valid_agents(assignments_path=_AREA_ASSIGNMENTS_YAML)
    assert "grok-infra" in all_valids
    assert "claude-atlas" in all_valids
    assert "codex-devops" in all_valids
    assert "gemini-hramatka" in all_valids
    assert "gemini-infra" in all_valids
    assert "claude-folk" in all_valids
    assert "codex-corpus" in all_valids
    assert "cursor-infra" in all_valids
    assert "cursor-atlas" in all_valids
    assert "codex-hramatka" in all_valids

    # Verify _validate_agent, _validate_post_agent, _validate_recipient_agent do not raise
    _channels._validate_agent("grok-infra", assignments_path=_AREA_ASSIGNMENTS_YAML)
    _channels._validate_post_agent("claude-atlas", assignments_path=_AREA_ASSIGNMENTS_YAML)
    _channels._validate_recipient_agent("codex-devops", assignments_path=_AREA_ASSIGNMENTS_YAML)
    _channels._validate_recipient_agent("cursor-infra", assignments_path=_AREA_ASSIGNMENTS_YAML)
    _inbox._validate_agent("grok-infra")
    _inbox._validate_agent("cursor-infra")


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini", "grok", "kimi", "cursor"])
def test_monitor_aliases_preserve_inbox_destinations_beside_muse(provider: str) -> None:
    slot = f"{provider}-monitor"
    # grok-monitor is a registered slot (#10835); the other monitor names keep the bare-provider inbox.
    expected = slot if provider == "grok" else provider
    assert _channels.resolve_recipient_alias(slot, assignments_path=_AREA_ASSIGNMENTS_YAML) == expected
    for muse_slot in ("muse-monitor", "muse-devops"):
        assert muse_slot in _channels.get_valid_recipient_agents(assignments_path=_AREA_ASSIGNMENTS_YAML)
        assert _channels.resolve_recipient_alias(muse_slot, assignments_path=_AREA_ASSIGNMENTS_YAML) == muse_slot
    assert _channels.resolve_recipient_alias("unknown-monitor", assignments_path=_AREA_ASSIGNMENTS_YAML) == "unknown-monitor"
    with pytest.raises(ValueError, match="Unknown delivery target"):
        _channels._validate_recipient_agent("unknown-monitor", assignments_path=_AREA_ASSIGNMENTS_YAML)


@pytest.mark.parametrize(
    ("provider", "lane"),
    [
        *((provider, lane) for provider in ("kimi", "cursor") for lane in ("folk", "bio", "hramatka", "open-model-data")),
        *(("grok", lane) for lane in ("folk", "bio", "hramatka")),
    ],
)
def test_removed_content_slots_are_not_bridge_recipients(provider: str, lane: str) -> None:
    slot = f"{provider}-{lane}"
    assert slot not in _channels.get_valid_recipient_agents(assignments_path=_AREA_ASSIGNMENTS_YAML)
    # A Kimi slot is refused first: Kimi is not a bridge recipient at all.
    refusal = "KIMI CODING-ONLY" if provider == "kimi" else "Unknown delivery target"
    with pytest.raises(ValueError, match=refusal):
        _channels._validate_recipient_agent(slot, assignments_path=_AREA_ASSIGNMENTS_YAML)


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


# ---------------------------------------------------------------------------
# 2. R2 Validation Sites Tests
# ---------------------------------------------------------------------------


def test_bottleneck_alerts_accepts_roster_slot_holder(tmp_path: Path) -> None:
    """Verify bottleneck_alerts._active_lease_holder accepts a registry roster slot as holder (R2 site 2)."""
    from agents_extensions.shared.session_streams import LeaseHolder, SessionStreamDatabase, SessionStreamStore
    from scripts.fleet_comms.bottleneck_alerts import _active_lease_holder

    db_path = tmp_path / "session-streams.sqlite3"
    db = SessionStreamDatabase(db_path)
    store = SessionStreamStore(db)
    now = datetime.now(UTC)
    store.open_session(
        stream_id="epic:4707",
        holder=LeaseHolder(
            agent="grok-infra",
            harness="grok",
            instance_id="inst-1",
            process_id=100,
            task_id="task-1",
        ),
        lineage_id="lineage-1",
        ttl_seconds=3600,
        now=now,
    )

    holder = _active_lease_holder("4707", session_db=db_path, now=now)
    assert holder == "grok-infra"


# ---------------------------------------------------------------------------
# 3. Slot->Holder Resolution Helper Tests (resolve_slot_holder)
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
    assert res.stream_id == "epic:4387"  # allow-hardcoded-epic: slot addressing taxonomy resolution
    assert res.session_id == "sess_atlas_123"
    assert res.holder_agent == "claude-infra"
    assert res.holder_harness == "claude"
    assert res.generation == 1
    assert res.expires_at == future_time
    assert res.queue_location == "channels DB delivery queue for 'claude-atlas'"


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
    assert res.stream_id == "epic:2836"  # allow-hardcoded-epic: slot addressing alias resolution
    assert res.holder_agent == "grok-infra"


# ---------------------------------------------------------------------------
# 4. Bounce Visibility Warning in Post
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 4b. Bounce/resolver warnings in post() return dict (#5889)
# ---------------------------------------------------------------------------


def test_post_bounce_warning_in_return_dict_hermetic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No-live-holder bounce warning appears in post() return dict (#5889 item 1).

    Hermetic (step-3 r2 pattern): ``resolve_slot_holder`` is stubbed to a
    deterministic no-holder result, so this does not depend on real
    session-streams state.

    MUTATION-CHECK (revert→fail): if the ``warnings`` key is removed from
    post()'s return dict, the ``in result`` and content assertions fail —
    the warning would only reach stderr and be unreachable to callers.
    """
    from scripts.orchestration import slot_routing
    from scripts.orchestration.slot_routing import SlotHolderResult

    def _no_holder(slot: str, **kwargs: object) -> SlotHolderResult:
        return SlotHolderResult(
            has_holder=False,
            slot=slot,
            area_id="infra",
            queue_location=f"channels DB delivery queue for '{slot}'",
            reason="no-live-holder",
        )

    monkeypatch.setattr(slot_routing, "resolve_slot_holder", _no_holder)

    with contextlib.suppress(Exception):
        _channels.init_db()
    with contextlib.suppress(ValueError):
        _channels.create_channel("test-bounce-ret", description="test channel")

    result = _channels.post(
        "test-bounce-ret",
        "user",
        "Hello bounce",
        to_agents=["grok-infra"],
        auto_snapshot=False,
    )

    # Item 1: warnings present in the return dict as list[str] (not just stderr).
    assert "warnings" in result
    assert isinstance(result["warnings"], list)
    assert len(result["warnings"]) == 1
    assert "recipient grok slot in area 'infra' has no live holder (no-live-holder)" in result["warnings"][0]
    assert "queued in its channels DB delivery queue" in result["warnings"][0]
    # Delivery still queued at the slot identity.
    assert len(result["delivery_ids"]) == 1


def test_post_resolver_failure_surfaces_warning_not_silent(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Resolver/import failure surfaces a warning instead of silent-dropping (#5889 item 2).

    Hermetic: ``resolve_slot_holder`` is stubbed to raise, exercising the
    exception path directly without depending on real infrastructure.

    MUTATION-CHECK (revert→fail): if the bare ``except Exception: return
    agent`` swallow is restored, ``result['warnings']`` stays empty (the
    failure is silent-dropped) and every warning assertion below fails.
    """
    from scripts.orchestration import slot_routing

    def _boom(slot: str, **kwargs: object) -> None:
        raise RuntimeError("simulated resolver/import failure")

    monkeypatch.setattr(slot_routing, "resolve_slot_holder", _boom)

    with contextlib.suppress(Exception):
        _channels.init_db()
    with contextlib.suppress(ValueError):
        _channels.create_channel("test-resolver-fail", description="test channel")

    result = _channels.post(
        "test-resolver-fail",
        "user",
        "Hello resolver-fail",
        to_agents=["grok-infra"],
        auto_snapshot=False,
    )

    # Item 2: resolver failure surfaced as a warning in the return dict...
    assert "warnings" in result
    assert any("slot resolver failed for the grok slot" in w for w in result["warnings"])
    assert any("RuntimeError" in w for w in result["warnings"])
    assert any("simulated resolver/import failure" in w for w in result["warnings"])
    # ...and on stderr (visible handling, not silent).
    captured = capsys.readouterr()
    assert "slot resolver failed for the grok slot" in captured.err
    # Delivery still queued at the slot identity (fail-open on delivery).
    assert len(result["delivery_ids"]) == 1
