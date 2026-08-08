"""Tests for fleet-comms driver cold start board (Sol PR-2)."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from scripts.fleet_comms.cli import EXIT_OK
from scripts.fleet_comms.cli import main as cli_main
from scripts.fleet_comms.cold_start_board import (
    MAX_BOARD_BYTES,
    build_cold_start_board,
    cap_data,
    render_markdown_board,
    run_fail_open_probe,
)


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
