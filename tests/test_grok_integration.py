"""Integration test surfaces for Grok in delegate.py / ab discuss / lint.

The canonical native CLI seat is ``grok`` (``GrokBuildAdapter``). Permanent
alias ``grok-build`` remains on the surface allowlists. These tests pin that
future churn cannot silently strip either of them.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ab_channels_cli_marks_grok_cli_available():
    """``ab discuss`` requires the agent to be CLI-spawnable."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from lu_machinery.ai_agent_bridge import _channels_cli

    assert _channels_cli._cli_available_agent("grok") is True
    assert _channels_cli._cli_available_agent("grok-build") is True


def test_lint_agent_trailer_accepts_grok_and_alias():
    """Native seat and permanent alias trailers must both validate."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from audit.lint_agent_trailer import _TRAILER_RE

    for agent in ("grok", "grok-build"):
        sample = f"X-Agent: {agent}/2026-05-17-integration"
        match = _TRAILER_RE.search(sample)
        assert match is not None, f"lint_agent_trailer rejected {agent!r}"
        assert match.group("agent") == agent
