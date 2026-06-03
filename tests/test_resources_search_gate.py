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
    assert result["manual_coverage_verified"] is False


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
    assert result["manual_coverage_verified"] is False


def test_resources_search_attempted_gate_accepts_a1_zero_script_manual_coverage() -> None:
    result = linear_pipeline._resources_search_attempted_gate(
        [],
        plan={"level": "A1", "sequence": 1},
        resource_coverage={"passed": True},
    )

    assert result["passed"] is True
    assert result["search_attempt_count"] == 0
    assert result["manual_coverage_verified"] is True


def test_resources_search_attempted_gate_accepts_a1_m1_m7_manual_coverage() -> None:
    result = linear_pipeline._resources_search_attempted_gate(
        [],
        plan={"level": "A1", "sequence": 5},
        resource_coverage={"passed": True},
    )

    assert result["passed"] is True
    assert result["manual_coverage_verified"] is True


def test_resources_search_attempted_gate_keeps_non_a1_manual_coverage_strict() -> None:
    result = linear_pipeline._resources_search_attempted_gate(
        [],
        plan={"level": "A1", "sequence": 8},
        resource_coverage={"passed": True},
    )

    assert result["passed"] is False
    assert result["manual_coverage_verified"] is False
