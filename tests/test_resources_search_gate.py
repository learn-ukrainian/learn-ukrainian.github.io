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


def test_resources_search_attempted_gate_skips_when_telemetry_absent_and_grounded() -> None:
    # Static re-verification of an already-built module: the writer trace was
    # never persisted (telemetry_present=False), but the resources are confirmed
    # real by citations_resolve + chunk_context_for_all_refs (grounding_verified).
    result = linear_pipeline._resources_search_attempted_gate(
        [],
        plan={"level": "folk", "sequence": 1},
        telemetry_present=False,
        grounding_verified=True,
    )

    assert result["passed"] is True
    assert result["search_attempt_count"] == 0
    assert result["manual_coverage_verified"] is False
    assert result["skipped"] == "build_telemetry_absent_resources_independently_grounded"


def test_resources_search_attempted_gate_fails_when_telemetry_absent_but_ungrounded() -> None:
    # Telemetry absent but resources NOT independently grounded -> cannot rule out
    # fabrication, so the HARD gate must still fail (no skip path).
    result = linear_pipeline._resources_search_attempted_gate(
        [],
        plan={"level": "folk", "sequence": 1},
        telemetry_present=False,
        grounding_verified=False,
    )

    assert result["passed"] is False
    assert "skipped" not in result


def test_resources_search_attempted_gate_fails_when_telemetry_present_without_search() -> None:
    # Build-time path: telemetry exists but shows no resource search. The
    # anti-fabrication contract is unchanged -> hard fail regardless of grounding.
    result = linear_pipeline._resources_search_attempted_gate(
        [{"tool": "mcp__sources__verify_words", "args": {"words": ["ранок"]}}],
        plan={"level": "folk", "sequence": 1},
        telemetry_present=True,
        grounding_verified=True,
    )

    assert result["passed"] is False
    assert "skipped" not in result
