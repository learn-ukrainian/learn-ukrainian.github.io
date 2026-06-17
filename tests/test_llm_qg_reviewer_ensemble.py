from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.build import linear_pipeline


def _review_response(score: float, evidence: str) -> str:
    return json.dumps(
        {
            "score": score,
            "evidence": f'"{evidence}"',
            "verdict": "PASS" if score >= 8.0 else "REVISE",
        }
    )


def _event_collector() -> tuple[list[dict[str, Any]], Any]:
    events: list[dict[str, Any]] = []

    def collect(event: str, **fields: Any) -> None:
        events.append({"event": event, **fields})

    return events, collect


def test_reviewer_ensemble_selects_odd_median_sample(monkeypatch: pytest.MonkeyPatch) -> None:
    scores = [6.0, 8.0, 7.0]
    calls: list[str] = []
    events, event_sink = _event_collector()

    def reviewer(_prompt: str, _reviewer: str, *, dim: str, **_kwargs: Any) -> str:
        sample_index = len(calls)
        calls.append(dim)
        return _review_response(scores[sample_index], f"sample {sample_index + 1}")

    monkeypatch.setattr(linear_pipeline, "invoke_reviewer_dim", reviewer)

    result = linear_pipeline.invoke_reviewer_dim_ensemble(
        "prompt",
        "codex-tools",
        dim="pedagogical",
        writer_under_review="claude-tools",
        reviewer_samples=3,
        event_sink=event_sink,
    )

    assert calls == ["pedagogical", "pedagogical", "pedagogical"]
    assert result == {
        "score": 7.0,
        "evidence": '"sample 3"',
        "verdict": "REVISE",
    }
    assert events == [
        {
            "event": "reviewer_ensemble",
            "dim": "pedagogical",
            "n": 3,
            "scores": [6.0, 8.0, 7.0],
            "median_score": 7.0,
            "chosen_sample_index": 2,
            "reviewer": "codex-tools",
            "module": None,
            "writer_under_review": "claude-tools",
        }
    ]


def test_reviewer_ensemble_n1_passthrough_single_call(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    events, event_sink = _event_collector()

    def reviewer(_prompt: str, _reviewer: str, *, dim: str, **_kwargs: Any) -> str:
        calls.append(dim)
        return _review_response(8.0, "single sample")

    monkeypatch.setattr(linear_pipeline, "invoke_reviewer_dim", reviewer)

    result = linear_pipeline.invoke_reviewer_dim_ensemble(
        "prompt",
        "codex-tools",
        dim="tone",
        writer_under_review="claude-tools",
        reviewer_samples=1,
        event_sink=event_sink,
    )

    assert calls == ["tone"]
    assert result == {
        "score": 8.0,
        "evidence": '"single sample"',
        "verdict": "PASS",
    }
    assert events == []


def test_reviewer_ensemble_even_n_uses_lower_middle_real_sample(monkeypatch: pytest.MonkeyPatch) -> None:
    scores = [6.0, 8.0, 7.0, 9.0]
    calls: list[str] = []
    events, event_sink = _event_collector()

    def reviewer(_prompt: str, _reviewer: str, *, dim: str, **_kwargs: Any) -> str:
        sample_index = len(calls)
        calls.append(dim)
        return _review_response(scores[sample_index], f"even sample {sample_index + 1}")

    monkeypatch.setattr(linear_pipeline, "invoke_reviewer_dim", reviewer)

    result = linear_pipeline.invoke_reviewer_dim_ensemble(
        "prompt",
        "codex-tools",
        dim="engagement",
        writer_under_review="claude-tools",
        reviewer_samples=4,
        event_sink=event_sink,
    )

    assert result == {
        "score": 7.0,
        "evidence": '"even sample 3"',
        "verdict": "REVISE",
    }
    assert events[0]["median_score"] == 7.0
    assert events[0]["chosen_sample_index"] == 2


def test_llm_qg_reviewer_samples_profile_config() -> None:
    assert linear_pipeline.llm_qg_reviewer_samples_for_level("folk") == 3
    assert linear_pipeline.llm_qg_reviewer_samples_for_level("a1") == 1
