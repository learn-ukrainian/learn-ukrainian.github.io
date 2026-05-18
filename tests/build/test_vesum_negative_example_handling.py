from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from scripts.build import linear_pipeline


def _verify_except(
    missing: set[str],
    seen: list[list[str]] | None = None,
):
    def verify(words: list[str]) -> dict[str, list[dict[str, str]]]:
        if seen is not None:
            seen.append(list(words))
        return {
            word: ([] if word in missing else [{"lemma": word}])
            for word in words
        }

    return verify


def _events(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _vesum_gate(
    activities: list[dict[str, object]],
    *,
    missing: set[str] | None = None,
    seen: list[list[str]] | None = None,
) -> dict[str, object]:
    return linear_pipeline._vesum_gate(
        module_text="## Діалоги\n\nЯ дивлюся в дзеркало.",
        activities=activities,
        vocabulary=[],
        resources=[],
        verify_words_fn=_verify_except(missing or set(), seen),
    )


def test_bad_marker_in_true_false_statement_is_stripped() -> None:
    seen: list[list[str]] = []
    activity = {
        "id": "act-tf",
        "type": "true-false",
        "items": [
            {
                "statement": (
                    "Правильна форма — дивлюся, а не "
                    "<!-- bad -->дивюся<!-- /bad -->."
                ),
                "answer": True,
            }
        ],
    }

    result = _vesum_gate([activity], missing={"дивюся"}, seen=seen)

    assert result["passed"] is True
    assert "дивлюся" in seen[0]
    assert "дивюся" not in seen[0]


def test_bad_marker_in_error_correction_sentence_is_harmless() -> None:
    seen: list[list[str]] = []
    activity = {
        "id": "act-error",
        "type": "error-correction",
        "items": [
            {
                "sentence": "Я <!-- bad -->дивюся<!-- /bad --> в дзеркало.",
                "error": "дивюся",
                "correction": "дивлюся",
            }
        ],
    }

    result = _vesum_gate([activity], missing={"дивюся"}, seen=seen)

    assert result["passed"] is True
    assert "дивюся" not in seen[0]
    assert "дивлюся" in seen[0]


def test_true_false_ukrainian_negative_example_tail_is_stripped(
    tmp_path: Path,
) -> None:
    seen: list[list[str]] = []
    telemetry = tmp_path / "events.jsonl"
    activity = {
        "id": "act-tf",
        "type": "true-false",
        "items": [
            {
                "statement": "Правильна форма — дивлюся, а не дивюся.",
                "answer": True,
            }
        ],
    }

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = _vesum_gate([activity], missing={"дивюся"}, seen=seen)

    assert result["passed"] is True
    assert "дивюся" not in seen[0]
    events = _events(telemetry)
    event = next(
        item
        for item in events
        if item["event"] == "vesum_verified_negative_example_stripped"
    )
    assert event["activity_id"] == "act-tf"
    assert event["item_idx"] == 0
    assert event["forms"] == ["дивюся"]


def test_true_false_english_negative_example_tail_is_stripped(
    tmp_path: Path,
) -> None:
    seen: list[list[str]] = []
    telemetry = tmp_path / "events.jsonl"
    activity = {
        "id": "act-tf-pro",
        "type": "true-false",
        "items": [
            {
                "statement": "The correct first-person form is дивлюся, not дивюся.",
                "answer": True,
            }
        ],
    }

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = _vesum_gate([activity], missing={"дивюся"}, seen=seen)

    assert result["passed"] is True
    assert "дивюся" not in seen[0]
    assert any(
        event["event"] == "vesum_verified_negative_example_stripped"
        and event["forms"] == ["дивюся"]
        for event in _events(telemetry)
    )


def test_true_false_without_negative_example_pattern_emits_no_event(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "events.jsonl"
    activity = {
        "id": "act-tf",
        "type": "true-false",
        "items": [
            {"statement": "Форма дивлюся правильна.", "answer": True}
        ],
    }

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = _vesum_gate([activity], missing={"дивюся"})

    assert result["passed"] is True
    assert not any(
        event["event"] == "vesum_verified_negative_example_stripped"
        for event in _events(telemetry)
    )


def test_true_false_multi_form_negative_example_still_requires_markers(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "events.jsonl"
    activity = {
        "id": "act-tf",
        "type": "true-false",
        "items": [
            {
                "statement": (
                    "Правильна форма — дивлюся, а не дивюся або користуювася."
                ),
                "answer": True,
            }
        ],
    }

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = _vesum_gate([activity], missing={"дивюся", "користуювася"})

    assert result["passed"] is False
    assert result["missing"] == ["дивюся", "користуювася"]
    assert not any(
        event["event"] == "vesum_verified_negative_example_stripped"
        for event in _events(telemetry)
    )


def test_false_true_false_statement_stays_out_of_vesum_scope(
    tmp_path: Path,
) -> None:
    seen: list[list[str]] = []
    telemetry = tmp_path / "events.jsonl"
    activity = {
        "id": "act-tf",
        "type": "true-false",
        "items": [
            {
                "statement": "Правильна форма — дивлюся, а не дивюся.",
                "answer": False,
            }
        ],
    }

    with linear_pipeline.telemetry_event_sink(telemetry):
        result = _vesum_gate([activity], missing={"дивюся"}, seen=seen)

    assert result["passed"] is True
    assert "дивюся" not in seen[0]
    assert not any(
        event["event"] == "vesum_verified_negative_example_stripped"
        for event in _events(telemetry)
    )


def test_match_activity_bad_form_requires_marker() -> None:
    unmarked = {
        "id": "act-match",
        "type": "match",
        "items": [{"left": "Я дивюся в дзеркало.", "right": "I look."}],
    }
    marked = {
        "id": "act-match",
        "type": "match",
        "items": [
            {
                "left": "Я <!-- bad -->дивюся<!-- /bad --> в дзеркало.",
                "right": "I look.",
            }
        ],
    }

    assert _vesum_gate([unmarked], missing={"дивюся"})["missing"] == ["дивюся"]
    assert _vesum_gate([marked], missing={"дивюся"})["passed"] is True


def test_fill_in_sentence_bad_form_requires_marker() -> None:
    unmarked = {
        "id": "act-fill",
        "type": "fill-in",
        "items": [{"sentence": "Я дивюся в дзеркало.", "answer": "дивлюся"}],
    }
    marked = {
        "id": "act-fill",
        "type": "fill-in",
        "items": [
            {
                "sentence": "Я <!-- bad -->дивюся<!-- /bad --> в дзеркало.",
                "answer": "дивлюся",
            }
        ],
    }

    assert _vesum_gate([unmarked], missing={"дивюся"})["missing"] == ["дивюся"]
    assert _vesum_gate([marked], missing={"дивюся"})["passed"] is True


def test_detect_unmarkered_negative_examples_finds_writer_omission() -> None:
    activities_yaml = yaml.safe_dump(
        [
            {
                "id": "act-tf",
                "type": "true-false",
                "items": [
                    {
                        "statement": "Правильна форма — дивлюся, не дивюся.",
                        "answer": True,
                    }
                ],
            }
        ],
        allow_unicode=True,
        sort_keys=False,
    )

    findings = linear_pipeline.detect_unmarkered_negative_examples(activities_yaml)

    assert findings == [
        {
            "activity_id": "act-tf",
            "item_idx": 0,
            "form": "дивюся",
            "hint": (
                "Wrap the negative example as "
                "<!-- bad -->дивюся<!-- /bad -->."
            ),
        }
    ]


def test_m20_style_true_false_negative_example_smoke(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    activities = [
        {
            "id": "act-error-l2",
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Я дивюся в дзеркало.",
                    "error": "дивюся",
                    "correction": "дивлюся",
                }
            ],
        },
        {
            "id": "act-tf",
            "type": "true-false",
            "items": [
                {
                    "statement": (
                        "У дієсловах другої дієвідміни 1-ша особа однини "
                        "після губних має вставне 'л' — дивлюся, а не дивюся."
                    ),
                    "answer": True,
                }
            ],
        },
    ]

    with monkeypatch.context() as disabled_safety_net:
        disabled_safety_net.setattr(
            linear_pipeline,
            "_TF_NEGATIVE_EXAMPLE_RE",
            re.compile(r"a^"),
        )
        baseline = _vesum_gate(activities, missing={"дивюся"})

    telemetry = tmp_path / "events.jsonl"
    with linear_pipeline.telemetry_event_sink(telemetry):
        result = _vesum_gate(activities, missing={"дивюся"})

    assert baseline["passed"] is False
    assert baseline["missing"] == ["дивюся"]
    assert result["passed"] is True
    assert any(
        event["event"] == "vesum_verified_negative_example_stripped"
        and event["activity_id"] == "act-tf"
        and event["forms"] == ["дивюся"]
        for event in _events(telemetry)
    )
