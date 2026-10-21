"""Tests for the early activity_schema Python QG gate."""

from __future__ import annotations

from scripts.build.linear_pipeline import (
    PYTHON_QG_GATE_ORDER,
    LinearPipelineError,
    _activity_schema_gate,
    _apply_activity_schema_correction,
    _load_bare_activity_list,
)


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


def test_load_activity_list_accepts_inline_workbook_v2(tmp_path) -> None:
    path = tmp_path / "activities.yaml"
    path.write_text(
        """
version: '1.0'
module: sample
level: b1
inline:
  - id: act-1
    type: variant-comparison
workbook:
  - type: essay-response
""".lstrip(),
        encoding="utf-8",
    )

    assert _load_bare_activity_list(path) == [
        {"id": "act-1", "type": "variant-comparison"},
        {"type": "essay-response"},
    ]


def test_load_activity_list_rejects_unknown_v2_keys(tmp_path) -> None:
    path = tmp_path / "activities.yaml"
    path.write_text(
        """
inline:
  - id: act-1
    type: variant-comparison
extra:
  - type: essay-response
""".lstrip(),
        encoding="utf-8",
    )

    try:
        _load_bare_activity_list(path)
    except LinearPipelineError as exc:
        assert "unexpected keys" in str(exc)
        assert "extra" in str(exc)
    else:
        raise AssertionError("unexpected V2 activity keys should be rejected")


def test_load_activity_list_rejects_activities_wrapper(tmp_path) -> None:
    path = tmp_path / "activities.yaml"
    path.write_text(
        """
activities:
  - id: act-1
    type: quiz
""".lstrip(),
        encoding="utf-8",
    )

    try:
        _load_bare_activity_list(path)
    except LinearPipelineError as exc:
        assert "not activities:" in str(exc)
    else:
        raise AssertionError("activities: wrapper should be rejected")


def test_activity_schema_correction_removes_forbidden_item_fields_preserving_v2(tmp_path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    path = module_dir / "activities.yaml"
    path.write_text(
        """
version: '1.0'
module: sample
level: b1
inline:
  - id: act-1
    type: error-correction
    items:
      - sentence: "Не <error> файл."
        error: "відкрий"
        correction: "відкривай"
        error_type: aspect
workbook: []
""".lstrip(),
        encoding="utf-8",
    )
    gate_report = _activity_schema_gate(_load_bare_activity_list(path))

    payload = _apply_activity_schema_correction(module_dir=module_dir, gate_report=gate_report)

    assert payload["applied"] is True
    fixed = path.read_text(encoding="utf-8")
    assert "version: '1.0'" in fixed
    assert "inline:" in fixed
    assert "  - id: act-1" in fixed
    assert "\n- id: act-1" not in fixed
    assert "workbook: []" in fixed
    assert "error_type" not in fixed
    assert _activity_schema_gate(_load_bare_activity_list(path))["passed"] is True


def test_activity_schema_correction_scopes_forbidden_item_field_removal(tmp_path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    path = module_dir / "activities.yaml"
    path.write_text(
        """
version: '1.0'
module: sample
level: b1
inline:
  - id: act-1
    type: error-correction
    items:
      - sentence: "Перший."
        error: "а"
        correction: "б"
        error_type: keep-me
  - id: act-2
    type: error-correction
    items:
      - sentence: "Другий."
        error: "в"
        correction: "г"
        error_type: remove-me
workbook: []
""".lstrip(),
        encoding="utf-8",
    )
    gate_report = {
        "violations": [
            {
                "activity_id": "act-2",
                "activity_index": 2,
                "item_index": 1,
                "offending_field": "error_type",
                "expected_field": None,
            }
        ]
    }

    _apply_activity_schema_correction(module_dir=module_dir, gate_report=gate_report)

    fixed = path.read_text(encoding="utf-8")
    assert "error_type: keep-me" in fixed
    assert "error_type: remove-me" not in fixed


def test_activity_schema_correction_preserves_v2_when_multiple_normalizers_apply(tmp_path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    path = module_dir / "activities.yaml"
    path.write_text(
        """
version: '1.0'
module: sample
level: b1
inline:
  - id: act-1
    type: performance
    prompt: "Виконайте."
    self_check: "old"
    self_checklist:
      - "new"
  - id: act-2
    type: error-correction
    items:
      - sentence: "Не <error> файл."
        error: "відкрий"
        correction: "відкривай"
        error_type: aspect
workbook: []
""".lstrip(),
        encoding="utf-8",
    )
    gate_report = _activity_schema_gate(_load_bare_activity_list(path))

    payload = _apply_activity_schema_correction(module_dir=module_dir, gate_report=gate_report)

    assert payload["applied"] is True
    fixed = path.read_text(encoding="utf-8")
    assert "version: '1.0'" in fixed
    assert "  - id: act-1" in fixed
    assert "  - id: act-2" in fixed
    assert "    self_check: \"old\"" not in fixed
    assert "    self_checklist:" in fixed
    assert "error_type" not in fixed
    assert _activity_schema_gate(_load_bare_activity_list(path))["passed"] is True


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


def test_performance_self_check_string_fails_activity_schema() -> None:
    activities = [
        {
            "id": "folk-performance",
            "type": "performance",
            "prompt": "Продекламуйте фрагмент.",
            "fragment": "Добрий вечір.",
            "self_check": "Чітко вимовлено звертання.",
        }
    ]

    result = _activity_schema_gate(activities)

    assert result["passed"] is False
    assert result["checked"] == 0
    assert result["violations"][0]["activity_id"] == "folk-performance"
    assert result["violations"][0]["scope"] == "activity"
    assert result["violations"][0]["offending_field"] == "self_check"
    assert result["violations"][0]["expected_type"] == "list"
    assert result["violations"][0]["actual_type"] == "str"
    assert (
        result["violations"][0]["message"]
        == "performance activity 'self_check' must be a list, not a str"
    )
    assert "performance activity 'self_check' must be a list, not a str" in result["message"]


def test_performance_self_check_list_passes_activity_schema() -> None:
    activities = [
        {
            "id": "folk-performance",
            "type": "performance",
            "prompt": "Продекламуйте фрагмент.",
            "fragment": "Добрий вечір.",
            "self_check": ["Чітко вимовлено звертання."],
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
