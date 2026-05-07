from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.claude import ClaudeAdapter
from agent_runtime.adapters.codex import CodexAdapter
from agent_runtime.adapters.gemini import GeminiAdapter
from agent_runtime.tool_calls import summarize_tool_output


def test_claude_adapter_parses_tool_use_events() -> None:
    stdout = "\n".join([
        '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"u1","name":"mcp__sources__verify_words","input":{"words":["ранок"]}}]}}',
        '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"u1","content":"ранок: verified"}]}}',
        '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"u2","name":"mcp__sources__search_heritage","input":{"query":"Київ"}}]}}',
        '{"type":"result","subtype":"success","result":"Done.","session_id":"session-123"}',
    ])

    result = ClaudeAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.response == "Done."
    assert [call["name"] for call in result.tool_calls] == [
        "mcp__sources__verify_words",
        "mcp__sources__search_heritage",
    ]
    assert result.tool_calls[0]["arguments"] == {"words": ["ранок"]}
    assert result.tool_calls[0]["output_summary"] == "ранок: verified"


def test_claude_adapter_extracts_stream_text_without_result_event() -> None:
    stdout = "\n".join([
        '{"type":"assistant","message":{"content":[{"type":"text","text":"Привіт."}]}}',
        '{"type":"assistant","message":{"content":[{"type":"text","text":"Готово."}]}}',
    ])

    result = ClaudeAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.response == "Привіт.\nГотово."


def test_claude_stream_json_invocation_adds_verbose(tmp_path: Path) -> None:
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"cmd_prefix": ["true"]},
    )

    assert plan.cmd[plan.cmd.index("--output-format") + 1] == "stream-json"
    assert "--verbose" in plan.cmd


def test_gemini_adapter_parses_tool_calls() -> None:
    stderr = "\n".join([
        'DEBUG tool_call {"type":"tool_call","name":"mcp__sources__verify_words","arguments":{"words":["дім"]},"timestamp":"2026-05-07T10:00:00Z"}',
        'DEBUG tool_call {"type":"tool_call","name":"mcp__sources__search_heritage","arguments":{"query":"Львів"},"output":"found 2"}',
    ])

    result = GeminiAdapter().parse_response(
        stdout="Final response.",
        stderr=stderr,
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert [call["name"] for call in result.tool_calls] == [
        "mcp__sources__verify_words",
        "mcp__sources__search_heritage",
    ]
    assert result.tool_calls[1]["arguments"] == {"query": "Львів"}
    assert result.tool_calls[1]["output_summary"] == "found 2"


def test_codex_adapter_parses_tool_calls(tmp_path: Path) -> None:
    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("Final answer.", encoding="utf-8")
    stdout = "\n".join([
        "session id: 00000000-0000-0000-0000-000000000001",
        '{"type":"tool_call","name":"mcp__sources__verify_words","arguments":{"words":["мати"]},"output":"ok"}',
        '{"type":"tool_call","name":"mcp__sources__search_heritage","arguments":{"query":"Чернігів"}}',
    ])

    result = CodexAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=output_file,
    )

    assert result.ok is True
    assert result.session_id == "00000000-0000-0000-0000-000000000001"
    assert [call["name"] for call in result.tool_calls] == [
        "mcp__sources__verify_words",
        "mcp__sources__search_heritage",
    ]
    assert result.tool_calls[0]["arguments"] == {"words": ["мати"]}


def test_codex_adapter_parses_stderr_tool_calls(tmp_path: Path) -> None:
    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("Final answer.", encoding="utf-8")

    result = CodexAdapter().parse_response(
        stdout="",
        stderr='{"type":"tool_call","name":"mcp__sources__verify_words","arguments":{"words":["ніч"]},"output":"ok"}',
        returncode=0,
        output_file=output_file,
    )

    assert result.ok is True
    assert result.tool_calls[0]["name"] == "mcp__sources__verify_words"
    assert result.tool_calls[0]["arguments"] == {"words": ["ніч"]}


def test_tool_call_output_summary_truncation() -> None:
    summary = summarize_tool_output("x" * 10_000)

    assert len(summary) == 500
    assert summary.endswith("[...truncated]")


def test_unparseable_tool_event_emits_warning_not_crash(caplog) -> None:
    caplog.set_level(logging.WARNING, logger="agent_runtime.adapters.gemini")

    result = GeminiAdapter().parse_response(
        stdout="Final response.",
        stderr="DEBUG tool_call {not-json",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.tool_calls == []
    assert "tool-call trace line" in caplog.text
