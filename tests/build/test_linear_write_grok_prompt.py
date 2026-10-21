
from scripts.build import linear_pipeline


def test_plan_thinking_sections_count_as_writer_cot_coverage() -> None:
    output = """<plan_thinking>
<sections>
Діалоги: vocab=[прокидатися]; refs=Захарійчук G1 p.52; budget=300w.
Дієслова на -ся: vocab=[вмиватися]; refs=Караман G10 p.176; budget=300w.
Мій ранок: vocab=[снідати]; refs=packet; budget=300w.
Підсумок: vocab=[повторити]; refs=packet; budget=300w.
</sections>
<verification_trace>verification not performed</verification_trace>
</plan_thinking>
<end_gate><removed_unverified></removed_unverified></end_gate>"""

    summary = linear_pipeline.emit_writer_response_telemetry(
        output,
        writer="grok-tools",
        module="a1/20",
        sections=["Діалоги", "Дієслова на -ся", "Мій ранок", "Підсумок"],
        tool_calls=[],
        event_sink=lambda *_args, **_kwargs: None,
    )

    assert summary["sections_total"] == 4
    assert summary["sections_with_cot"] == 4


def test_plan_thinking_tool_citations_feed_tool_theatre_gate() -> None:
    output = """<plan_thinking>
<sections>
Діалоги: vocab=[прокидатися]; refs=packet; budget=300w.
</sections>
<verification_trace>mcp__sources__verify_words(["прокидатися"]) -> all-OK.</verification_trace>
</plan_thinking>"""

    assert linear_pipeline.detect_tool_theatre(
        output,
        [{"tool": "verify_words", "args": {"words": ["прокидатися"]}}],
    ) == []
    assert linear_pipeline.detect_tool_theatre(output, []) == ["verify_words"]
