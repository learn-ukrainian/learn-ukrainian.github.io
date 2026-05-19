from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.adapters.hermes_deepseek import HermesDeepSeekAdapter
from agent_runtime.errors import AgentTimeoutError, AgentUnavailableError
from agent_runtime.runner import invoke
from agent_runtime.usage import _reset_rate_limit_cache_for_tests


@pytest.fixture(autouse=True)
def _isolate_runtime(tmp_path):
    _reset_rate_limit_cache_for_tests()
    with patch("agent_runtime.usage._usage_dir", return_value=tmp_path / "api_usage"):
        yield
    _reset_rate_limit_cache_for_tests()


def _build(prompt: str, tmp_path: Path, model: str = "deepseek-v4-pro"):
    return HermesDeepSeekAdapter().build_invocation(
        prompt=prompt,
        mode="workspace-write",
        cwd=tmp_path,
        model=model,
        task_id=None,
        session_id=None,
        tool_config={"hermes_mcp_servers": ["sources"]},
        effort="medium",
    )


def test_deepseek_adapter_invokes_hermes_z_with_correct_argv_pro(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_runtime.adapters.hermes_deepseek.shutil.which", lambda _: "hermes")

    plan = _build("Write the module.", tmp_path, model="deepseek-v4-pro")

    assert plan.cmd == ["hermes", "-z", "Write the module.", "-m", "deepseek-v4-pro"]
    assert plan.cwd == tmp_path
    assert plan.stdin_payload == ""


def test_deepseek_adapter_invokes_hermes_z_with_correct_argv_flash(tmp_path, monkeypatch):
    """Flash variant uses the same shape, different ``-m``."""
    monkeypatch.setattr("agent_runtime.adapters.hermes_deepseek.shutil.which", lambda _: "hermes")

    plan = _build("Review this code.", tmp_path, model="deepseek-v4-flash")

    assert plan.cmd == ["hermes", "-z", "Review this code.", "-m", "deepseek-v4-flash"]


def test_deepseek_adapter_translates_mcp_prefix_for_hermes(tmp_path, monkeypatch):
    """Hermes registers MCP tools with single-underscore (`mcp_sources_*`)
    while the canonical writer prompt documents double-underscore
    (`mcp__sources__*`). The adapter must translate so the model emits
    names Hermes can actually dispatch. 2026-05-19 B1-bakeoff finding —
    without this translation, deepseek-pro wrote verification_trace
    blocks but never invoked any MCP tool.
    """
    monkeypatch.setattr("agent_runtime.adapters.hermes_deepseek.shutil.which", lambda _: "hermes")

    prompt_with_mcp = (
        "Verify each Ukrainian word via `mcp__sources__verify_words` and "
        "look up etymology via `mcp__sources__search_esum`."
    )
    plan = _build(prompt_with_mcp, tmp_path, model="deepseek-v4-pro")

    sent_prompt = plan.cmd[2]  # ["hermes", "-z", PROMPT, "-m", MODEL]
    assert "mcp__sources__" not in sent_prompt, (
        "double-underscore MCP names should be rewritten before Hermes invocation"
    )
    assert "mcp_sources_verify_words" in sent_prompt
    assert "mcp_sources_search_esum" in sent_prompt


def test_deepseek_adapter_leaves_non_mcp_prompts_unchanged(tmp_path, monkeypatch):
    """The translation must be scoped to ``mcp__sources__`` exactly — no
    accidental matches on similar substrings like ``mcp__rag__`` (legacy
    naming, archived) or random underscore-heavy text."""
    monkeypatch.setattr("agent_runtime.adapters.hermes_deepseek.shutil.which", lambda _: "hermes")

    prompt = "Module b1-052: write content. Use `mcp__rag__legacy_tool` only if it appears."
    plan = _build(prompt, tmp_path, model="deepseek-v4-pro")

    assert plan.cmd[2] == prompt


def test_deepseek_adapter_default_model_is_pro(tmp_path, monkeypatch):
    """When model=None, the adapter falls back to deepseek-v4-pro (primary)."""
    monkeypatch.setattr("agent_runtime.adapters.hermes_deepseek.shutil.which", lambda _: "hermes")
    adapter = HermesDeepSeekAdapter()

    plan = adapter.build_invocation(
        prompt="hi",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
        effort=None,
    )

    assert plan.cmd[-1] == "deepseek-v4-pro"


def test_deepseek_adapter_returns_stdout_as_response():
    result = HermesDeepSeekAdapter().parse_response(
        stdout="hello from deepseek",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.response == "hello from deepseek"


def test_deepseek_adapter_tool_calls_total_is_none_not_zero():
    """Hermes ``-z`` exposes no tool-call trace — distinguish unknown from zero."""
    result = HermesDeepSeekAdapter().parse_response(
        stdout="hello",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.tool_calls == []
    assert result.tool_calls_total is None


def test_deepseek_adapter_handles_missing_hermes_binary(tmp_path):
    with (
        patch("agent_runtime.runner.has_headroom", return_value=(True, "")),
        patch("agent_runtime.runner.write_record"),
        patch(
            "agent_runtime.runner.subprocess.Popen",
            side_effect=FileNotFoundError("hermes"),
        ),
        pytest.raises(AgentUnavailableError, match="Popen failed: FileNotFoundError"),
    ):
        invoke(
            "deepseek",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            model="deepseek-v4-pro",
            entrypoint="dispatch",
            effort="medium",
        )


def test_deepseek_adapter_honors_timeout(tmp_path, monkeypatch):
    adapter = HermesDeepSeekAdapter()

    def fake_build_invocation(**kwargs):
        return InvocationPlan(cmd=["/bin/sh", "-c", "sleep 5"], cwd=Path(kwargs["cwd"]))

    monkeypatch.setattr(adapter, "build_invocation", fake_build_invocation)
    monkeypatch.setattr("agent_runtime.runner._load_adapter", lambda _name: adapter)

    with (
        patch("agent_runtime.runner.has_headroom", return_value=(True, "")),
        patch("agent_runtime.runner.write_record"),
        pytest.raises(AgentTimeoutError),
    ):
        invoke(
            "deepseek",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            model="deepseek-v4-pro",
            entrypoint="dispatch",
            hard_timeout=1,
        )


def test_deepseek_adapter_strips_ansi_codes_from_stdout():
    result = HermesDeepSeekAdapter().parse_response(
        stdout="\x1b[32mhello\x1b[0m",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.response == "hello"


def test_deepseek_adapter_detects_rate_limit():
    """Rate-limit pattern (HTTP 429 / "rate limit") is surfaced on returncode != 0."""
    result = HermesDeepSeekAdapter().parse_response(
        stdout="",
        stderr="HTTP 429 rate limit exceeded",
        returncode=1,
        output_file=None,
    )

    assert result.rate_limited is True
    assert result.ok is False


def test_runner_preserves_unknown_deepseek_tool_call_total(tmp_path, monkeypatch):
    """Runner round-trip preserves the unknown-vs-zero distinction."""
    adapter = HermesDeepSeekAdapter()

    def fake_build_invocation(**kwargs):
        return InvocationPlan(cmd=["/bin/sh", "-c", "printf hello"], cwd=Path(kwargs["cwd"]))

    monkeypatch.setattr(adapter, "build_invocation", fake_build_invocation)
    monkeypatch.setattr("agent_runtime.runner._load_adapter", lambda _name: adapter)

    with (
        patch("agent_runtime.runner.has_headroom", return_value=(True, "")),
        patch("agent_runtime.runner.write_record"),
    ):
        result = invoke(
            "deepseek",
            "hello",
            mode="workspace-write",
            cwd=tmp_path,
            model="deepseek-v4-pro",
            entrypoint="dispatch",
            effort="medium",
        )

    assert result.response == "hello"
    assert result.tool_calls == []
    assert result.tool_calls_total is None


def test_registry_lists_deepseek_with_hermes_adapter():
    """Sanity check: registry entry is wired to the new adapter class."""
    from agent_runtime.registry import get_agent_entry

    entry = get_agent_entry("deepseek")
    assert entry["cli_available"] is True
    assert entry["default_model"] == "deepseek-v4-pro"
    assert entry["adapter"].endswith(":HermesDeepSeekAdapter")
    assert entry["resume_policy"] == "never"
