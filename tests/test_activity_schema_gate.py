"""Tests for the early activity_schema Python QG gate."""

from __future__ import annotations

from scripts.build.linear_pipeline import PYTHON_QG_GATE_ORDER, _activity_schema_gate


def test_canonical_error_correction_passes() -> None:
    activities = [
        {
            "id": "morning-routine-error-correction",
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Я <error> о сьомій.",
                    "error": "прокидаєшся",
                    "correction": "прокидаюся",
                }
            ],
        }
    ]

    result = _activity_schema_gate(activities)

    assert result == {"passed": True, "checked": 1, "violations": []}


def test_forbidden_alias_incorrect_fails() -> None:
    activities = [
        {
            "id": "morning-routine-error-correction",
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Я <error> о сьомій.",
                    "incorrect": "прокидаєшся",
                    "correction": "прокидаюся",
                }
            ],
        }
    ]

    result = _activity_schema_gate(activities)

    assert result["passed"] is False
    assert result["checked"] == 1
    assert result["violations"][0]["offending_field"] == "incorrect"
    assert result["violations"][0]["expected_field"] == "error"
    assert "use 'error:'" in result["violations"][0]["message"]


def test_forbidden_alias_wrong_fails() -> None:
    activities = [
        {
            "id": "wrong-field-error-correction",
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Він <error> пізно.",
                    "wrong": "прокидаюся",
                    "answer": "прокидається",
                }
            ],
        }
    ]

    result = _activity_schema_gate(activities)

    assert result["passed"] is False
    assert any(
        violation["offending_field"] == "wrong"
        and violation["expected_field"] == "error"
        for violation in result["violations"]
    )


def test_missing_required_error_field_fails() -> None:
    activities = [
        {
            "id": "missing-error-field",
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Я <error> вранці.",
                    "correction": "вмиваюся",
                }
            ],
        }
    ]

    result = _activity_schema_gate(activities)

    assert result["passed"] is False
    assert any(
        violation["offending_field"] is None
        and violation["expected_field"] == "error"
        and "must include 'error:'" in violation["message"]
        for violation in result["violations"]
    )


def test_multiple_violations_all_reported() -> None:
    activities = [
        {
            "id": "multi-alias-error-correction",
            "type": "error-correction",
            "items": [
                {
                    "sentence": "Я <error> о сьомій.",
                    "incorrect": "прокидаєшся",
                    "correction": "прокидаюся",
                },
                {
                    "sentence": "Він <error> пізно.",
                    "wrong": "прокидаюся",
                    "answer": "прокидається",
                },
                {
                    "sentence": "Я <error> в дзеркало.",
                    "correctAnswer": "дивлюся",
                    "error": "дивюся",
                },
            ],
        }
    ]

    result = _activity_schema_gate(activities)
    fields = {
        (violation["offending_field"], violation["expected_field"])
        for violation in result["violations"]
    }

    assert result["passed"] is False
    assert ("incorrect", "error") in fields
    assert ("wrong", "error") in fields
    assert ("correctAnswer", "correction") in fields


def test_non_error_correction_activities_pass_through() -> None:
    activities = [
        {
            "id": "dialogue-practice",
            "type": "dialogue",
            "items": [
                {
                    "incorrect": "This field is ignored because dialogue has no strict item schema.",
                }
            ],
        }
    ]

    result = _activity_schema_gate(activities)

    assert result == {"passed": True, "checked": 0, "violations": []}


def test_replays_m20_build8_failure_shape() -> None:
    activities = [
        {
            "id": "morning-routine-error-correction",
            "type": "error-correction",
            "items": [
                {"incorrect": "Я прокидаєшся о сьомій."},
                {"incorrect": "Я дивюся в дзеркало."},
            ],
        }
    ]

    result = _activity_schema_gate(activities)

    assert result["passed"] is False
    assert any(
        violation["offending_field"] == "incorrect"
        and violation["expected_field"] == "error"
        for violation in result["violations"]
    )


def test_activity_schema_gate_precedes_vesum_verified() -> None:
    assert PYTHON_QG_GATE_ORDER.index("activity_schema") < PYTHON_QG_GATE_ORDER.index(
        "vesum_verified"
    )
