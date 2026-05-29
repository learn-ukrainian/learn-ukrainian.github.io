"""Tests for quiz/translate explanation Python QG coverage."""

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
    ]

    result = _quiz_translate_explanation_gate(activities)

    assert result == {"passed": True, "checked": 2, "violations": []}


def test_quiz_translate_explanation_gate_runs_after_schema() -> None:
    assert PYTHON_QG_GATE_ORDER.index("activity_schema") < PYTHON_QG_GATE_ORDER.index(
        "quiz_translate_explanations"
    )
