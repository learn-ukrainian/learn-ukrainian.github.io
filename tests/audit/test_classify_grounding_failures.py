from __future__ import annotations

import json
from pathlib import Path

from scripts.audit.classify_grounding_failures import classify_grounding
from scripts.audit.runtime_tool_events import map_runtime_tool_calls


def test_classify_paraphrase_when_tokens_overlap_retrieved_output() -> None:
    events = map_runtime_tool_calls(
        [
            {
                "name": "mcp__sources__query_wikipedia",
                "arguments": {"query": "Веснянки"},
                "result": [
                    {
                        "type": "text",
                        "text": (
                            "Веснянки — назва старовинних слов'янських обрядових пісень, "
                            "пов'язаних з початком весни"
                        ),
                    }
                ],
            }
        ]
    )
    grounding = {
        "tool": "mcp__sources__query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": (
            "назва старовинних слов'янських обрядових пісень про початок весни"
        ),
    }
    row = classify_grounding(grounding, events, source="fact_check", claim="genre")
    assert row is not None
    assert row.bucket == "paraphrase_of_retrieved"


def test_classify_fabrication_when_excerpt_absent_from_outputs() -> None:
    events = map_runtime_tool_calls(
        [
            {
                "name": "mcp__sources__query_wikipedia",
                "arguments": {"query": "Веснянки"},
                "result": [{"type": "text", "text": "Веснянки — обрядові пісні"}],
            }
        ]
    )
    grounding = {
        "tool": "mcp__sources__query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": "Дівчата прикрашали гаї стрічками під час обряду",
    }
    row = classify_grounding(grounding, events, source="fact_check", claim="ribbons")
    assert row is not None
    assert row.bucket == "excerpt_not_in_tool_output"


def test_confirmed_against_evidence_beats_paraphrase() -> None:
    events = map_runtime_tool_calls(
        [
            {
                "name": "mcp__sources__query_wikipedia",
                "arguments": {"query": "Веснянки"},
                "result": [
                    {
                        "type": "text",
                        "text": (
                            "інтонували мелодію пронизливо, майже криком, у дуже "
                            "високій теситурі; мелодії побудовані на повторенні "
                            "поспівок у межах невеликого діапазону"
                        ),
                    }
                ],
            }
        ]
    )
    grounding = {
        "tool": "mcp__sources__query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": (
            "інтонували мелодію пронизливо майже криком у дуже високій теситурі"
        ),
    }
    # Same grounding is benign paraphrase without gold context...
    paraphrase = classify_grounding(grounding, events, source="fact_check", claim="melody")
    assert paraphrase is not None
    assert paraphrase.bucket == "paraphrase_of_retrieved"
    # ...but a gold-false CONFIRMED verdict escalates it to against-evidence.
    against = classify_grounding(
        grounding, events, source="fact_check", claim="melody", against_evidence=True
    )
    assert against is not None
    assert against.bucket == "confirmed_against_evidence"


def test_confirmed_against_evidence_requires_supporting_output() -> None:
    events = map_runtime_tool_calls(
        [
            {
                "name": "mcp__sources__query_wikipedia",
                "arguments": {"query": "Веснянки"},
                "result": [{"type": "text", "text": "Веснянки — обрядові пісні"}],
            }
        ]
    )
    grounding = {
        "tool": "mcp__sources__query_wikipedia",
        "query": "Веснянки",
        "evidence_excerpt": "Дівчата прикрашали гаї стрічками під час обряду",
    }
    # No supporting output → stays fabrication even if verdict is a false CONFIRMED.
    row = classify_grounding(
        grounding, events, source="fact_check", claim="ribbons", against_evidence=True
    )
    assert row is not None
    assert row.bucket == "excerpt_not_in_tool_output"


def test_analyze_paths_on_vesnianky_multirun_artifact() -> None:
    root = Path(__file__).resolve().parents[2]
    artifact_path = (
        root
        / "audit/2026-07-06-qg-bakeoff-multirun/openrouter-deepseek-deepseek-v4-pro__vesnianky.json"
    )
    if not artifact_path.exists():
        return
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    from scripts.audit.classify_grounding_failures import classify_artifact

    rows = classify_artifact(artifact)
    assert rows, "expected at least one failed grounding in ds-pro vesnianky cell"
