from __future__ import annotations

from scripts.build import linear_pipeline


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
