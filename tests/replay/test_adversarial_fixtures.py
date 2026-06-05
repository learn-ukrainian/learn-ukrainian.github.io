import json
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.codex import CodexAdapter, InvocationPlan
from scripts.build.linear_pipeline import (
    _build_vesum_text,
    _result_items_from_call,
    _summarize_tool_result,
)
from scripts.wiki.sources_db import _prepare_query

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_long_cyrillic_query():
    fixture_path = FIXTURES_DIR / "queries" / "long_cyrillic_query.txt"
    content = fixture_path.read_text(encoding="utf-8")
    assert len(content.encode("utf-8")) > 255

    # Should return a tuple and not raise OSError
    result = _prepare_query(content, "fast")
    assert isinstance(result, tuple)
    assert len(result) == 3


@pytest.mark.xfail(reason="Issue #1905 Part 2")
def test_rollout_matches_plan():
    fixture_path = FIXTURES_DIR / "rollouts" / "agents_md_envelope.jsonl"

    # The real prompt is the last part of the content array
    plan = InvocationPlan(cmd=["dummy"], cwd=Path("."), stdin_payload="real prompt")
    adapter = CodexAdapter()

    assert adapter._rollout_matches_plan(fixture_path, plan) is True


def test_mc_with_correct_false_distractors():
    """Pin the documented `_activity_vesum_text` MC contract.

    By design (see `_activity_vesum_text` docstring), the `text` leaf of an
    `options` entry with falsy `correct` is treated as a potentially
    intentional wrong answer and is EXCLUDED from VESUM scope, while the
    correct option and surrounding prompt stay in scope. This is intentional —
    not a bug — so distractors that are fabricated wrong forms don't trip
    VESUM. The fixture uses non-overlapping tokens (книга / олівець) so the
    membership assertions can't be satisfied by substring coincidence.
    """
    import yaml

    fixture_path = FIXTURES_DIR / "activities" / "mc_with_correct_false.yaml"
    activity = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))

    vesum_text = _build_vesum_text(module_text="", activities=[activity], vocabulary=[], resources=[])

    # Correct option text is verified; distractor (correct: false) is excluded.
    assert "книга" in vesum_text
    assert "олівець" not in vesum_text


def test_search_text_telemetry_recovers_items_after_clear():
    """search_text telemetry must survive the raw result being cleared.

    Production summarizes a search_text tool result via
    `_summarize_tool_result("search_text", ...)` -> `_summarize_search_text_result`,
    which PRESERVES per-item `text` so `_result_items_from_call` can recover the
    grounded hits even after the raw `result` is dropped from the call record.
    (The generic summarizer collapses to `{"count": N}` and loses items, but the
    production search_text path does not use it — so the earlier xfail against
    `_summarize_generic_tool_result` documented a non-production code path.)
    """
    fixture_path = FIXTURES_DIR / "telemetry" / "search_text_result.json"
    result_data = json.loads(fixture_path.read_text(encoding="utf-8"))

    summary = _summarize_tool_result("search_text", result_data)
    call = {
        "tool": "search_text",
        "result_summary": summary,
        "result": None,  # raw result cleared from telemetry, summary retained
    }

    items = _result_items_from_call(call)

    assert len(items) > 0
    assert items[0]["text"] == "some text"
