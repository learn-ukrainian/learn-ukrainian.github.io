"""Deadlock-prevention contracts for synchronous lifecycle hooks."""

from __future__ import annotations

import json
import time
from pathlib import Path

from scripts.agent_runtime.bounded_command import TIMEOUT_EXIT_CODE, run

REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_HOOKS = REPO_ROOT / "agents_extensions" / "codex" / "hooks.json"
SESSION_SETUP = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "session-setup.sh"
POST_COMPACT = REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "post-compact.sh"


def test_bounded_command_terminates_a_slow_process() -> None:
    started = time.monotonic()

    result = run(["/bin/bash", "-c", "sleep 5"], timeout_seconds=0.05)

    assert result == TIMEOUT_EXIT_CODE
    assert time.monotonic() - started < 1


def test_session_start_has_a_hard_outer_budget() -> None:
    manifest = json.loads(CODEX_HOOKS.read_text(encoding="utf-8"))
    session_hook = manifest["hooks"]["SessionStart"][0]["hooks"][0]

    assert session_hook["timeout"] == 15


def test_session_start_defers_optional_network_diagnostics() -> None:
    source = SESSION_SETUP.read_text(encoding="utf-8")

    assert "gh issue list" not in source
    assert "curl " not in source
    assert "check_decisions.py" not in source
    assert "check_adrs.py" not in source
    assert "check_postmortems.py" not in source
    assert "Orientation diagnostics:" in source


def test_rollover_and_postcompact_commands_are_bounded() -> None:
    session_source = SESSION_SETUP.read_text(encoding="utf-8")
    compact_source = POST_COMPACT.read_text(encoding="utf-8")

    assert "LEARN_UKRAINIAN_LOCK_TIMEOUT_SECONDS=1" in session_source
    assert "THREAD_ROLLOVER_COMMAND_TIMEOUT_SECONDS=3" in session_source
    assert 'run_bounded 3 "$ROLLOVER_PYTHON"' in session_source
    assert 'run_bounded 2 "$ROLLOVER_PYTHON"' in compact_source
