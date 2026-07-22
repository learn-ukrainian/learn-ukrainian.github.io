"""Tests for the P1 cold-start consolidation endpoints (GH #1309).

Covered:
    /api/state/manifest       — tiny JSON index with per-component hashes
    /api/rules?format=...     — condensed rule text
    /api/session/current      — current session summary
    /api/comms/inbox?agent=   — per-agent unread deliveries
"""

from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.rules_router as rules_router
import scripts.api.session_router as session_router
import scripts.api.state_router as state_router

client = TestClient(api_main.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------
# /api/rules
# ---------------------------------------------------------------------


def test_rule_sources_includes_all_unscoped_files():
    """All always-load (API-served) rule files must be served by /api/rules."""
    expected = {
        "agents_extensions/shared/rules/operator-expectations.md",
        "agents_extensions/shared/rules/critical-rules.md",
        "agents_extensions/shared/rules/non-negotiable-rules.md",
        "agents_extensions/shared/rules/workflow.md",
        "agents_extensions/shared/rules/fleet-comms-coordination.md",
        "agents_extensions/shared/rules/delegate-must-use-worktree.md",
        "agents_extensions/shared/rules/cli-help-standard.md",
        "agents_extensions/shared/rules/model-assignment.md",
        "docs/best-practices/fleet-shared-doctrine.md",
        "docs/best-practices/fleet-role-scorecard.md",
    }
    assert set(rules_router.RULE_SOURCES) == expected
    # Order: machine routing before living scorecard (#5529).
    assert rules_router.RULE_SOURCES.index(
        "agents_extensions/shared/rules/model-assignment.md"
    ) < rules_router.RULE_SOURCES.index("docs/best-practices/fleet-role-scorecard.md")
    # Fleet-comms mid-cutover rule sits with operational workflow, before model table.
    assert rules_router.RULE_SOURCES.index(
        "agents_extensions/shared/rules/workflow.md"
    ) < rules_router.RULE_SOURCES.index(
        "agents_extensions/shared/rules/fleet-comms-coordination.md"
    )
    assert rules_router.RULE_SOURCES.index(
        "agents_extensions/shared/rules/fleet-comms-coordination.md"
    ) < rules_router.RULE_SOURCES.index(
        "agents_extensions/shared/rules/model-assignment.md"
    )


def test_rules_live_assembly_includes_fleet_scorecard():
    """Live PROJECT_ROOT must serve doctrine + scorecard so cold-starts see them."""
    resp = client.get("/api/rules?format=json")
    assert resp.status_code == 200
    body = resp.json()
    sources = body["sources"]
    assert "docs/best-practices/fleet-shared-doctrine.md" in sources
    assert "docs/best-practices/fleet-role-scorecard.md" in sources
    md = body["markdown"]
    assert "Fleet role scorecard" in md
    assert "Fleet topology" in md or "orchestrator" in md.lower()
    assert body["hash"] == hashlib.sha256(md.encode("utf-8")).hexdigest()


def test_rules_live_assembly_includes_fleet_comms_coordination():
    """Standalone TUI/UI drivers must receive dual-aware fleet-comms mid-cutover SSOT."""
    resp = client.get("/api/rules?format=json")
    assert resp.status_code == 200
    body = resp.json()
    assert "agents_extensions/shared/rules/fleet-comms-coordination.md" in body["sources"]
    md = body["markdown"]
    assert "Fleet-comms coordination" in md or "fleet-comms coordination" in md.lower()
    assert "plane-status" in md
    assert "review-pr" in md
    assert "dual_write" in md or "dual-write" in md
    assert "do not invent a competing design" in md.lower() or "competing design" in md


def test_rules_markdown_default(monkeypatch, tmp_path):
    """GET /api/rules returns text/markdown with an X-Rules-Hash header."""
    # Redirect the router at synthetic rule files so the test is hermetic.
    rule_file = tmp_path / "rules.md"
    rule_file.write_text("# Rule A\n\nBe excellent.\n", encoding="utf-8")
    monkeypatch.setattr(rules_router, "RULE_SOURCES", (str(rule_file.relative_to(tmp_path.parent)),))
    monkeypatch.setattr(rules_router, "PROJECT_ROOT", tmp_path.parent)

    resp = client.get("/api/rules")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    assert "Be excellent." in resp.text
    assert resp.headers.get("X-Rules-Hash"), "missing X-Rules-Hash"


def test_rules_json_includes_hash_and_sources(monkeypatch, tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("A body\n", encoding="utf-8")
    b.write_text("B body\n", encoding="utf-8")
    monkeypatch.setattr(rules_router, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        rules_router,
        "RULE_SOURCES",
        ("a.md", "b.md", "does-not-exist.md"),
    )

    resp = client.get("/api/rules?format=json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sources"] == ["a.md", "b.md"]  # missing file omitted, order preserved
    assert "A body" in body["markdown"] and "B body" in body["markdown"]
    # Hash is stable given the markdown string.
    assert body["hash"] == hashlib.sha256(body["markdown"].encode("utf-8")).hexdigest()


def test_rules_500_when_no_sources_readable(monkeypatch, tmp_path):
    monkeypatch.setattr(rules_router, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(rules_router, "RULE_SOURCES", ("missing.md",))
    resp = client.get("/api/rules")
    assert resp.status_code == 500


# ---------------------------------------------------------------------
# /api/session/current
# ---------------------------------------------------------------------


@pytest.fixture
def session_fixture(tmp_path, monkeypatch):
    """Point the session router at a synthetic docs/session-state dir."""
    project_root = tmp_path
    session_dir = project_root / "docs" / "session-state"
    session_dir.mkdir(parents=True)
    (session_dir / "current.md").write_text(
        "# Current Session Router\n\n"
        "Latest-Brief: docs/session-state/codex-orchestrator-handoff.md\n\n"
        "Agent-Handoff:\n"
        "- orchestrator: docs/session-state/codex-orchestrator-handoff.md\n"
        "- codex: docs/session-state/current.orchestrator.md\n",
        encoding="utf-8",
    )
    (session_dir / "codex-orchestrator-handoff.md").write_text(
        "# Current task\n\nWorking on #1309.\n\nCodex-specific handoff.\n", encoding="utf-8"
    )
    (session_dir / "current.orchestrator.md").write_text("# Pointer\n\nSee durable state.\n", encoding="utf-8")
    (session_dir / "2026-04-01-old.md").write_text("old handoff\n", encoding="utf-8")
    (session_dir / "2026-04-17-newest.md").write_text("new handoff\n", encoding="utf-8")

    monkeypatch.setattr(session_router, "PROJECT_ROOT", project_root)
    return project_root


def test_session_current_markdown(session_fixture):
    resp = client.get("/api/session/current")
    assert resp.status_code == 200
    assert "Working on #1309." in resp.text
    # Recent handoffs block appended after the current.md body.
    assert "Recent session-state files" in resp.text
    assert "2026-04-17-newest.md" in resp.text
    # Older handoffs listed too but not current router or agent handoff files.
    recent_block = resp.text.split("Recent session-state")[1]
    assert "current.md" not in recent_block
    assert "codex-orchestrator-handoff.md" not in recent_block


def test_session_current_json(session_fixture):
    resp = client.get("/api/session/current?format=json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sections"]["agent"] == "orchestrator"
    assert body["sections"]["current"] == "docs/session-state/codex-orchestrator-handoff.md"
    assert body["sections"]["router"] == "docs/session-state/current.md"
    assert body["sections"]["recent_handoffs"][0].endswith("2026-04-17-newest.md")
    assert body["hash"]
    assert body["bytes"] == len(body["markdown"].encode("utf-8"))


def test_session_current_agent_query(session_fixture):
    resp = client.get("/api/session/current?agent=codex")
    assert resp.status_code == 200
    assert "Codex-specific handoff." in resp.text
    assert "Working on #1309." in resp.text
    assert "See durable state." not in resp.text


def test_session_current_legacy_orchestrator_mapping_uses_durable_handoff(tmp_path, monkeypatch):
    project_root = tmp_path
    session_dir = project_root / "docs" / "session-state"
    session_dir.mkdir(parents=True)
    (session_dir / "current.md").write_text(
        "# Current Session Router\n\n"
        "Latest-Brief: docs/session-state/current.orchestrator.md\n\n"
        "Agent-Handoff:\n"
        "- orchestrator: docs/session-state/current.orchestrator.md\n",
        encoding="utf-8",
    )
    (session_dir / "current.orchestrator.md").write_text("# Pointer\n\nSee durable state.\n", encoding="utf-8")
    (session_dir / "codex-orchestrator-handoff.md").write_text(
        "# Durable task\n\nDurable orchestrator state.\n", encoding="utf-8"
    )
    monkeypatch.setattr(session_router, "PROJECT_ROOT", project_root)

    resp = client.get("/api/session/current?format=json")

    assert resp.status_code == 200
    body = resp.json()
    assert "Durable orchestrator state." in body["markdown"]
    assert body["sections"]["current"] == "docs/session-state/codex-orchestrator-handoff.md"


def test_session_current_codex_without_router_uses_durable_handoff(tmp_path, monkeypatch):
    project_root = tmp_path
    session_dir = project_root / "docs" / "session-state"
    session_dir.mkdir(parents=True)
    (session_dir / "codex-orchestrator-handoff.md").write_text("# Durable task\n\nCodex UI state.\n", encoding="utf-8")
    monkeypatch.setattr(session_router, "PROJECT_ROOT", project_root)

    resp = client.get("/api/session/current?agent=codex&format=json")

    assert resp.status_code == 200
    body = resp.json()
    assert "Codex UI state." in body["markdown"]
    assert body["sections"]["current"] == "docs/session-state/codex-orchestrator-handoff.md"


def test_session_current_codex_empty_router_uses_router_body(tmp_path, monkeypatch):
    project_root = tmp_path
    session_dir = project_root / "docs" / "session-state"
    session_dir.mkdir(parents=True)
    (session_dir / "current.md").write_text("# Legacy current body\n\nNo agent router yet.\n", encoding="utf-8")
    (session_dir / "codex-orchestrator-handoff.md").write_text("# Durable task\n\nCodex UI state.\n", encoding="utf-8")
    monkeypatch.setattr(session_router, "PROJECT_ROOT", project_root)

    resp = client.get("/api/session/current?agent=codex&format=json")

    assert resp.status_code == 200
    body = resp.json()
    assert "No agent router yet." in body["markdown"]
    assert "Codex UI state." not in body["markdown"]
    assert body["sections"]["current"] == "docs/session-state/current.md"


def test_session_current_legacy_pointer_remap_is_codex_or_orchestrator_only(tmp_path, monkeypatch):
    project_root = tmp_path
    session_dir = project_root / "docs" / "session-state"
    session_dir.mkdir(parents=True)
    (session_dir / "current.md").write_text(
        "# Current Session Router\n\nAgent-Handoff:\n- claude: docs/session-state/current.orchestrator.md\n",
        encoding="utf-8",
    )
    (session_dir / "current.orchestrator.md").write_text(
        "# Pointer\n\nClaude was mapped here deliberately.\n", encoding="utf-8"
    )
    (session_dir / "codex-orchestrator-handoff.md").write_text(
        "# Durable task\n\nDurable orchestrator state.\n", encoding="utf-8"
    )
    monkeypatch.setattr(session_router, "PROJECT_ROOT", project_root)

    resp = client.get("/api/session/current?agent=claude&format=json")

    assert resp.status_code == 200
    body = resp.json()
    assert "Claude was mapped here deliberately." in body["markdown"]
    assert "Durable orchestrator state." not in body["markdown"]
    assert body["sections"]["current"] == "docs/session-state/current.orchestrator.md"


def test_session_current_router_query(session_fixture):
    resp = client.get("/api/session/current?agent=router")
    assert resp.status_code == 200
    assert "Agent-Handoff:" in resp.text
    assert "Codex-specific handoff." not in resp.text


def test_session_current_rejects_invalid_agent(session_fixture):
    resp = client.get("/api/session/current?agent=../bad")
    assert resp.status_code == 400


def test_session_current_404_without_current_md(tmp_path, monkeypatch):
    project_root = tmp_path
    (project_root / "docs" / "session-state").mkdir(parents=True)
    monkeypatch.setattr(session_router, "PROJECT_ROOT", project_root)

    resp = client.get("/api/session/current")
    assert resp.status_code == 404


# ---------------------------------------------------------------------
# /api/state/manifest
# ---------------------------------------------------------------------


def test_manifest_shape_and_hashes(monkeypatch, tmp_path):
    """Manifest exposes a hash + URL for rules + session; orient + inbox don't need hashes."""
    # Stub rules + session so we get deterministic hashes. Patch the names
    # where they are USED (state_router binds them at import time via
    # top-level `from .rules_router import rules_hash` — patching the origin
    # module would not affect the already-bound reference).
    monkeypatch.setattr(state_router, "rules_hash", lambda: "r" * 64)
    monkeypatch.setattr(state_router, "session_hash", lambda: "s" * 64)

    resp = client.get("/api/state/manifest")
    assert resp.status_code == 200
    body = resp.json()

    assert set(body) >= {"generated_at", "rules", "session", "orient", "inbox"}
    assert body["rules"]["hash"] == "r" * 64
    assert body["rules"]["url"] == "/api/rules?format=markdown"
    assert body["session"]["hash"] == "s" * 64
    assert body["orient"]["url"] == "/api/orient"
    assert body["orient"]["fresh_param"] == "?fresh=true"
    assert body["inbox"]["url_template"] == "/api/comms/inbox?agent={name}"
    assert body["activity"]["url"] == "/api/comms/agent-activity"


def test_manifest_stays_small():
    """Manifest must stay under 2 KB — that's the whole point of it."""
    resp = client.get("/api/state/manifest")
    assert resp.status_code == 200
    assert len(resp.content) < 2048, (
        f"manifest grew to {len(resp.content)} bytes; keep it lean or agents will stop using it"
    )


def test_manifest_omits_research_when_flag_off(monkeypatch):
    """ADR-011 P2: with the kill switch off, the manifest is exactly the pre-P2
    shape — no ``research`` key — so existing clients are untouched."""
    monkeypatch.setenv("LEARN_UK_RESEARCH_REGISTRY_ENABLED", "false")
    resp = client.get("/api/state/manifest")
    assert resp.status_code == 200
    assert "research" not in resp.json()


@pytest.mark.parametrize("telemetry", ["0", "1"])
def test_manifest_with_research_stays_within_budget(monkeypatch, telemetry):
    """Enabled research component ≤ 512 bytes and total manifest < 2 KB, with and
    without the telemetry footer. Uses the real committed 3-record registry."""
    monkeypatch.setenv("LEARN_UK_RESEARCH_REGISTRY_ENABLED", "true")
    monkeypatch.setenv("LEARN_UKRAINIAN_TELEMETRY_FOOTER", telemetry)
    # Unresolvable session → bounded, deterministic telemetry block (no sidecar).
    resp = client.get("/api/state/manifest?session=00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 200
    body = resp.json()
    assert body["research"]["url"] == "/api/knowledge/manifest"
    assert len(body["research"]["hash"]) == 64
    component = json.dumps(body["research"], separators=(",", ":")).encode("utf-8")
    assert len(component) <= 512, f"research component grew to {len(component)} bytes"
    assert len(resp.content) < 2048, f"manifest grew to {len(resp.content)} bytes"


# ---------------------------------------------------------------------
# /api/comms/inbox
# ---------------------------------------------------------------------


def test_inbox_returns_pending_deliveries(monkeypatch):
    """The inbox endpoint surfaces pending channel deliveries for an agent."""
    import scripts.api.comms_router as comms_router  # noqa: F401 — ensure mounted
    from scripts.ai_agent_bridge import _channels

    fake_rows = [
        {
            "delivery_id": "d1",
            "message_id": "m1",
            "cm_channel": "reviews",
            "cm_from_agent": "codex",
            "body": "please review #1309 " * 20,  # > 160 chars, exercises preview truncation
            "dispatched_at": "2026-04-17T10:00:00Z",
            "attempt_count": 0,
        },
        {
            "delivery_id": "d2",
            "message_id": "m2",
            "cm_channel": "pipeline",
            "cm_from_agent": "gemini",
            "body": "short",
            "dispatched_at": "2026-04-17T10:05:00Z",
            "attempt_count": 2,
        },
    ]
    monkeypatch.setattr(_channels, "pending_deliveries_for", lambda agent: fake_rows)

    resp = client.get("/api/comms/inbox?agent=claude")
    assert resp.status_code == 200
    body = resp.json()
    assert body["agent"] == "claude"
    assert body["count"] == 2
    assert body["truncated"] is False
    assert len(body["deliveries"]) == 2
    first = body["deliveries"][0]
    assert first["delivery_id"] == "d1"
    assert first["channel"] == "reviews"
    assert first["from_agent"] == "codex"
    assert first["preview"].endswith("...")
    assert first["body_length"] == len("please review #1309 " * 20)


def test_inbox_respects_limit_and_marks_truncated(monkeypatch):
    from scripts.ai_agent_bridge import _channels

    fake_rows = [
        {
            "delivery_id": f"d{i}",
            "message_id": f"m{i}",
            "cm_channel": "shared",
            "cm_from_agent": "claude",
            "body": f"body {i}",
            "dispatched_at": "2026-04-17T10:00:00Z",
            "attempt_count": 0,
        }
        for i in range(5)
    ]
    monkeypatch.setattr(_channels, "pending_deliveries_for", lambda agent: fake_rows)

    resp = client.get("/api/comms/inbox?agent=gemini&limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 5
    assert body["truncated"] is True
    assert len(body["deliveries"]) == 2


def test_inbox_claude_infra_returns_empty_when_no_pending(monkeypatch):
    from scripts.ai_agent_bridge import _channels

    monkeypatch.setattr(_channels, "pending_deliveries_for", lambda agent: [])

    resp = client.get("/api/comms/inbox?agent=claude-infra")
    assert resp.status_code == 200
    body = resp.json()
    assert body["agent"] == "claude-infra"
    assert body["count"] == 0
    assert body["deliveries"] == []


def test_inbox_400_on_invalid_agent(monkeypatch):
    from scripts.ai_agent_bridge import _channels

    def raises(_agent):
        raise ValueError("unknown agent: foobar")

    monkeypatch.setattr(_channels, "pending_deliveries_for", raises)

    resp = client.get("/api/comms/inbox?agent=foobar")
    assert resp.status_code == 400
    # Generic error message — the comms router intentionally redacts
    # internal ValueError text (CodeQL py/stack-trace-exposure fix on
    # comms_router.py:1431, PR #1687) and surfaces a generic "invalid
    # agent" string plus a correlation `error_id` instead of leaking
    # the raised message.
    body = resp.json()
    assert body["error"] == "invalid agent"
    assert "error_id" in body


def test_agent_activity_summarizes_deliveries_and_events(monkeypatch, tmp_path):
    """The activity endpoint gives orchestrators one compact bridge snapshot."""
    import scripts.api.comms_router as comms_router

    db_path = tmp_path / "messages.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE channels (
            name TEXT PRIMARY KEY,
            created_at TEXT,
            description TEXT,
            include TEXT,
            subscribers TEXT
        );
        CREATE TABLE channel_messages (
            message_id TEXT PRIMARY KEY,
            channel TEXT,
            thread_id TEXT,
            parent_id TEXT,
            correlation_id TEXT,
            round_index INTEGER,
            from_agent TEXT,
            from_model TEXT,
            kind TEXT,
            body TEXT,
            attachments TEXT,
            context_rev_shared TEXT,
            context_rev_channel TEXT,
            monitor_state_snapshot TEXT,
            created_at TEXT
        );
        CREATE TABLE deliveries (
            delivery_id TEXT PRIMARY KEY,
            message_id TEXT,
            to_agent TEXT,
            to_model TEXT,
            status TEXT,
            dispatched_at TEXT,
            delivered_at TEXT,
            error TEXT,
            lease_until TEXT,
            attempt_count INTEGER DEFAULT 0,
            retry_after TEXT,
            last_error_kind TEXT
        );
        CREATE TABLE channel_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            delivery_id TEXT,
            thread_id TEXT,
            event TEXT,
            payload_json TEXT,
            ts TEXT
        );
    """)
    conn.execute(
        "INSERT INTO channels VALUES (?, ?, ?, ?, ?)",
        ("reviews", "2026-05-31T10:00:00Z", "", "", ""),
    )
    conn.execute(
        """
        INSERT INTO channel_messages (
            message_id, channel, thread_id, parent_id, correlation_id,
            round_index, from_agent, from_model, kind, body, attachments,
            context_rev_shared, context_rev_channel, monitor_state_snapshot,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "m1",
            "reviews",
            "t1",
            None,
            None,
            0,
            "claude",
            None,
            "post",
            "please handle this bridge item",
            None,
            "",
            "",
            None,
            "2026-05-31T10:01:00Z",
        ),
    )
    conn.executemany(
        """
        INSERT INTO deliveries (
            delivery_id, message_id, to_agent, to_model, status,
            dispatched_at, delivered_at, error, lease_until, attempt_count,
            retry_after, last_error_kind
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("d1", "m1", "codex", None, "pending", None, None, None, None, 0, None, None),
            ("d2", "m1", "gemini", None, "processing", None, None, None, "2026-05-31T10:20:00Z", 1, None, None),
        ],
    )
    conn.execute(
        "INSERT INTO channel_events (delivery_id, thread_id, event, payload_json, ts) VALUES (?, ?, ?, ?, ?)",
        (None, "t1", "reply_started", '{"agent": "codex"}', "2026-05-31T10:02:00Z"),
    )
    conn.execute(
        "INSERT INTO channel_events (delivery_id, thread_id, event, payload_json, ts) VALUES (?, ?, ?, ?, ?)",
        ("d2", "t1", "heartbeat", '{"elapsed_s": 60}', "2026-05-31T10:03:00Z"),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(comms_router, "MESSAGE_DB", db_path)

    resp = client.get("/api/comms/agent-activity?agents=codex,gemini&limit=2")
    assert resp.status_code == 200
    body = resp.json()

    assert body["totals"]["pending"] == 1
    assert body["totals"]["processing"] == 1
    assert body["agents"]["codex"]["pending"] == 1
    assert body["agents"]["codex"]["recent_events"][0]["event"] == "reply_started"
    assert body["agents"]["codex"]["next_actions"][0]["kind"] == "drain_inbox"
    assert body["agents"]["gemini"]["processing"] == 1
    assert body["agents"]["gemini"]["recent_deliveries"][0]["thread_id"] == "t1"
    assert any(action["kind"] == "watch_thread" for action in body["agents"]["gemini"]["next_actions"])
