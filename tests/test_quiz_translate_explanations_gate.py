"""Tests for quiz/translate/fill-in explanation Python QG coverage (#8214)."""

from __future__ import annotations

from scripts.build.linear_pipeline import PYTHON_QG_GATE_ORDER, _quiz_translate_explanation_gate


def test_empty_quiz_translate_explanation_fails() -> None:
    activities = [
        {
            "id": "morning-quiz",
            "type": "quiz",
            "items": [
                {
                    "question": "I wake up -> ?",
                    "options": [{"text": "prokydaiusia", "correct": True}],
                    "explanation": "",
                }
            ],
        },
        {
            "id": "morning-translate",
            "type": "translate",
            "items": [
                {
                    "source": "I look in the mirror.",
                    "options": [{"text": "dyvliusia", "correct": True}],
                },
                {
                    "source": "I wash.",
                    "options": [{"text": "vmyvaiusia", "correct": True}],
                    "explanation": "   ",
                },
                {
                    "source": "I get dressed.",
                    "options": [{"text": "odiahaisia", "correct": True}],
                    "explanation": True,
                },
            ],
        },
    ]

    result = _quiz_translate_explanation_gate(activities)

    assert result["passed"] is False
    assert result["checked"] == 4
    assert [violation["reason"] for violation in result["violations"]] == [
        "empty",
        "missing",
        "empty",
        "invalid_type",
    ]
    assert "QUIZ_TRANSLATE_EXPLANATIONS_GATE FAILED: 4 violations" in result["message"]


def test_fill_in_missing_explanation_fails() -> None:
    """#8214 — micro-blank comedy without teaching feedback is a hard fail."""
    activities = [
        {
            "id": "act-w5",
            "type": "fill-in",
            "items": [
                {
                    "sentence": "бур___ян",
                    "answer": "'",
                    "options": ["'", "ь", ""],
                },
                {
                    "sentence": "ден___",
                    "answer": "ь",
                    "options": ["ь", "'", "й"],
                    "explanation": "День потребує м'якого знака.",
                },
            ],
        }
    ]
    result = _quiz_translate_explanation_gate(activities)
    assert result["passed"] is False
    assert result["checked"] == 2
    assert result["violations"][0]["activity_type"] == "fill-in"
    assert result["violations"][0]["reason"] == "missing"


def test_real_quiz_translate_explanations_pass() -> None:
    activities = [
        {
            "id": "morning-quiz",
            "type": "quiz",
            "items": [
                {
                    "question": "I wake up -> ?",
                    "options": [{"text": "prokydaiusia", "correct": True}],
                    "explanation": "Use the first-person reflexive ending for I.",
                }
            ],
        },
        {
            "id": "morning-translate",
            "type": "translate",
            "items": [
                {
                    "source": "I look in the mirror.",
                    "options": [{"text": "dyvliusia", "correct": True}],
                    "explanation": "This is the first-person reflexive form.",
                }
            ],
        },
        {
            "id": "ss-fill",
            "type": "fill-in",
            "items": [
                {
                    "sentence": "бур___ян",
                    "answer": "'",
                    "options": ["'", "ь"],
                    "explanation": (
                        "У слові бур'ян потрібен апостроф після р. — "
                        "In бур'ян an apostrophe is needed after р."
                    ),
                }
            ],
        },
    ]

    result = _quiz_translate_explanation_gate(activities)

    assert result == {"passed": True, "checked": 3, "violations": []}


def test_true_false_is_explanation_required() -> None:
    from scripts.build.linear_pipeline import _ACTIVITY_EXPLANATION_REQUIRED_TYPES

    expected = frozenset({"quiz", "translate", "fill-in", "true-false"})
    assert expected == _ACTIVITY_EXPLANATION_REQUIRED_TYPES


def test_true_false_missing_explanation_fails() -> None:
    result = _quiz_translate_explanation_gate(
        [
            {
                "id": "tf-1",
                "type": "true-false",
                "items": [{"statement": "The text says it.", "correct": True}],
            }
        ]
    )
    assert result["passed"] is False
    assert result["checked"] == 1
    assert result["violations"][0]["activity_type"] == "true-false"
    assert result["violations"][0]["reason"] == "missing"


def test_quiz_translate_explanation_gate_runs_after_schema() -> None:
    assert PYTHON_QG_GATE_ORDER.index("activity_schema") < PYTHON_QG_GATE_ORDER.index(
        "quiz_translate_explanations"
    )
