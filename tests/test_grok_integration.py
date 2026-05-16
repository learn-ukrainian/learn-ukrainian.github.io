"""Integration test surfaces for Grok in delegate.py / ab discuss / lint.

The agent runtime registry already exposes ``grok`` via
``scripts/agent_runtime/registry.py`` (HermesGrokAdapter, ``cli_available:
True``). What was missing was the surface integration so the user could
actually invoke it from the orchestration tools the rest of the project
uses. These tests pin the surface allowlists so future churn cannot
silently strip ``grok`` from any of them.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_registry_exposes_grok():
    """The agent_runtime registry is the canonical source of truth — every
    surface allowlist tested below must consult it (directly or via the
    fallback). If grok ever falls out of the registry, all the other tests
    in this module also stop being meaningful."""
    # Importing under tests/ may not have scripts/ on path; install it.
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from agent_runtime.registry import AGENTS, available_agents

    assert "grok" in AGENTS, "grok must be in agent_runtime.registry.AGENTS"
    assert AGENTS["grok"]["cli_available"] is True
    assert "grok" in available_agents()


def test_delegate_dispatch_accepts_grok_agent():
    """``delegate.py dispatch --agent grok ...`` must parse without error.

    We use ``--dry-run`` so the subprocess only validates argparse and
    returns the task-id without actually spawning a worker. A non-zero
    exit here means argparse rejected ``grok`` from the choices list.
    """
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO_ROOT / "scripts" / "delegate.py"),
            "dispatch",
            "--agent", "grok",
            "--task-id", "test-grok-argparse-probe",
            "--prompt", "noop",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"delegate dispatch --agent grok failed:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "test-grok-argparse-probe" in result.stdout


def test_ab_channels_valid_agents_includes_grok():
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels

    importlib.reload(_channels)
    assert "grok" in _channels.VALID_AGENTS


def test_ab_channels_cli_marks_grok_cli_available():
    """``ab discuss`` requires the agent to be CLI-spawnable.

    The fallback set (used when agent_runtime is unimportable) must also
    list grok so the discuss command doesn't refuse it in degraded
    environments.
    """
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels_cli

    assert _channels_cli._cli_available_agent("grok") is True


def test_lint_agent_trailer_accepts_grok():
    """Commits authored by ``grok`` dispatches must pass the X-Agent
    trailer linter. The committer email is identical for every agent
    (the user's local git config), so the trailer is the only way to
    attribute provenance — if grok isn't on the allowed list, every
    grok-authored PR fails CI."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from audit.lint_agent_trailer import _TRAILER_RE

    sample = "X-Agent: grok/2026-05-17-integration"
    match = _TRAILER_RE.search(sample)
    assert match is not None, "lint_agent_trailer rejected grok-authored trailer"
    assert match.group("agent") == "grok"
    assert match.group("task") == "2026-05-17-integration"
