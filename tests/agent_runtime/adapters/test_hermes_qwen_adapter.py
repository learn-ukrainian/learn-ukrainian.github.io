"""Tests for HermesQwenAdapter.

Anti-regression coverage for the 2026-05-19 Hermes provider-routing-drift fix:
``moonshotai/*`` and ``minimax/*`` model prefixes default to an internal
``nvidia`` provider mapping at per-invocation ``-m`` routing despite the
top-level ``model.provider: openrouter`` in ``~/.hermes/config.yaml``. The
adapter must pass ``--provider openrouter`` explicitly so the documented
behavior is enforced. See ``scripts/agent_runtime/adapters/hermes_qwen.py``
for the bug rationale.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from agent_runtime.adapters.hermes_qwen import HermesQwenAdapter
from agent_runtime.usage import _reset_rate_limit_cache_for_tests


@pytest.fixture(autouse=True)
def _isolate_runtime(tmp_path):
    _reset_rate_limit_cache_for_tests()
    with patch("agent_runtime.usage._usage_dir", return_value=tmp_path / "api_usage"):
        yield
    _reset_rate_limit_cache_for_tests()


def _build(prompt: str, tmp_path: Path, model: str | None = None):
    return HermesQwenAdapter().build_invocation(
        prompt=prompt,
        mode="workspace-write",
        cwd=tmp_path,
        model=model,
        task_id=None,
        session_id=None,
        tool_config={"hermes_mcp_servers": ["sources"]},
        effort="medium",
    )


def test_qwen_adapter_invokes_hermes_z_with_correct_argv(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agent_runtime.adapters.hermes_qwen.shutil.which", lambda _: "hermes"
    )

    plan = _build("Write the module.", tmp_path, model="qwen/qwen3.6-plus")

    assert plan.cmd == [
        "hermes",
        "-z", "Write the module.",
        "-m", "qwen/qwen3.6-plus",
        "--provider", "openrouter",
    ]
    assert plan.cwd == tmp_path
    assert plan.stdin_payload == ""


def test_qwen_adapter_forces_openrouter_provider_for_routing_drift_fix(
    tmp_path, monkeypatch
):
    """Regression guard for the 2026-05-19 ``moonshotai/*`` / ``minimax/*``
    routing-drift bug. Without ``--provider openrouter`` Hermes raises
    ``RuntimeError: Provider 'nvidia' is set in config.yaml but no API key
    was found`` despite the top-level config saying openrouter. The flag MUST
    appear in cmd for every model this adapter routes."""
    monkeypatch.setattr(
        "agent_runtime.adapters.hermes_qwen.shutil.which", lambda _: "hermes"
    )

    for model in (
        "moonshotai/kimi-k2.5",
        "moonshotai/kimi-k2.6",
        "minimax/minimax-m2.7",
        "qwen/qwen3.6-plus",
        "qwen/qwen3.6-max-preview",
        "deepseek/deepseek-v4-pro",
    ):
        plan = _build("hi", tmp_path, model=model)
        assert "--provider" in plan.cmd, f"--provider missing for {model}"
        provider_idx = plan.cmd.index("--provider")
        assert plan.cmd[provider_idx + 1] == "openrouter", (
            f"--provider value for {model} is "
            f"{plan.cmd[provider_idx + 1]!r}, expected 'openrouter'"
        )


def test_qwen_adapter_uses_default_model_when_none_passed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agent_runtime.adapters.hermes_qwen.shutil.which", lambda _: "hermes"
    )

    plan = _build("hi", tmp_path, model=None)

    # default_model declared on the adapter class
    assert "-m" in plan.cmd
    m_idx = plan.cmd.index("-m")
    assert plan.cmd[m_idx + 1] == HermesQwenAdapter.default_model
