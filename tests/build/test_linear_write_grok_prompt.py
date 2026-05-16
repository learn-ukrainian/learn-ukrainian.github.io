import re

from scripts.build import linear_pipeline

PHASES_DIR = linear_pipeline.PROJECT_ROOT / "scripts" / "build" / "phases"


def test_linear_write_grok_prompt_exists_and_is_non_empty() -> None:
    prompt_path = PHASES_DIR / "linear-write-grok.md"

    assert prompt_path.exists()
    assert prompt_path.read_text(encoding="utf-8").strip()


def test_linear_write_grok_prompt_uses_plan_thinking_not_section_reasoning() -> None:
    prompt_text = (PHASES_DIR / "linear-write-grok.md").read_text(encoding="utf-8")

    assert "<plan_thinking>" in prompt_text
    assert not re.search(r"<plan_reasoning\s+section=", prompt_text)


def test_linear_write_grok_prompt_is_no_longer_than_default_prompt() -> None:
    grok_words = (PHASES_DIR / "linear-write-grok.md").read_text(encoding="utf-8").split()
    default_words = (PHASES_DIR / "linear-write.md").read_text(encoding="utf-8").split()

    assert len(grok_words) <= len(default_words)


def test_prompt_by_writer_routes_grok_and_defaults_to_linear_write() -> None:
    assert linear_pipeline.PROMPT_BY_WRITER["grok-tools"] == "linear-write-grok.md"
    assert linear_pipeline.writer_prompt_path("grok-tools").name == "linear-write-grok.md"
    assert linear_pipeline.writer_prompt_path("claude-tools").name == "linear-write.md"
    assert linear_pipeline.writer_prompt_path("unknown-tools").name == "linear-write.md"
    assert (
        linear_pipeline.writer_correction_prompt_path("grok-tools").name
        == "linear-writer-correction-grok.md"
    )


def test_linear_write_grok_prompt_keeps_all_artifact_fences() -> None:
    prompt_text = (PHASES_DIR / "linear-write-grok.md").read_text(encoding="utf-8")

    for artifact in linear_pipeline.WRITER_ARTIFACTS:
        assert f"file={artifact}" in prompt_text


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
