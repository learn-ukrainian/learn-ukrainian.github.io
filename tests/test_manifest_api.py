"""Tests for the P1 cold-start consolidation endpoints (GH #1309).

Covered:
    /api/state/manifest       — tiny JSON index with per-component hashes
    /api/rules?format=...     — condensed rule text
    /api/session/current      — current session summary
    /api/comms/inbox?agent=   — per-agent unread deliveries
"""

from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.rules_router as rules_router
import scripts.api.session_router as session_router

client = TestClient(api_main.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------
# /api/rules
# ---------------------------------------------------------------------


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
        rules_router, "RULE_SOURCES",
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
        "# Current task\n\nWorking on #1309.\n", encoding="utf-8"
    )
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
    # Older handoffs listed too but not current.md itself.
    assert "current.md" not in resp.text.split("Recent session-state")[1]


def test_session_current_json(session_fixture):
    resp = client.get("/api/session/current?format=json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sections"]["current"] == "docs/session-state/current.md"
    assert body["sections"]["recent_handoffs"][0].endswith("2026-04-17-newest.md")
    assert body["hash"]
    assert body["bytes"] == len(body["markdown"].encode("utf-8"))


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
    # Stub rules + session so we get deterministic hashes.
    monkeypatch.setattr(rules_router, "rules_hash", lambda: "r" * 64)
    monkeypatch.setattr(session_router, "session_hash", lambda: "s" * 64)

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


def test_manifest_stays_small():
    """Manifest must stay under 2 KB — that's the whole point of it."""
    resp = client.get("/api/state/manifest")
    assert resp.status_code == 200
    assert len(resp.content) < 2048, (
        f"manifest grew to {len(resp.content)} bytes; keep it lean or "
        "agents will stop using it"
    )


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


def test_inbox_400_on_invalid_agent(monkeypatch):
    from scripts.ai_agent_bridge import _channels

    def raises(_agent):
        raise ValueError("unknown agent: foobar")

    monkeypatch.setattr(_channels, "pending_deliveries_for", raises)

    resp = client.get("/api/comms/inbox?agent=foobar")
    assert resp.status_code == 400
    assert "unknown agent" in resp.json()["error"]
