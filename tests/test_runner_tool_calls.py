from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.adapters.claude import ClaudeAdapter
from agent_runtime.adapters.codex import CodexAdapter
from agent_runtime.adapters.gemini import GeminiAdapter
from agent_runtime.tool_calls import summarize_tool_output
from tests.helpers.codex_exec_stream import THREAD_ID, command, completed_stream, mcp_call


def test_claude_adapter_parses_tool_use_events() -> None:
    stdout = "\n".join(
        [
            '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"u1","name":"mcp__sources__verify_words","input":{"words":["ранок"]}}]}}',
            '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"u1","content":"ранок: verified"}]}}',
            '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"u2","name":"mcp__sources__search_heritage","input":{"query":"Київ"}}]}}',
            '{"type":"result","subtype":"success","result":"Done.","session_id":"session-123"}',
        ]
    )

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
    assert result.tool_calls[0]["paired"] is True and result.tool_calls[0]["is_error"] is False
    assert "is_error" not in result.tool_calls[1]


def test_claude_adapter_extracts_stream_text_without_result_event() -> None:
    stdout = "\n".join(
        [
            '{"type":"assistant","message":{"content":[{"type":"text","text":"Привіт."}]}}',
            '{"type":"assistant","message":{"content":[{"type":"text","text":"Готово."}]}}',
        ]
    )

    result = ClaudeAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is True
    assert result.response == "Привіт.\nГотово."


def test_claude_stream_json_without_text_fails_loudly() -> None:
    stdout = '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"u1","name":"mcp__sources__verify_words","input":{"words":["ранок"]}}]}}'

    result = ClaudeAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.ok is False
    assert result.response == ""
    assert result.tool_calls[0]["name"] == "mcp__sources__verify_words"


def test_claude_adapter_recovers_tool_calls_from_session_jsonl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    cwd = tmp_path / "work"
    cwd.mkdir()
    session_id = "abc-123"
    slug = str(cwd.resolve()).replace("/", "-")
    session_dir = tmp_path / ".claude" / "projects" / slug
    session_dir.mkdir(parents=True)
    session_file = session_dir / f"{session_id}.jsonl"
    session_file.write_text(
        "\n".join(
            [
                (
                    '{"type":"assistant","message":{"content":['
                    '{"type":"tool_use","id":"u1","name":"mcp__sources__verify_word",'
                    '"input":{"word":"тест"}}]}}'
                ),
                ('{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"u1","content":"ok"}]}}'),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    stdout = '{"type":"result","subtype":"success","result":"Done.","session_id":"abc-123"}'
    plan = InvocationPlan(
        cmd=["claude"],
        cwd=cwd,
        stdin_payload="",
        output_file=None,
        env_overrides={},
    )
    result = ClaudeAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )
    assert result.ok is True
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["name"] == "mcp__sources__verify_word"
    assert result.tool_calls[0]["output_summary"] == "ok"


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
    stderr = "\n".join(
        [
            'DEBUG tool_call {"type":"tool_call","name":"mcp__sources__verify_words","arguments":{"words":["дім"]},"timestamp":"2026-05-07T10:00:00Z"}',
            'DEBUG tool_call {"type":"tool_call","name":"mcp__sources__search_heritage","arguments":{"query":"Львів"},"output":"found 2"}',
        ]
    )

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


def test_gemini_adapter_parses_session_file_tool_calls(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = tmp_path / "home"
    chats = home / ".gemini" / "tmp" / tmp_path.name / "chats"
    chats.mkdir(parents=True)
    (chats / "session-test.json").write_text(
        "\n".join(
            [
                "{",
                '  "messages": [',
                '    {"type":"user","content":[{"text":"Write the module."}]},',
                '    {"type":"tool_call","name":"mcp__sources__verify_words","arguments":{"words":["ранок"]},"output":"verified"},',
                '    {"type":"gemini","content":"Final response."}',
                "  ]",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: home)

    result = GeminiAdapter().parse_response(
        stdout="Final response.",
        stderr="",
        returncode=0,
        output_file=None,
        plan=InvocationPlan(cmd=["gemini"], cwd=tmp_path, stdin_payload="Write the module."),
    )

    assert result.ok is True
    assert result.tool_calls[0]["name"] == "mcp__sources__verify_words"
    assert result.tool_calls[0]["arguments"] == {"words": ["ранок"]}


def test_codex_adapter_ignores_untyped_stdout_tool_calls(tmp_path: Path) -> None:
    """#9532: only typed exec items are tool calls; other JSON objects are not."""
    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("Final answer.", encoding="utf-8")
    stdout = completed_stream(
        {"type": "tool_call", "name": "mcp__sources__verify_words", "arguments": {"words": ["мати"]}, "output": "ok"},
        command("cat trace.jsonl", '{"type":"tool_call","name":"mcp__sources__search_heritage"}'),
    )

    result = CodexAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=output_file,
    )

    assert result.ok is True
    assert result.session_id == THREAD_ID
    assert [call["name"] for call in result.tool_calls] == ["exec_command"]


def test_codex_adapter_ignores_stderr_tool_calls(tmp_path: Path) -> None:
    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("Final answer.", encoding="utf-8")

    result = CodexAdapter().parse_response(
        stdout=completed_stream(),
        stderr='{"type":"tool_call","name":"mcp__sources__verify_words","arguments":{"words":["ніч"]},"output":"ok"}',
        returncode=0,
        output_file=output_file,
    )

    assert result.ok is True
    assert result.tool_calls == []


def test_codex_adapter_maps_typed_mcp_items_to_tool_calls(tmp_path: Path) -> None:
    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("Final answer.", encoding="utf-8")

    result = CodexAdapter().parse_response(
        stdout=completed_stream(
            mcp_call("sources", "verify_words", {"words": ["день"]}, text="день: verified", item_id="item_1"),
            mcp_call("sources", "search_text", {"query": "ступені"}, text="Found 1 result", item_id="item_2"),
            mcp_call("sources", "verify_word", {"word": "ніч"}, error="server unavailable", item_id="item_3"),
        ),
        stderr="",
        returncode=0,
        output_file=output_file,
    )

    assert result.ok is True
    verify, search, failed = result.tool_calls
    assert verify["name"] == "mcp__sources__verify_words"
    assert verify["arguments"] == {"words": ["день"]}
    assert search["name"] == "mcp__sources__search_text"
    assert search["result"] == [{"type": "text", "text": "Found 1 result"}]
    assert search["paired"] is True and search["is_error"] is False
    assert failed["is_error"] is True
    assert search["output_summary"] == '[{"text": "Found 1 result", "type": "text"}]'
    assert failed["status"] == "failed" and failed["output_summary"] == "server unavailable"


def test_tool_call_output_summary_truncation() -> None:
    summary = summarize_tool_output("x" * 10_000)

    assert len(summary) == 500
    assert summary.endswith("[...truncated]")


def test_tool_call_arguments_are_bounded(tmp_path: Path) -> None:
    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("Final answer.", encoding="utf-8")

    result = CodexAdapter().parse_response(
        stdout=completed_stream(mcp_call("sources", "write", {"file_path": "lesson.md", "content": "x" * 10_000})),
        stderr="",
        returncode=0,
        output_file=output_file,
    )

    assert result.ok is True
    assert len(result.tool_calls[0]["arguments"]["content"]) == 500
    assert result.tool_calls[0]["arguments"]["content"].endswith("[...truncated]")


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


@pytest.mark.parametrize("status,is_error,item_error", [("completed", False, None), ("completed", True, None),
    ("failed", False, None), ("in_progress", False, None), ("completed", False, {"message": "synthetic error"})])
def test_codex_structured_result_and_all_error_channels(status, is_error, item_error):
    from agent_runtime.adapters.codex_events import tool_calls_from_items
    envelope = {"schema": "sources.tool-result.v1", "tool": "verify_words", "status": "ok"}
    calls = tool_calls_from_items([{"type": "mcp_tool_call", "server": "sources", "tool": "verify_words",
        "status": status, "arguments": {}, "error": item_error,
        "result": {"isError": is_error, "content": [], "structured_content": envelope}}])
    assert calls[0]["result"] == (item_error["message"] if item_error else envelope)
    assert calls[0]["mcp_result"]["structured_content"] == envelope
    assert calls[0]["paired"] is True
    assert calls[0]["is_error"] is (status != "completed" or is_error or bool(item_error))


@pytest.mark.parametrize("recovery", [False, True])
def test_claude_stream_and_session_recovery_preserve_errors(tmp_path, monkeypatch, recovery):
    import json

    import agent_runtime.adapters.claude as claude_module
    events = [
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "u1",
            "name": "mcp__sources__verify_words", "input": {"words": ["synthetic"]}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "u1",
            "is_error": True, "content": "synthetic failure"}]}},
        {"type": "result", "subtype": "success", "result": "Done", "session_id": "synthetic-session"},
    ]
    if recovery:
        session = tmp_path / "session.jsonl"
        session.write_text("\n".join(json.dumps(event) for event in events))
        monkeypatch.setattr(claude_module, "_claude_session_jsonl_path", lambda *args, **kwargs: session)
        stdout = json.dumps(events[-1])
    else:
        stdout = "\n".join(json.dumps(event) for event in events)
    plan = InvocationPlan(cmd=["claude"], cwd=tmp_path, stdin_payload="", output_file=None, env_overrides={})
    result = ClaudeAdapter().parse_response(stdout=stdout, stderr="", returncode=0, output_file=None, plan=plan)
    assert result.tool_calls[0]["paired"] is True and result.tool_calls[0]["is_error"] is True
