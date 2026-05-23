"""Integration test surfaces for Cursor in delegate.py / ab discuss / lint.

The agent runtime registry already exposes ``cursor`` via
``scripts/agent_runtime/registry.py`` (CursorAdapter, ``cli_available:
True``). These tests pin the surface allowlists so future churn cannot
silently strip ``cursor`` from any of them.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_registry_exposes_cursor():
    """The agent_runtime registry is the canonical source of truth."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from agent_runtime.registry import AGENTS, available_agents

    assert "cursor" in AGENTS, "cursor must be in agent_runtime.registry.AGENTS"
    assert AGENTS["cursor"]["cli_available"] is True
    assert "cursor" in available_agents()


def test_delegate_dispatch_accepts_cursor_agent():
    """``delegate.py dispatch --agent cursor ...`` must parse without error."""
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO_ROOT / "scripts" / "delegate.py"),
            "dispatch",
            "--agent", "cursor",
            "--task-id", "test-cursor-argparse-probe",
            "--prompt", "noop",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"delegate dispatch --agent cursor failed:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "test-cursor-argparse-probe" in result.stdout


def test_ab_channels_valid_agents_includes_cursor():
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels

    importlib.reload(_channels)
    assert "cursor" in _channels.VALID_AGENTS


def test_ab_channels_cli_marks_cursor_cli_available():
    """``ab discuss`` requires the agent to be CLI-spawnable.

    The fallback set (used when agent_runtime is unimportable) must also
    list cursor so the discuss command doesn't refuse it in degraded
    environments.
    """
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels_cli

    assert _channels_cli._cli_available_agent("cursor") is True


def test_lint_agent_trailer_accepts_cursor():
    """Commits authored by ``cursor`` dispatches must pass the X-Agent trailer linter."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from audit.lint_agent_trailer import _TRAILER_RE

    sample = "X-Agent: cursor/2026-05-23-integration"
    match = _TRAILER_RE.search(sample)
    assert match is not None, "lint_agent_trailer rejected cursor-authored trailer"
    assert match.group("agent") == "cursor"
    assert match.group("task") == "2026-05-23-integration"
