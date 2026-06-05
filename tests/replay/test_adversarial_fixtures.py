import json
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.codex import CodexAdapter, InvocationPlan
from scripts.build.linear_pipeline import (
    _build_vesum_text,
    _result_items_from_call,
    _summarize_generic_tool_result,
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
    plan = InvocationPlan(cmd=["dummy"], cwd=".", stdin_payload="real prompt")
    adapter = CodexAdapter()

    assert adapter._rollout_matches_plan(fixture_path, plan) is True


def test_mc_with_correct_false_distractors():
    import yaml

    fixture_path = FIXTURES_DIR / "activities" / "mc_with_correct_false.yaml"
    activity = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))

    # _build_vesum_text extracts text that gets verified
    # The 'text' of options with 'correct: false' should not be in the output
    vesum_text = _build_vesum_text(module_text="", activities=[activity], vocabulary=[], resources=[])

    assert "правильно" in vesum_text
    assert "неправильно" not in vesum_text


@pytest.mark.xfail(reason="Issue #1905 Part 2")
def test_search_text_telemetry_shape():
    fixture_path = FIXTURES_DIR / "telemetry" / "search_text_result.json"
    result_data = json.loads(fixture_path.read_text(encoding="utf-8"))

    summary = _summarize_generic_tool_result(result_data)

    # Mock a call with the summary
    call = {
        "result_summary": summary,
        "result": None,  # Simulating result cleared from telemetry
    }

    items = _result_items_from_call(call)

    # This might fail because _summarize_generic_tool_result returns {"count": 1}
    # instead of preserving the items for _result_items_from_call to find.
    assert len(items) > 0
    assert items[0]["text"] == "some text"
