from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS

WRITER_SECTIONS = ["intro", "vocabulary", "dialogue", "practice", "resources"]


def _event_sink(events: list[dict[str, Any]]):
    def sink(event: str, **fields: Any) -> None:
        events.append({"event": event, "ts": "2026-05-05T00:00:00+00:00", **fields})

    return sink


def _writer_prompt() -> str:
    contract = {
        "sections": [
            {"title": section, "word_budget": {"target": 80}, "covers": [section]}
            for section in WRITER_SECTIONS
        ]
    }
    return (
        "## Module Context\n\n"
        "- Level: A1\n"
        "- Module: 20\n"
        "- Slug: telemetry-fixture\n\n"
        "## Contract YAML\n\n"
        "```yaml\n"
        f"{linear_pipeline.yaml.safe_dump(contract, sort_keys=False)}"
        "```\n"
    )


def _writer_response() -> str:
    reasoning = "\n\n".join(
        f"""<plan_reasoning section="{section}">
<word_budget>Allocate 80 words to {section}.</word_budget>
<plan_vocab>Place required vocabulary in a concrete Ukrainian sentence.</plan_vocab>
<register>Keep the Ukrainian/English immersion split tight.</register>
<teaching_sequence>Anchor the section in the knowledge packet citations.</teaching_sequence>
<verification_plan>Call MCP tools for section claims.</verification_plan>
<verification_trace>mcp__sources__verify_words(["привіт"])</verification_trace>
</plan_reasoning>"""
        for section in WRITER_SECTIONS
    )
    return f"""{reasoning}

```markdown file=module.md
## intro
Привіт. Це короткий вступ.
```

```json file=activities.yaml
[
  {{"id": "act-1", "type": "fill-in", "items": []}}
]
```

```json file=vocabulary.yaml
[
  {{"lemma": "привіт", "translation": "hello", "pos": "noun", "usage": "Привіт!"}}
]
```

```json file=resources.yaml
[
  {{"title": "Fixture source", "notes": "Test source."}}
]
```

<end_gate>
<rescanned_words>Checked мама, тато, кава, школа, дім, ранок, вечір, взірець against VESUM.</rescanned_words>
<rescanned_sources>Checked Fixture source against MCP.</rescanned_sources>
<grammar_claims_grounded>Grounded one grammar note in the Knowledge Packet.</grammar_claims_grounded>
<removed_unverified>Removed 1 unverified lemma.</removed_unverified>
</end_gate>
"""


def _writer_tool_calls() -> list[dict[str, Any]]:
    words = ["мама", "тато", "кава", "школа", "дім", "ранок", "вечір", "взірець"]
    verified = {word: [{"lemma": word}] for word in words[:-1]}
    verified["взірець"] = []
    return [
        {
            "tool": "mcp__sources__verify_words",
            "section": "vocabulary",
            "args": {"words": words},
            "result": verified,
            "duration_ms": 421,
        },
        {
            "tool": "search_definitions",
            "section": "vocabulary",
            "args": {"query": "кава", "limit": 1},
            "result": [{"definition": "Fixture definition"}],
            "duration_ms": 88,
        },
        {
            "tool": "verify_lemma",
            "section": "practice",
            "args": {"lemma": "привіт"},
            "result": [{"word_form": "привіт"}],
            "duration_ms": 37,
        },
    ]


def _reviewer_prompt(dim: str) -> str:
    return (
        "## Module Context\n\n"
        "- Level: A1\n"
        "- Module: 20\n"
        "- Slug: telemetry-fixture\n\n"
        f"Assigned dimension: {dim}\n"
    )


def _reviewer_response(dim: str) -> str:
    score_by_dim = {
        "pedagogical": 8.0,
        "naturalness": 8.5,
        "decolonization": 7.5,
        "engagement": 9.0,
        "tone": 8.0,
    }
    quote_a = f"{dim} quote one"
    quote_b = f"{dim} quote two"
    quote_c = f"{dim} quote three"
    return json.dumps(
        {
            "score": score_by_dim[dim],
            "evidence": f"\"{quote_a}\"",
            "evidence_quotes": [quote_a, quote_b, quote_c],
            "rubric_mapping": f"{dim} quotes map directly to the rubric.",
            "verdict": "PASS",
        }
    )


def _reviewer_audit_calls(dim: str) -> list[dict[str, Any]]:
    calls_by_dim = {
        "pedagogical": [
            ("search_text", "quote_verification", 1),
            ("search_definitions", "source_attribution", 1),
        ],
        "naturalness": [("verify_lemma", "modern_form_check", 1)],
        "decolonization": [
            ("search_grinchenko_1907", "source_attribution", 1),
            ("search_style_guide", "sovietization_check", 1),
            ("check_modern_form", "modern_form_check", 1),
        ],
        "engagement": [("query_wikipedia", "quote_verification", 1)],
        "tone": [("search_idioms", "sovietization_check", 1)],
    }
    return [
        {
            "tool": tool,
            "audit_type": audit_type,
            "args": {"items": [f"{dim}-{index}" for index in range(count)]},
            "result": {"items_checked": count, "items_failed": 0, "flags_raised": []},
        }
        for tool, audit_type, count in calls_by_dim[dim]
    ]


def _events_named(events: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [event for event in events if event["event"] == name]


def test_writer_telemetry_events_fire_from_invocation_wrapper() -> None:
    events: list[dict[str, Any]] = []

    def invoker(agent: str, prompt: str, **kwargs: Any) -> SimpleNamespace:
        assert agent == "claude"
        assert prompt == _writer_prompt()
        assert kwargs["entrypoint"] == "dispatch"
        return SimpleNamespace(response=_writer_response(), tool_calls=_writer_tool_calls())

    response = linear_pipeline.invoke_writer(
        _writer_prompt(),
        "claude-tools",
        invoker=invoker,
        event_sink=_event_sink(events),
    )

    assert response == _writer_response()
    cot_events = _events_named(events, "writer_cot_emit")
    assert len(cot_events) == 5
    assert {event["section"] for event in cot_events} == set(WRITER_SECTIONS)
    assert all(event["block_present"] is True for event in cot_events)
    assert all(event["block_chars"] > 0 for event in cot_events)
    assert all(set(event["fields_filled"]) == set(linear_pipeline.PROMPT_ADHERENCE_FIELDS) for event in cot_events)

    tool_events = _events_named(events, "writer_tool_call")
    assert len(tool_events) == 3
    verify_event = next(event for event in tool_events if event["tool"] == "verify_words")
    assert verify_event["args_summary"] == {"count": 8}
    assert verify_event["result_summary"] == {
        "verified": 7,
        "failed": 1,
        "failed_words": ["взірець"],
    }
    assert verify_event["duration_ms"] == 421

    gate_event = _events_named(events, "writer_end_gate")[0]
    assert gate_event["gate_present"] is True
    assert gate_event["gate_actions"] == [
        "rescanned_words",
        "rescanned_sources",
        "grammar_claims_grounded",
        "removed_unverified",
    ]
    assert gate_event["removed_count"] == 1

    summary = _events_named(events, "phase_writer_summary")[0]
    assert summary["sections_total"] == 5
    assert summary["sections_with_cot"] == 5
    assert summary["tool_calls_total"] == 3
    assert summary["verify_words_calls"] == 1
    assert summary["end_gate_fired"] is True
    assert summary["removed_via_gate"] == 1


def test_reviewer_telemetry_events_and_rollup_fire_from_dim_wrappers() -> None:
    events: list[dict[str, Any]] = []

    def invoker(agent: str, prompt: str, **kwargs: Any) -> SimpleNamespace:
        assert agent == "gemini"
        assert kwargs["entrypoint"] == "dispatch"
        dim = kwargs["task_id"].removeprefix("phase-4-review-")
        assert prompt == _reviewer_prompt(dim)
        return SimpleNamespace(
            response=_reviewer_response(dim),
            tool_calls=_reviewer_audit_calls(dim),
        )

    report: dict[str, dict[str, Any]] = {}
    for dim in QG_DIMS:
        response = linear_pipeline.invoke_reviewer_dim(
            _reviewer_prompt(dim),
            "gemini-tools",
            dim=dim,
            writer_under_review="claude-tools",
            invoker=invoker,
            event_sink=_event_sink(events),
        )
        report[dim] = linear_pipeline.parse_review_response(response, dim)

    audit_calls_total = len(_events_named(events, "reviewer_audit_call"))
    flags_raised_total = sum(
        len(event["flags_raised"])
        for event in _events_named(events, "reviewer_audit_call")
    )
    linear_pipeline.aggregate_llm_review(
        report,
        "A1",
        reviewer="gemini-tools",
        module="a1/20",
        writer_under_review="claude-tools",
        audit_calls_total=audit_calls_total,
        flags_raised_total=flags_raised_total,
        event_sink=_event_sink(events),
    )

    dim_events = _events_named(events, "reviewer_dim_evidence")
    assert len(dim_events) == 5
    assert {event["dim"] for event in dim_events} == set(QG_DIMS)
    assert all(len(event["evidence_quotes"]) == 3 for event in dim_events)
    assert all(len(event["rubric_mapping"]) <= 500 for event in dim_events)
    assert all(event["writer_under_review"] == "claude-tools" for event in dim_events)

    audit_events = _events_named(events, "reviewer_audit_call")
    assert len(audit_events) == 8
    assert {event["audit_type"] for event in audit_events} == {
        "source_attribution",
        "quote_verification",
        "sovietization_check",
        "modern_form_check",
    }
    assert all(event["items_checked"] >= 1 for event in audit_events)
    assert all(event["items_failed"] == 0 for event in audit_events)
    assert all(event["flags_raised"] == [] for event in audit_events)

    summary = _events_named(events, "phase_review_summary")[0]
    assert summary["dims_scored"] == 5
    assert summary["dims_with_evidence"] == 5
    assert summary["audit_calls_total"] == 8
    assert summary["flags_raised_total"] == 0
    assert summary["min_dim_score"] == 7.5
    assert summary["weighted_score"] == 8.2


def test_telemetry_event_schema_is_bounded_and_flat() -> None:
    events: list[dict[str, Any]] = []
    linear_pipeline.emit_writer_response_telemetry(
        _writer_response(),
        writer="claude-tools",
        module="a1/20",
        sections=WRITER_SECTIONS,
        tool_calls=_writer_tool_calls(),
        event_sink=_event_sink(events),
    )

    for event in events:
        assert "event" in event
        assert "ts" in event
        if event["event"] == "writer_tool_call":
            assert set(event["args_summary"]) <= {"count", "keys", "lemma", "query_chars", "type", "word"}
            assert "args" not in event
            assert "result" not in event
        if event["event"] == "writer_cot_emit":
            assert event["block_chars"] < 1000
            assert set(event["fields_filled"]) <= set(linear_pipeline.PROMPT_ADHERENCE_FIELDS)


def test_telemetry_event_sink_appends_jsonl(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline.emit_event("first", slug="x")
    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline.emit_event("second", slug="x")

    captured = capsys.readouterr()
    events = [json.loads(line) for line in telemetry.read_text("utf-8").splitlines()]

    assert captured.out == ""
    assert [event["event"] for event in events] == ["first", "second"]
    assert all(event["slug"] == "x" for event in events)
