from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.codex import CodexAdapter
from scripts.build.linear_pipeline import (
    _result_items_from_call,
    _summarize_tool_result,
    _vesum_gate,
)
from scripts.wiki.sources_db import _prepare_query

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_prepare_query_handles_replayed_long_cyrillic_query() -> None:
    fixture_path = FIXTURES_DIR / "queries" / "long_cyrillic_query.txt"
    content = fixture_path.read_text(encoding="utf-8")
    assert len(content.encode("utf-8")) > 255

    bucket_a, bucket_b, dense = _prepare_query(content, "fast")

    assert isinstance(bucket_a, list)
    assert isinstance(bucket_b, set)
    assert dense


def test_vesum_gate_skips_replayed_correct_false_distractors() -> None:
    activity = yaml.safe_load(
        (FIXTURES_DIR / "activities" / "mc_with_correct_false.yaml").read_text(
            encoding="utf-8",
        )
    )
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        return {word: [{"lemma": word}] for word in words}

    result = _vesum_gate(
        module_text="",
        activities=[activity],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert result["passed"] is True
    assert "книга" in sent_for_verification
    assert "олівець" not in sent_for_verification


def test_search_text_summary_preserves_replayed_result_items() -> None:
    result_data = json.loads(
        (FIXTURES_DIR / "telemetry" / "search_text_result.json").read_text(
            encoding="utf-8",
        )
    )

    summary = _summarize_tool_result("search_text", result_data)
    call: dict[str, Any] = {
        "tool": "search_text",
        "result_summary": summary,
        "result": None,
    }

    items = _result_items_from_call(call)

    assert summary["count"] == 1
    assert items
    assert items[0]["source_type"] == "textbook"
    assert items[0]["text"] == "some text"


def test_codex_rollout_matches_replayed_agents_md_envelope() -> None:
    rollout_path = FIXTURES_DIR / "rollouts" / "agents_md_envelope.jsonl"
    plan = InvocationPlan(cmd=["codex"], cwd=Path("."), stdin_payload="real prompt")

    assert CodexAdapter()._rollout_matches_plan(rollout_path, plan) is True
