"""Regression tests for ai_agent_bridge._db.set_session (grok-build crash fix).

Bug: `set_session` raised `ValueError: Unknown session agent: grok-build` and
crashed `ask-grok-build` AFTER a successful run, because grok-build is
resume_policy="never" yet returns a session id, and only claude/gemini/codex had
session columns. Fix: set_session is a no-op for always-fresh agents (those
without a persisted session column), instead of raising.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge._db import (
    _session_column,
    get_session,
    init_db,
    set_session,
)


@pytest.fixture
def bridge_db(tmp_path):
    """Use a temporary broker DB so tests never touch the real one."""
    db_path = tmp_path / "messages.db"
    with patch("ai_agent_bridge._db.DB_PATH", db_path):
        conn = init_db()
        conn.close()
        yield db_path


def test_session_column_known_resumable_agents():
    assert _session_column("claude") == "claude_session_id"
    assert _session_column("gemini") == "gemini_session_id"
    assert _session_column("codex") == "codex_session_id"


@pytest.mark.parametrize("agent", ["grok-build", "agy", "cursor", "hermes", "deepseek-v4-pro"])
def test_session_column_none_for_always_fresh_agents(agent):
    """Always-fresh agents have no persisted column -> None (no longer raises)."""
    assert _session_column(agent) is None


def test_set_session_persists_resumable_agent(bridge_db):
    set_session("task-1", "codex", "codex-session-abcdef12")
    assert get_session("task-1")["codex"] == "codex-session-abcdef12"


def test_set_session_noop_for_grok_build_does_not_raise(bridge_db):
    """The exact regression: grok-build must not crash set_session."""
    # Must not raise (previously ValueError: Unknown session agent: grok-build).
    set_session("task-2", "grok-build", "019ef5b4-8c38-7421-85ff")
    # And it is a genuine no-op: the resumable columns stay empty.
    sess = get_session("task-2")
    assert sess["claude"] is None
    assert sess["gemini"] is None
    assert sess["codex"] is None


@pytest.mark.parametrize("agent", ["agy", "cursor", "hermes"])
def test_set_session_noop_for_other_fresh_agents(bridge_db, agent):
    set_session(f"task-{agent}", agent, "some-session-id")
    sess = get_session(f"task-{agent}")
    assert sess == {"claude": None, "gemini": None, "codex": None}
