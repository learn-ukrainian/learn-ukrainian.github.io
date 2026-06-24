from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.agent_runtime import tool_config as tool_config_mod
from scripts.build import linear_pipeline


def _seed_sources_mcp_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mcp_config_path = tmp_path / ".mcp.json"
    mcp_config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "sources": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:8766/mcp",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    tool_config_mod._load_mcp_config.cache_clear()
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", mcp_config_path)


def _iterative_plan() -> dict[str, Any]:
    return {
        "level": "b1",
        "module": 1,
        "slug": "iterative-tools-gate",
        "title": "Iterative tools gate",
        "content_outline": [
            {"section": "Intro", "words": 1, "points": ["Open the module."]},
            {"section": "Discussion", "words": 1, "points": ["Synthesize the module."]},
        ],
    }


def _section_artifact_response(section_id: str, title: str) -> str:
    payload = {
        "section_id": section_id,
        "markdown": f"## {title}\n\nGrounded sentence for {title}.",
        "citations_used": [],
        "primary_readings_used": [],
        "vocab_candidates": [],
        "activity_refs": [],
        "self_check": {},
    }
    return "```section_artifact.json\n" + json.dumps(payload) + "\n```"


def _patch_invoke_writer_with_tool_totals(
    monkeypatch: pytest.MonkeyPatch,
    tool_totals: list[int],
) -> list[str]:
    original_invoke_writer = linear_pipeline.invoke_writer
    section_calls: list[str] = []

    def fake_invoke_writer(prompt: str, writer: str, **kwargs: Any) -> str:
        section_title = kwargs["sections"][0]
        section_index = len(section_calls)
        section_calls.append(section_title)
        tool_calls_total = tool_totals[section_index]
        tool_calls = [
            {
                "tool": "mcp__sources__search_text",
                "args": {"query": section_title},
                "result": {"matches": []},
            }
            for _ in range(tool_calls_total)
        ]

        def fake_runtime_invoker(_agent: str, _prompt: str, **_runtime_kwargs: Any) -> SimpleNamespace:
            return SimpleNamespace(
                response=_section_artifact_response(f"s{section_index + 1}", section_title),
                tool_calls=tool_calls,
                tool_calls_total=tool_calls_total,
            )

        return original_invoke_writer(
            prompt,
            writer,
            invoker=fake_runtime_invoker,
            **kwargs,
        )

    monkeypatch.setattr(linear_pipeline, "invoke_writer", fake_invoke_writer)
    return section_calls


def test_iterative_tools_writer_runtime_gate_aggregates_module_tool_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    section_calls = _patch_invoke_writer_with_tool_totals(monkeypatch, [2, 0])

    result = linear_pipeline.run_iterative_writer(
        _iterative_plan(),
        knowledge_packet="",
        readings=[],
        writer="gemini-tools",
        cwd=tmp_path,
        module="folk/iterative-tools-gate",
    )

    assert section_calls == ["Intro", "Discussion"]
    assert "## Intro" in result["module_md"]
    assert "## Discussion" in result["module_md"]


def test_iterative_tools_writer_runtime_gate_fails_when_module_has_zero_tool_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_sources_mcp_config(tmp_path, monkeypatch)
    section_calls = _patch_invoke_writer_with_tool_totals(monkeypatch, [0, 0])
    events: list[dict[str, Any]] = []

    with pytest.raises(linear_pipeline.LinearPipelineError, match="mcp_tools_never_invoked"):
        linear_pipeline.run_iterative_writer(
            _iterative_plan(),
            knowledge_packet="",
            readings=[],
            writer="gemini-tools",
            cwd=tmp_path,
            module="folk/iterative-tools-gate",
            event_sink=lambda event, **fields: events.append({"event": event, **fields}),
        )

    assert section_calls == ["Intro", "Discussion"]
    assert any(
        event["event"] == "writer_failure_class"
        and event["failure_class"] == "mcp_tools_never_invoked"
        and event["gate"] == "tools_writer_runtime_gate"
        for event in events
    )
