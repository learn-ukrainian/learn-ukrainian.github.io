from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.gemini import GeminiAdapter
from scripts.build import linear_pipeline


def _plan(cwd: Path, prompt: str = "Call the sources tool.") -> InvocationPlan:
    return InvocationPlan(
        cmd=["gemini"],
        cwd=cwd,
        stdin_payload=prompt,
        output_file=None,
        env_overrides={},
        env_unsets=(),
        liveness_paths=(),
    )


def _write_jsonl_session(
    home: Path,
    cwd: Path,
    *,
    prompt: str = "Call the sources tool.",
    gemini_events: list[dict[str, Any]],
) -> Path:
    chats_dir = home / ".gemini" / "tmp" / cwd.name / "chats"
    chats_dir.mkdir(parents=True)
    session = chats_dir / "session-2026-05-09T19-20-fixture.jsonl"
    events = [
        {"sessionId": "fixture", "startTime": "2026-05-09T19:20:00Z"},
        {"type": "user", "content": [{"text": prompt}]},
        *gemini_events,
    ]
    session.write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
        encoding="utf-8",
    )
    return session


def _parse_from_session(home: Path, monkeypatch: pytest.MonkeyPatch, cwd: Path):
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda _: home))
    return GeminiAdapter().parse_response(
        stdout="writer output",
        stderr="",
        returncode=0,
        output_file=None,
        plan=_plan(cwd),
    )


def test_parse_response_extracts_mcp_tool_calls_from_gemini_jsonl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    _write_jsonl_session(
        home,
        cwd,
        gemini_events=[
            {
                "type": "gemini",
                "toolCalls": [
                    {
                        "id": "mcp__sources__verify_words_fixture",
                        "name": "mcp__sources__verify_words",
                        "args": {"words": ["кіт", "добре"]},
                        "status": "success",
                        "timestamp": "2026-05-09T19:20:01Z",
                    }
                ],
            }
        ],
    )

    result = _parse_from_session(home, monkeypatch, cwd)

    assert result.tool_calls == [
        {
            "name": "mcp__sources__verify_words",
            "arguments": {"words": ["кіт", "добре"]},
            "output_summary": "",
            "timestamp": "2026-05-09T19:20:01Z",
        }
    ]


def test_parse_response_keeps_empty_gemini_jsonl_tool_calls_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    _write_jsonl_session(
        home,
        cwd,
        gemini_events=[{"type": "gemini", "content": "No tools used."}],
    )

    result = _parse_from_session(home, monkeypatch, cwd)

    assert result.tool_calls == []


def test_parse_response_extracts_built_in_and_mcp_tool_calls_from_gemini_jsonl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    _write_jsonl_session(
        home,
        cwd,
        gemini_events=[
            {
                "type": "gemini",
                "toolCalls": [
                    {"name": "list_directory", "args": {"dir_path": "."}},
                    {"name": "read_file", "args": {"absolute_path": "README.md"}},
                    {
                        "name": "mcp__sources__verify_words",
                        "args": {"words": ["кіт"]},
                    },
                ],
            }
        ],
    )

    result = _parse_from_session(home, monkeypatch, cwd)

    assert [call["name"] for call in result.tool_calls] == [
        "list_directory",
        "read_file",
        "mcp__sources__verify_words",
    ]
    assert result.tool_calls[2]["arguments"] == {"words": ["кіт"]}


def test_invoke_writer_persists_gemini_jsonl_mcp_calls_to_writer_tool_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    cwd = tmp_path / "project"
    _write_jsonl_session(
        home,
        cwd,
        gemini_events=[
            {
                "type": "gemini",
                "toolCalls": [
                    {
                        "name": "mcp__sources__verify_words",
                        "args": {"words": ["кіт"]},
                    }
                ],
            }
        ],
    )
    parsed = _parse_from_session(home, monkeypatch, cwd)
    trace_path = tmp_path / "module" / "writer_tool_calls.json"

    def invoker(_agent: str, _prompt: str, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            response="writer output",
            tool_calls=parsed.tool_calls,
        )

    linear_pipeline.invoke_writer(
        "Write the module.",
        writer="gemini-tools",
        cwd=cwd,
        invoker=invoker,
        module="a1/1",
        sections=["vocabulary"],
        tool_trace_path=trace_path,
    )

    calls = json.loads(trace_path.read_text(encoding="utf-8"))
    assert [call["name"] for call in calls] == ["mcp__sources__verify_words"]
    assert calls[0]["arguments"] == {"words": ["кіт"]}

