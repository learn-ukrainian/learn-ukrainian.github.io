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


def test_resources_search_attempted_gate_skips_when_telemetry_absent_and_resources_live() -> None:
    # Static re-verification of an already-built module: the writer trace was
    # never persisted (telemetry_present=False), but EVERY resource is confirmed
    # real (resource_liveness.passed=True). The skip then applies.
    result = linear_pipeline._resources_search_attempted_gate(
        [],
        plan={"level": "folk", "sequence": 1},
        telemetry_present=False,
        resource_liveness={"passed": True, "checked": 9},
    )

    assert result["passed"] is True
    assert result["search_attempt_count"] == 0
    assert result["manual_coverage_verified"] is False
    assert result["skipped"] == "build_telemetry_absent_resources_verified_live"
    assert result["resources_verified_live"] == 9


def test_resources_search_attempted_gate_fails_when_a_resource_is_not_live() -> None:
    # Telemetry absent and liveness FAILED (a fabricated/dead resource) -> cannot
    # rule out fabrication, so the HARD gate must still fail (no skip path).
    result = linear_pipeline._resources_search_attempted_gate(
        [],
        plan={"level": "folk", "sequence": 1},
        telemetry_present=False,
        resource_liveness={"passed": False, "checked": 9},
    )

    assert result["passed"] is False
    assert "skipped" not in result


def test_resources_search_attempted_gate_fails_when_telemetry_absent_no_liveness() -> None:
    # Telemetry absent and NO liveness verification supplied (e.g. build-time
    # caller) -> no proof resources are real -> hard fail.
    result = linear_pipeline._resources_search_attempted_gate(
        [],
        plan={"level": "folk", "sequence": 1},
        telemetry_present=False,
        resource_liveness=None,
    )

    assert result["passed"] is False
    assert "skipped" not in result


def test_resources_search_attempted_gate_fails_when_telemetry_present_without_search() -> None:
    # Build-time path: telemetry exists but shows no resource search. The
    # anti-fabrication contract is unchanged -> hard fail even if resources live.
    result = linear_pipeline._resources_search_attempted_gate(
        [{"tool": "mcp__sources__verify_words", "args": {"words": ["ранок"]}}],
        plan={"level": "folk", "sequence": 1},
        telemetry_present=True,
        resource_liveness={"passed": True, "checked": 9},
    )

    assert result["passed"] is False
    assert "skipped" not in result


def test_verify_resources_live_passes_only_when_every_resource_real() -> None:
    resources = [
        {"title": "A", "role": "wiki", "url": "https://uk.wikipedia.org/wiki/Купало"},
        {"title": "B", "role": "article", "url": "https://example.org/x"},
    ]
    live = {"https://uk.wikipedia.org/wiki/Купало": True, "https://example.org/x": True}
    ok = linear_pipeline._verify_resources_live(resources, url_live_fn=lambda u: live.get(u, False))
    assert ok["passed"] is True
    assert ok["checked"] == 2

    # One dead URL fails the whole set (fail-closed).
    live["https://example.org/x"] = False
    bad = linear_pipeline._verify_resources_live(resources, url_live_fn=lambda u: live.get(u, False))
    assert bad["passed"] is False


def test_verify_resources_live_fails_closed_on_unverifiable_resource() -> None:
    # A non-textbook resource with no URL cannot be verified -> blocks the skip.
    resources = [{"title": "mystery", "role": "article"}]
    out = linear_pipeline._verify_resources_live(resources, url_live_fn=lambda u: True)
    assert out["passed"] is False

    # A textbook resource without a URL is acceptable (citations_resolve covers it).
    textbook = [{"title": "Грінченко", "role": "textbook"}]
    out2 = linear_pipeline._verify_resources_live(textbook, url_live_fn=lambda u: True)
    assert out2["passed"] is True
