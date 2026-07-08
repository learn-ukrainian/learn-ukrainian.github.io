"""Integration test surfaces for Agy in ab discuss / inbox / lint.

The agent runtime registry already exposes ``agy`` via
``scripts/agent_runtime/registry.py`` (AgyAdapter, ``cli_available:
True``). These tests pin the bridge allowlists so future churn cannot
silently strip ``agy`` from ``ab discuss --with``.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_registry_exposes_agy():
    """The agent_runtime registry is the canonical source of truth."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from agent_runtime.registry import AGENTS, available_agents

    assert "agy" in AGENTS, "agy must be in agent_runtime.registry.AGENTS"
    assert AGENTS["agy"]["cli_available"] is True
    assert AGENTS["agy"]["resume_policy"] == "bridge_only"
    assert "agy" in available_agents()


def test_delegate_dispatch_accepts_agy_agent():
    """``delegate.py dispatch --agent agy ...`` must parse without error."""
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO_ROOT / "scripts" / "delegate.py"),
            "dispatch",
            "--agent",
            "agy",
            "--task-id",
            "test-agy-argparse-probe",
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
        f"delegate dispatch --agent agy failed:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "test-agy-argparse-probe" in result.stdout


def test_ab_channels_valid_agents_includes_agy():
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels

    importlib.reload(_channels)
    assert "agy" in _channels.VALID_AGENTS


def test_ab_channels_cli_marks_agy_cli_available():
    """``ab discuss`` requires the agent to be CLI-spawnable."""
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from ai_agent_bridge import _channels_cli

    assert _channels_cli._cli_available_agent("agy") is True


def test_ab_discuss_accepts_agy_in_with_list(
    tmp_path, monkeypatch,
):
    """``ab discuss --with agy`` passes agent validation and invokes runtime."""
    from types import SimpleNamespace

    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    from ai_agent_bridge import _channels, _channels_cli, _db

    monkeypatch.setattr(_db, "DB_PATH", tmp_path / "bridge.db")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels, "context_sha256", lambda path: "")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "", "revs": {}, "missing": []},
    )

    _channels.create_channel("shared", exist_ok=True)
    _channels.create_channel("agy-topic", exist_ok=True)

    invoked: list[str] = []

    def fake_invoke(agent_name: str, prompt: str, **kwargs):
        invoked.append(agent_name)
        return SimpleNamespace(
            ok=True,
            response="[AGREE] agy first take",
            stderr_excerpt="",
            session_id="agy-session-1",
        )

    monkeypatch.setattr("agent_runtime.runner.invoke", fake_invoke)

    args = SimpleNamespace(
        channel="agy-topic",
        body="Does STRICT grounding measure model discipline fairly?",
        with_agents="agy",
        max_rounds=1,
        review=False,
    )

    assert _channels_cli._handle_discuss(args) == 0
    assert invoked == ["agy"]
