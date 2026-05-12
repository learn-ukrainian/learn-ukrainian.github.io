from __future__ import annotations

from scripts.build import linear_pipeline


def test_resources_search_attempted_gate_rejects_missing_search() -> None:
    result = linear_pipeline._resources_search_attempted_gate(
        [
            {"tool": "mcp__sources__verify_words", "args": {"words": ["ранок"]}},
            {"name": "mcp__sources__search_text", "arguments": {"query": "Караман"}},
        ]
    )

    assert result["passed"] is False
    assert result["severity"] == "HARD"
    assert result["search_attempt_count"] == 0
    assert result["search_tools_used"] == []


def test_resources_search_attempted_gate_accepts_multimedia_search() -> None:
    result = linear_pipeline._resources_search_attempted_gate(
        [
            {
                "tool_name": "mcp__sources__search_external",
                "args": {"query": "ранкова рутина українська мова відео"},
            }
        ]
    )

    assert result["passed"] is True
    assert result["search_attempt_count"] == 1
    assert result["search_tools_used"] == ["search_external"]
