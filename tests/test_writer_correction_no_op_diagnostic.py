from __future__ import annotations

import json
from pathlib import Path

from scripts.build import linear_pipeline


def _events(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


def test_detect_tool_theatre_returns_unmatched_citations() -> None:
    writer_output = (
        '<plan_reasoning section="intro" verification="checked">'
        "Verified lemmas with `verify_words`; heritage via `search_heritage`."
        "</plan_reasoning>"
    )

    assert linear_pipeline.detect_tool_theatre(
        writer_output,
        [{"tool": "verify_words"}],
    ) == ["search_heritage"]


def test_detect_tool_theatre_normalizes_mcp_prefix() -> None:
    writer_output = (
        '<plan_reasoning section="intro">'
        "Verified lemmas with `mcp__sources__verify_words`."
        "</plan_reasoning>"
    )

    assert linear_pipeline.detect_tool_theatre(
        writer_output,
        [{"tool": "verify_words"}],
    ) == []


def test_detect_tool_theatre_empty_input() -> None:
    assert linear_pipeline.detect_tool_theatre("", []) == []


def test_detect_tool_theatre_only_scans_plan_reasoning_blocks() -> None:
    writer_output = (
        "```markdown file=module.md\n"
        "This lesson mentions that `search_heritage` is the function name.\n"
        "```\n\n"
        '<plan_reasoning section="intro">No tool citation here.</plan_reasoning>'
    )

    assert linear_pipeline.detect_tool_theatre(writer_output, []) == []


def test_detect_tool_theatre_scans_plan_reasoning_attributes() -> None:
    writer_output = (
        '<plan_reasoning section="intro" verification="checked with `verify_words`">'
        "No citation in the body."
        "</plan_reasoning>"
    )

    assert linear_pipeline.detect_tool_theatre(writer_output, []) == ["verify_words"]


def test_detect_tool_theatre_scans_unbackticked_tool_names() -> None:
    writer_output = (
        '<plan_reasoning section="intro">'
        "Verified using search_heritage."
        "</plan_reasoning>"
    )

    assert linear_pipeline.detect_tool_theatre(writer_output, []) == [
        "search_heritage"
    ]


def test_detect_tool_theatre_ignores_plan_reasoning_inside_fences() -> None:
    writer_output = (
        "```markdown file=module.md\n"
        "<plan_reasoning section=\"example\">`search_heritage`</plan_reasoning>\n"
        "```\n"
    )

    assert linear_pipeline.detect_tool_theatre(writer_output, []) == []


def test_detect_tool_theatre_handles_multiple_blocks() -> None:
    writer_output = (
        '<plan_reasoning section="intro">`verify_words` checked.</plan_reasoning>\n'
        '<plan_reasoning section="heritage">`search_heritage` checked.</plan_reasoning>'
    )

    assert linear_pipeline.detect_tool_theatre(writer_output, []) == [
        "search_heritage",
        "verify_words",
    ]


def test_detect_tool_theatre_returns_all_citations_when_trace_empty() -> None:
    writer_output = (
        '<plan_reasoning section="intro">'
        "`verify_words`, `search_heritage`, and `query_pravopys` checked."
        "</plan_reasoning>"
    )

    assert linear_pipeline.detect_tool_theatre(writer_output, []) == [
        "query_pravopys",
        "search_heritage",
        "verify_words",
    ]


def test_writer_summary_emits_tool_theatre_event(tmp_path: Path) -> None:
    writer_output = (
        '<plan_reasoning section="intro">'
        "`verify_words` checked; `search_heritage` checked."
        "</plan_reasoning>"
    )
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        summary = linear_pipeline.emit_writer_response_telemetry(
            writer_output,
            writer="codex-tools",
            module="a1/test",
            sections=["intro"],
            tool_calls=[{"tool": "verify_words"}],
        )

    events = _events(telemetry)
    theatre_event = next(
        event for event in events if event["event"] == "writer_tool_theatre"
    )
    summary_event = next(
        event for event in events if event["event"] == "phase_writer_summary"
    )
    assert summary["tool_theatre_violations"] == ["search_heritage"]
    assert summary["tool_theatre_violation_count"] == 1
    assert theatre_event["violations"] == ["search_heritage"]
    assert theatre_event["violation_count"] == 1
    assert theatre_event["cited_count"] == 2
    assert theatre_event["called_count"] == 1
    assert summary_event["tool_theatre_violations"] == ["search_heritage"]
    assert summary_event["tool_theatre_violation_count"] == 1


def test_writer_correction_unparseable_response_emits_diagnostic(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("## Morning\n\nTest module.\n", encoding="utf-8")
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline._apply_writer_correction(
            "word_count",
            {"passed": False, "minimum": 100, "actual": 20},
            qg_report={"gates": {}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer_corrector=lambda _context: "I fixed the prose but emitted no artifacts.",
            writer="codex-tools",
            invoker=None,
        )

    events = _events(telemetry)
    assert [event["event"] for event in events] == ["writer_correction_unparseable"]
    assert events[0]["gate"] == "word_count"
    assert events[0]["response_preview"] == "I fixed the prose but emitted no artifacts."


def test_parse_writer_correction_module_only_extracts_single_block() -> None:
    """The patch-bounded correction parser accepts the contract format
    (one fenced ``markdown file=module.md`` block, no other prose)."""
    response = (
        "```markdown file=module.md\n"
        "## Morning\n\n"
        "Patched prose with the missing 50 words appended.\n"
        "```\n"
    )
    body = linear_pipeline.parse_writer_correction_module_only(response)
    assert body is not None
    assert body.startswith("## Morning")
    assert "Patched prose" in body
    assert body.endswith("\n")


def test_parse_writer_correction_module_only_accepts_short_form_label() -> None:
    """The parser also accepts ``markdown module.md`` and ``module.md``
    fence-info conventions — writers vary on this minor formatting."""
    response_short = "```markdown module.md\nbody1\n```"
    response_bare = "```module.md\nbody2\n```"
    assert linear_pipeline.parse_writer_correction_module_only(response_short) == "body1\n"
    assert linear_pipeline.parse_writer_correction_module_only(response_bare) == "body2\n"


def test_parse_writer_correction_module_only_rejects_zero_or_multi_blocks() -> None:
    """No fenced block, or multiple fenced blocks, returns None — the
    pipeline falls through to writer_correction_unparseable."""
    assert linear_pipeline.parse_writer_correction_module_only("just prose") is None
    multi = (
        "```markdown file=module.md\nfirst\n```\n\n"
        "```markdown file=module.md\nsecond\n```\n"
    )
    assert linear_pipeline.parse_writer_correction_module_only(multi) is None


def test_parse_writer_correction_module_only_rejects_empty_body() -> None:
    """A fenced block with no content is unparseable — writer is patching
    nothing, which violates the patch-bounded contract."""
    response = "```markdown file=module.md\n\n```"
    assert linear_pipeline.parse_writer_correction_module_only(response) is None


def test_parse_writer_correction_module_only_rejects_bare_markdown_fence() -> None:
    """A bare ``markdown`` fence (without module.md label) does NOT qualify.
    The gate semantics is "this is the patched module.md" — bare markdown
    might be a knowledge_packet, a draft excerpt, or unrelated content."""
    response = "```markdown\nsome unrelated markdown content\n```"
    assert linear_pipeline.parse_writer_correction_module_only(response) is None


def test_parse_writer_correction_module_only_rejects_full_4_block_response() -> None:
    """A realistic 4-block writer response that happens to contain a
    module.md fence MUST NOT parse as module-only. The contract is "the
    entire response is a single fence" — extra fences disqualify it.

    Caught upstream too: ``_apply_writer_correction`` checks
    ``all(name in response for name in WRITER_ARTIFACTS)`` before reaching
    the module-only path. But the parser itself must also reject this
    case so it can be safely called out of context.
    """
    full_response = (
        "```markdown file=module.md\n## Morning\nProse.\n```\n\n"
        "```json file=activities.yaml\n[]\n```\n\n"
        "```json file=vocabulary.yaml\n[]\n```\n\n"
        "```json file=resources.yaml\n[]\n```\n"
    )
    assert linear_pipeline.parse_writer_correction_module_only(full_response) is None


def test_parse_writer_correction_module_only_rejects_leading_prose() -> None:
    """Any prose before the fence disqualifies the response — the contract
    says "that is the entire response"."""
    response = (
        "Done. Here is the patched module:\n\n"
        "```markdown file=module.md\nbody\n```\n"
    )
    assert linear_pipeline.parse_writer_correction_module_only(response) is None


def test_parse_writer_correction_module_only_rejects_trailing_prose() -> None:
    """Any prose after the fence disqualifies the response."""
    response = (
        "```markdown file=module.md\nbody\n```\n\n"
        "Word count went from 996 → 1325.\n"
    )
    assert linear_pipeline.parse_writer_correction_module_only(response) is None


def test_writer_correction_module_only_writes_patched_module(tmp_path: Path) -> None:
    """End-to-end: a contract-shaped response patches module.md and emits
    no `writer_correction_unparseable` event."""
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(
        "## Morning\n\nOriginal prose.\n", encoding="utf-8"
    )
    telemetry = tmp_path / "events.jsonl"
    patched_response = (
        "```markdown file=module.md\n"
        "## Morning\n\n"
        "Original prose. Patched insert: добрий ранок!\n"
        "```\n"
    )

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline._apply_writer_correction(
            "word_count",
            {"passed": False, "minimum": 100, "actual": 20},
            qg_report={"gates": {}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer_corrector=lambda _context: patched_response,
            writer="codex-tools",
            invoker=None,
        )

    # No diagnostic — the contract response parsed cleanly.
    events = (
        _events(telemetry)
        if telemetry.exists() and telemetry.stat().st_size > 0
        else []
    )
    assert events == [], (
        f"Expected no events, got: {[e['event'] for e in events]}"
    )
    # module.md was patched with the new prose.
    assert (module_dir / "module.md").read_text("utf-8") == (
        "## Morning\n\nOriginal prose. Patched insert: добрий ранок!\n"
    )


def test_writer_correction_handles_tool_theatre_gate(tmp_path: Path) -> None:
    """The tool_theatre gate uses the module-only correction path."""
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(
        "## Morning\n\nOriginal prose with `search_heritage` theatre.\n",
        encoding="utf-8",
    )
    reports = [
        {
            "gates": {
                "tool_theatre": {
                    "passed": False,
                    "violations": ["search_heritage"],
                },
                "passed": False,
            }
        },
        {"gates": {"tool_theatre": {"passed": True}, "passed": True}},
    ]
    patched_response = (
        "```markdown file=module.md\n"
        "## Morning\n\n"
        "Original prose with verification not performed theatre.\n"
        "```\n"
    )

    def qg_runner() -> dict[str, object]:
        return reports.pop(0)

    def writer_corrector(
        context: linear_pipeline.CorrectionContext,
    ) -> str:
        assert context.gate == "tool_theatre"
        assert "search_heritage" in context.prompt
        return patched_response

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        tmp_path / "plan.yaml",
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    assert report["gates"]["passed"] is True
    assert (module_dir / "module.md").read_text("utf-8") == (
        "## Morning\n\nOriginal prose with verification not performed theatre.\n"
    )


def test_writer_correction_strict_json_parse_gate_still_requires_full_artifacts(
    tmp_path: Path,
) -> None:
    """The strict_json_parse gate is the ONE writer-correction gate where
    the response must include all 4 artifact blocks — single-block response
    is unparseable for that gate because the original failure mode WAS the
    parse, so all artifacts need to be re-emitted."""
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(
        "## Morning\n\nOriginal prose.\n", encoding="utf-8"
    )
    telemetry = tmp_path / "events.jsonl"
    # A response that would parse as module-only but fails the
    # strict_json_parse contract because activities/vocabulary/resources
    # are absent.
    module_only_response = (
        "```markdown file=module.md\n## Morning\n\nPatched.\n```\n"
    )

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline._apply_writer_correction(
            "strict_json_parse",
            {"passed": False, "reason": "missing artifact"},
            qg_report={"gates": {}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer_corrector=lambda _context: module_only_response,
            writer="codex-tools",
            invoker=None,
        )

    events = _events(telemetry)
    assert [event["event"] for event in events] == ["writer_correction_unparseable"]
    assert events[0]["gate"] == "strict_json_parse"
