"""Integration test surfaces for Grok in delegate.py / ab discuss / lint.

The canonical native CLI seat is ``grok`` (``GrokBuildAdapter``). Permanent
alias ``grok-build`` and demoted Hermes path ``grok-hermes`` remain on the
surface allowlists. These tests pin that future churn cannot silently strip
any of them.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_registry_exposes_native_and_hermes_grok_seats():
    """Registry must expose native ``grok``, permanent alias ``grok-build``,
    and demoted Hermes ``grok-hermes``."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from agent_runtime.registry import AGENTS, available_agents

    assert "grok" in AGENTS
    assert "grok-build" in AGENTS
    assert "grok-hermes" in AGENTS
    assert "grok_build:GrokBuildAdapter" in AGENTS["grok"]["adapter"]
    assert "hermes_grok:HermesGrokAdapter" in AGENTS["grok-hermes"]["adapter"]
    assert AGENTS["grok"]["cli_available"] is True
    assert AGENTS["grok-hermes"]["cli_available"] is True
    for name in ("grok", "grok-build", "grok-hermes"):
        assert name in available_agents()


def test_delegate_dispatch_accepts_grok_agent_and_alias():
    """``--agent grok`` and permanent alias ``--agent grok-build`` parse."""
    for agent, task in (
        ("grok", "test-grok-argparse-probe"),
        ("grok-build", "test-grok-build-argparse-probe"),
        ("grok-hermes", "test-grok-hermes-argparse-probe"),
    ):
        result = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "delegate.py"),
                "dispatch",
                "--agent",
                agent,
                "--task-id",
                task,
                "--prompt",
                "noop",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"delegate dispatch --agent {agent} failed:\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
        )
        assert task in result.stdout


def test_ab_channels_valid_agents_includes_grok_seats():
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels

    importlib.reload(_channels)
    for name in ("grok", "grok-build", "grok-hermes"):
        assert name in _channels.VALID_AGENTS


def test_ab_channels_cli_marks_grok_cli_available():
    """``ab discuss`` requires the agent to be CLI-spawnable."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels_cli

    for name in ("grok", "grok-build", "grok-hermes"):
        assert _channels_cli._cli_available_agent(name) is True


def test_lint_agent_trailer_accepts_grok_and_alias():
    """Native seat, permanent alias, and hermes trailers must all validate."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from audit.lint_agent_trailer import _TRAILER_RE

    for agent in ("grok", "grok-build", "grok-hermes"):
        sample = f"X-Agent: {agent}/2026-05-17-integration"
        match = _TRAILER_RE.search(sample)
        assert match is not None, f"lint_agent_trailer rejected {agent!r}"
        assert match.group("agent") == agent
