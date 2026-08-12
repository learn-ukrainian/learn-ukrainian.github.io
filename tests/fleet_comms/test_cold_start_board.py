"""Tests for fleet-comms driver cold start board (Sol PR-2)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.fleet_comms.cli import EXIT_OK
from scripts.fleet_comms.cli import main as cli_main
from scripts.fleet_comms.cold_start_board import (
    MAX_BOARD_BYTES,
    _probe_backlog_and_dead_letters,
    _probe_inbox,
    build_cold_start_board,
    cap_data,
    render_markdown_board,
    run_fail_open_probe,
)


def _seed_legacy_broker(db: Path) -> None:
    """Real legacy broker schema: deliveries has no channel/recipient/sender/kind."""
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE channel_messages (
          message_id TEXT PRIMARY KEY,
          channel TEXT,
          from_agent TEXT,
          kind TEXT,
          body TEXT,
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
          attempt_count INTEGER DEFAULT 0
        );
        INSERT INTO channel_messages VALUES
          ('m1','fleet','codex','task','SECRET_BODY_SHOULD_NOT_LEAK','2026-08-01T10:00:00Z'),
          ('m2','fleet','claude','notice','also-secret','2026-08-01T11:00:00Z');
        INSERT INTO deliveries VALUES
          ('d1','m1','claude',NULL,'pending',NULL,NULL,0),
          ('d2','m2','claude',NULL,'dispatched','2026-08-01T11:01:00Z',NULL,1),
          ('d3','m2','codex',NULL,'delivered','2026-08-01T11:02:00Z','2026-08-01T11:03:00Z',1);
        """
    )
    conn.commit()
    conn.close()


def _seed_authority_plane(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    plane_db = root / "comms.sqlite3"
    conn = sqlite3.connect(plane_db)
    conn.executescript(
        """
        CREATE TABLE authority_deliveries (
          delivery_id TEXT PRIMARY KEY,
          message_id TEXT NOT NULL,
          recipient TEXT NOT NULL,
          state TEXT NOT NULL,
          deadline_at TEXT,
          lease_owner TEXT,
          lease_expires_at TEXT,
          fence_token INTEGER NOT NULL DEFAULT 0,
          attempt_count INTEGER NOT NULL DEFAULT 0,
          acknowledgment_artifact_id TEXT,
          terminal_sha256 TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          completed_at TEXT
        );
        CREATE TABLE authority_dead_letters (
          dead_letter_id TEXT PRIMARY KEY,
          delivery_id TEXT UNIQUE,
          job_id TEXT UNIQUE,
          reason_code TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        INSERT INTO authority_deliveries VALUES
          ('auth-d1','auth-m1','claude','queued',NULL,NULL,NULL,0,0,NULL,NULL,
           '2026-08-01T12:00:00Z','2026-08-01T12:00:00Z',NULL),
          ('auth-d2','auth-m2','claude','running',NULL,'worker',NULL,1,2,NULL,NULL,
           '2026-08-01T12:01:00Z','2026-08-01T12:02:00Z',NULL),
          ('auth-d3','auth-m3','codex','queued',NULL,NULL,NULL,0,0,NULL,NULL,
           '2026-08-01T12:03:00Z','2026-08-01T12:03:00Z',NULL),
          ('auth-d4','auth-m4','claude','acknowledged',NULL,NULL,NULL,0,1,NULL,'sha',
           '2026-08-01T11:00:00Z','2026-08-01T11:05:00Z','2026-08-01T11:05:00Z');
        INSERT INTO authority_dead_letters VALUES
          ('auth-dl1','auth-d4',NULL,'attempts_exhausted','2026-08-01T11:06:00Z');
        """
    )
    conn.commit()
    conn.close()
    return plane_db


def test_all_probes_board_structure():
    """Board emitted contains expected top-level keys and all 10 diagnostic probes."""
    board = build_cold_start_board(
        stream_id="epic:4707",
        agent="agy/cold-start-pr2-board",
        needle="board",
    )

    assert "timestamp" in board
    assert "board_status" in board
    assert board["stream_id"] == "epic:4707"
    assert board["agent"] == "agy/cold-start-pr2-board"
    assert board["needle"] == "board"
    assert "probes" in board

    probes = board["probes"]
    expected_probes = {
        "capsule_session_env",
        "plane_status",
        "backlog_and_dead_letters",
        "bottleneck_slice",
        "orient_lean",
        "issues_streams_membership",
        "session_streams_and_handoff",
        "inbox_check",
        "gh_pr_list",
        "needle_search",
    }
    assert expected_probes.issubset(set(probes.keys()))

    for name in expected_probes:
        pdict = probes[name]
        assert "status" in pdict
        assert "elapsed_ms" in pdict
        assert "error" in pdict
        assert "data" in pdict
        assert pdict["status"] in {"ok", "degraded", "error", "skipped"}


def test_probe_failure_degrades():
    """An exception inside a probe wrapper degrades the board fail-open without raising."""

    def broken_probe():
        raise RuntimeError("simulated database failure")

    result = run_fail_open_probe("test_broken", broken_probe)
    assert result.status == "error"
    assert result.error == "RuntimeError: simulated database failure"
    assert result.data is None
    assert result.elapsed_ms >= 0.0

    # Test full board building with a patched broken probe
    with patch(
        "scripts.fleet_comms.cold_start_board._probe_plane_status",
        side_effect=RuntimeError("plane crash"),
    ):
        board = build_cold_start_board(stream_id="epic:123")
        assert board["board_status"] == "degraded"
        assert board["probes"]["plane_status"]["status"] == "error"
        assert "plane crash" in board["probes"]["plane_status"]["error"]
        # Other probes still ran
        assert board["probes"]["capsule_session_env"]["status"] == "ok"


def test_size_cap():
    """Probe data truncates strings >200 chars, lists >5 items, and keeps board <=16KiB."""
    long_string = "x" * 300
    long_list = [f"item_{i}" for i in range(20)]
    sample_data = {
        "text": long_string,
        "items": long_list,
        "nested": {"deep": "y" * 250},
    }

    capped = cap_data(sample_data, max_str=200, max_list=5)

    assert len(capped["text"]) < 300
    assert "...[truncated" in capped["text"]
    assert len(capped["items"]) == 6  # 5 items + 1 truncated marker
    assert capped["items"][-1] == {"_truncated": "15 items omitted"}

    # Verify overall board JSON output respects 16KiB limit
    board = build_cold_start_board(stream_id="epic:9999", needle="test")
    serialized = json.dumps(board, indent=2)
    assert len(serialized.encode("utf-8")) <= MAX_BOARD_BYTES


def test_no_claim_or_write_calls(monkeypatch):
    """Verify that building cold start board makes no session lease claim or write calls."""
    try:
        from agents_extensions.shared.session_streams import handoff

        def forbidden_claim(*args, **kwargs):
            pytest.fail("claim_stream must never be called during cold-start-board generation")

        monkeypatch.setattr(handoff, "claim_stream", forbidden_claim)
    except ImportError:
        pass  # Module not loaded, claim cannot be called

    board = build_cold_start_board(stream_id="epic:4707", agent="test_agent")
    assert board["board_status"] in {"ok", "degraded"}


def test_markdown_path():
    """Verify markdown output path renders structured briefing."""
    board = build_cold_start_board(
        stream_id="epic:4707",
        agent="agy/cold-start-pr2-board",
        needle="board",
    )
    md = render_markdown_board(board)

    assert "# Driver Cold Start Board" in md
    assert "- **Stream ID:** `epic:4707`" in md
    assert "- **Agent:** `agy/cold-start-pr2-board`" in md
    assert "## Diagnostic Probes" in md
    assert "### `capsule_session_env`" in md
    assert len(md.encode("utf-8")) <= MAX_BOARD_BYTES


def test_cli_cold_start_board(capsys):
    """CLI subcommand cold-start-board runs cleanly and returns exit code 0."""
    code = cli_main(["cold-start-board", "--stream-id", "epic:4707", "--agent", "test-agent"])
    assert code == EXIT_OK

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["stream_id"] == "epic:4707"
    assert payload["agent"] == "test-agent"
    assert "probes" in payload


def test_cli_cold_start_board_markdown(capsys):
    """CLI subcommand cold-start-board with --format markdown returns exit code 0."""
    code = cli_main(
        [
            "cold-start-board",
            "--format",
            "markdown",
            "--stream-id",
            "epic:4707",
            "--agent",
            "test-agent",
        ]
    )
    assert code == EXIT_OK

    captured = capsys.readouterr()
    assert "# Driver Cold Start Board" in captured.out
    assert "epic:4707" in captured.out


def test_probe_inbox_legacy_schema_ok(tmp_path: Path, monkeypatch) -> None:
    """Legacy deliveries without channel/recipient columns must not degrade."""
    broker = tmp_path / "messages.db"
    _seed_legacy_broker(broker)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "off")
    monkeypatch.setenv("AB_DB_PATH", str(broker))

    result = _probe_inbox(root=None, repo_root=tmp_path, agent="claude")
    assert result.status == "ok"
    assert result.error is None
    assert result.data["source"] == "legacy"
    assert result.data["inbox_pending_count"] == 2
    assert result.data["matched_agent"] == "claude"
    recent = result.data["recent_deliveries"]
    assert len(recent) == 2
    assert {r["delivery_id"] for r in recent} == {"d1", "d2"}
    blob = json.dumps(result.data)
    assert "SECRET_BODY" not in blob
    assert "also-secret" not in blob


def test_probe_inbox_authority_counts_agent(tmp_path: Path, monkeypatch) -> None:
    """Authority path counts queued/running rows for the exact recipient."""
    plane_root = tmp_path / "plane"
    _seed_authority_plane(plane_root)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")

    result = _probe_inbox(root=plane_root, repo_root=tmp_path, agent="claude")
    assert result.status == "ok"
    assert result.error is None
    assert result.data["source"] == "authority"
    assert result.data["inbox_pending_count"] == 2
    assert result.data["matched_agent"] == "claude"
    states = {r["state"] for r in result.data["recent_deliveries"]}
    assert states == {"queued", "running"}
    assert all("body" not in r for r in result.data["recent_deliveries"])


def test_probe_inbox_authority_hyphen_alias(tmp_path: Path, monkeypatch) -> None:
    """Cheap hyphen base alias matches when exact recipient is absent."""
    plane_root = tmp_path / "plane"
    _seed_authority_plane(plane_root)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")

    result = _probe_inbox(root=plane_root, repo_root=tmp_path, agent="claude-infra")
    assert result.status == "ok"
    assert result.data["inbox_pending_count"] == 2
    assert result.data["matched_agent"] == "claude"


def test_probe_backlog_labels_authority_source(tmp_path: Path, monkeypatch) -> None:
    """Backlog probe uses authority collectors and labels source under authority mode."""
    plane_root = tmp_path / "plane"
    _seed_authority_plane(plane_root)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")

    data = _probe_backlog_and_dead_letters(root=plane_root, repo_root=tmp_path)
    assert data["source"] == "authority"
    # exclude_retired keeps non-gemini; fixture has claude×2 + codex×1 = 3
    assert data["backlog_total"] == 3
    assert data["dead_letters_total"] == 1
    assert "claude" in data["backlog_by_agent"]


def test_probe_backlog_labels_legacy_source(tmp_path: Path, monkeypatch) -> None:
    """Backlog probe falls back to broker DB and labels source=legacy when plane is off."""
    broker = tmp_path / "messages.db"
    _seed_legacy_broker(broker)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "off")
    monkeypatch.setenv("AB_DB_PATH", str(broker))

    data = _probe_backlog_and_dead_letters(root=tmp_path / "missing-plane", repo_root=tmp_path)
    assert data["source"] == "legacy"
    assert data["backlog_total"] == 2
    assert data["backlog_by_agent"].get("claude") == 2
