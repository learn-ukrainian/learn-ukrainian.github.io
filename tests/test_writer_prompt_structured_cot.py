from __future__ import annotations

import re

from scripts.build import linear_pipeline

WRITER_TEMPLATE = (
    linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
)

PLAN_REASONING_NODES = (
    "<word_budget>",
    "<plan_vocab>",
    "<register>",
    "<teaching_sequence>",
    "<verification_plan>",
    "<verification_trace>",
)

END_GATE_NODES = (
    "<rescanned_words>",
    "<rescanned_sources>",
    "<grammar_claims_grounded>",
    "<removed_unverified>",
)


def _writer_template() -> str:
    return WRITER_TEMPLATE.read_text(encoding="utf-8")


def test_writer_prompt_locks_structured_plan_reasoning_nodes() -> None:
    prompt = _writer_template()

    assert "Emit one `<plan_reasoning section=\"...\">` block per section" in prompt
    assert "with these sub-nodes:" in prompt
    for node in PLAN_REASONING_NODES:
        assert node in prompt


def test_writer_prompt_locks_grammar_claim_grounding_rule() -> None:
    prompt = _writer_template()

    assert "Grammar claim grounding" in prompt
    assert "EVERY specific grammar claim" in prompt
    assert 'source="..." grade="..." author="..."' in prompt
    assert "mcp__sources__search_text" in prompt
    assert re.search(r"exact grade\s+and\s+author", prompt)


def test_writer_prompt_locks_structured_end_gate_nodes() -> None:
    prompt = _writer_template()

    assert "<end_gate>" in prompt
    assert "</end_gate>" in prompt
    assert "actions: [" not in prompt
    for node in END_GATE_NODES:
        assert node in prompt


def test_writer_prompt_has_hard_stop_rule_after_artifacts() -> None:
    prompt = _writer_template()

    assert "## HARD STOP RULE" in prompt
    assert "After emitting all required `<plan_reasoning>` blocks" in prompt
    assert "the 4 artifact fences" in prompt
    assert "Do not write a summary, status report, completion" in prompt
    assert "confirmation, or any meta-commentary about what you did" in prompt
    assert "Anything after the `<end_gate>` block will be discarded by the" in prompt
    assert "parser. If you feel the urge to write" in prompt
    assert "The verification is in the `<end_gate>` block, not in prose" in prompt


def test_plan_reasoning_parser_preserves_nested_xml_body() -> None:
    output = """<plan_reasoning section="intro">
<word_budget>80 words.</word_budget>
<plan_vocab>кіт: Я бачу кота.</plan_vocab>
<register>80/20 immersion.</register>
<teaching_sequence>Knowledge Packet citation A.</teaching_sequence>
<verification_plan>Use VESUM.</verification_plan>
<verification_trace>mcp__sources__verify_words(["кіт"])</verification_trace>
</plan_reasoning>"""

    blocks = linear_pipeline._extract_plan_reasoning_blocks(output)

    assert blocks == [
        {
            "section": "intro",
            "body": (
                "<word_budget>80 words.</word_budget>\n"
                "<plan_vocab>кіт: Я бачу кота.</plan_vocab>\n"
                "<register>80/20 immersion.</register>\n"
                "<teaching_sequence>Knowledge Packet citation A.</teaching_sequence>\n"
                "<verification_plan>Use VESUM.</verification_plan>\n"
                '<verification_trace>mcp__sources__verify_words(["кіт"])</verification_trace>'
            ),
        }
    ]


def test_reasoning_fields_require_xml_subnodes_not_prose_labels() -> None:
    body = """
word_budget: 80 words.
plan_vocab: кіт in a sentence.
register: 80/20 split.
teaching_sequence: Knowledge Packet citation A.
verification_plan: Use VESUM.
verification_trace: mcp__sources__verify_words(["кіт"])
"""

    assert linear_pipeline._reasoning_fields_filled(body) == []


def test_verification_trace_tools_are_detected_as_theatre_when_uncalled() -> None:
    output = """<plan_reasoning section="intro">
<word_budget>80 words.</word_budget>
<plan_vocab>кіт: Я бачу кота.</plan_vocab>
<register>80/20 immersion.</register>
<teaching_sequence>Knowledge Packet citation A.</teaching_sequence>
<verification_plan>Use VESUM and textbook search.</verification_plan>
<verification_trace>mcp__sources__verify_words(["кіт"]); mcp__sources__search_text("відмінок")</verification_trace>
</plan_reasoning>"""

    assert linear_pipeline.detect_tool_theatre(
        output,
        [{"tool": "mcp__sources__verify_words"}],
    ) == ["search_text"]


def test_end_gate_grammar_claims_grounded_requires_structured_key() -> None:
    gate = linear_pipeline._extract_writer_gate(
        "<end_gate>grammar grounding ideas against a textbook</end_gate>"
    )

    assert gate["gate_actions"] == []
