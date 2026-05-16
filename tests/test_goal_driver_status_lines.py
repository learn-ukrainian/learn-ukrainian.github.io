"""Tests for the /goal status-line parser."""

from __future__ import annotations

import pytest

from scripts.goal_driver.status_lines import (
    ABORT_KIND,
    DONE_KIND,
    STATUS_KIND,
    TERMINAL_KINDS,
    WAIT_KIND,
    find_last_status_line,
    parse_status_line,
)


def test_status_line_parses_counters() -> None:
    line = "GOAL_STATUS turn=12/30 blocked=0/3 no_progress=1/3 queue_head=fix-test-x"
    parsed = parse_status_line(line)
    assert parsed is not None
    assert parsed.kind == STATUS_KIND
    assert parsed.fields["turn"] == "12/30"
    assert parsed.fields["blocked"] == "0/3"
    assert parsed.fields["no_progress"] == "1/3"
    assert parsed.fields["queue_head"] == "fix-test-x"
    assert parsed.is_terminal is False
    assert parsed.is_wait is False


def test_done_line_keeps_quoted_reason_intact() -> None:
    line = 'GOAL_DONE reason="all 5 modules audit-green per audit/INDEX.md"'
    parsed = parse_status_line(line)
    assert parsed is not None
    assert parsed.kind == DONE_KIND
    assert parsed.is_terminal is True
    assert parsed.fields["reason"] == "all 5 modules audit-green per audit/INDEX.md"


def test_abort_line_captures_all_six_fields() -> None:
    line = (
        'GOAL_ABORT reason="blocked_rounds=3" '
        'last_cmd=".venv/bin/pytest tests/test_x.py" '
        'last_cwd="/Users/k/projects/learn-ukrainian" '
        'last_output="FAILED: assertion mismatch line 47" '
        'next_action="rebase against origin/main, re-run" '
        "queue_head=fix-test-x"
    )
    parsed = parse_status_line(line)
    assert parsed is not None
    assert parsed.kind == ABORT_KIND
    assert parsed.is_terminal is True
    assert parsed.fields["reason"] == "blocked_rounds=3"
    assert parsed.fields["last_cmd"] == ".venv/bin/pytest tests/test_x.py"
    assert parsed.fields["last_cwd"] == "/Users/k/projects/learn-ukrainian"
    assert parsed.fields["last_output"] == "FAILED: assertion mismatch line 47"
    assert parsed.fields["next_action"] == "rebase against origin/main, re-run"
    assert parsed.fields["queue_head"] == "fix-test-x"


def test_wait_line_carries_signal_and_eta() -> None:
    line = (
        'GOAL_WAIT signal=watcher-b6v1j-codex-dispatch-done '
        'reason="in-flight Codex dispatch ETA 30 min" eta_s=1800'
    )
    parsed = parse_status_line(line)
    assert parsed is not None
    assert parsed.kind == WAIT_KIND
    assert parsed.is_wait is True
    assert parsed.is_terminal is False
    assert parsed.signal == "watcher-b6v1j-codex-dispatch-done"
    assert parsed.fields["eta_s"] == "1800"


def test_terminal_kinds_constant_is_exhaustive() -> None:
    assert TERMINAL_KINDS == (DONE_KIND, ABORT_KIND)
    # GOAL_WAIT is intentionally non-terminal — it suspends, not exits.
    assert WAIT_KIND not in TERMINAL_KINDS


@pytest.mark.parametrize(
    "garbage",
    [
        "",
        "   ",
        "I think we're almost done",
        "goal_status turn=1/30",  # lowercase — grammar is uppercase-only
        "PARTIAL_GOAL_DONE reason=x",
    ],
)
def test_non_status_text_returns_none(garbage: str) -> None:
    assert parse_status_line(garbage) is None


def test_find_last_status_line_picks_last_match_in_blob() -> None:
    blob = """
    Some narrative the model emitted.
    GOAL_STATUS turn=1/30 blocked=0/3 no_progress=0/3 queue_head=item-a
    More narrative.
    Inline mention of GOAL_DONE in a comment that should not match (no header anchor).
    GOAL_STATUS turn=2/30 blocked=0/3 no_progress=0/3 queue_head=item-b
    """
    parsed = find_last_status_line(blob)
    assert parsed is not None
    assert parsed.kind == STATUS_KIND
    assert parsed.fields["queue_head"] == "item-b"


def test_find_last_status_line_returns_none_when_empty() -> None:
    assert find_last_status_line("just chatter without any status line") is None


def test_malformed_quote_does_not_raise() -> None:
    # Single unbalanced quote — parser must downgrade gracefully so the
    # Stop hook stays exit-zero even if the model emits a bad line.
    line = 'GOAL_DONE reason="unterminated string'
    parsed = parse_status_line(line)
    assert parsed is not None
    assert parsed.kind == DONE_KIND
