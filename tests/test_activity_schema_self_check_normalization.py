from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from scripts.build import linear_pipeline


def _write_activities(module_dir: Path, activities: list[dict[str, Any]]) -> None:
    (module_dir / "activities.yaml").write_text(
        yaml.safe_dump(activities, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _activity_schema_only_report(module_dir: Path) -> dict[str, Any]:
    activities = yaml.safe_load((module_dir / "activities.yaml").read_text("utf-8"))
    gate = linear_pipeline._activity_schema_gate(activities)
    return {"gates": {"activity_schema": gate, "passed": gate["passed"]}}


def test_activity_schema_correction_drops_duplicate_string_self_check(
    tmp_path: Path,
) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    checklist = [
        "Я витримав спокійний, рівний тон зачину.",
        "Я не пришвидшив приспів.",
    ]
    _write_activities(
        module_dir,
        [
            {
                "id": "koliadky-performance",
                "type": "performance",
                "title": "Колядування",
                "prompt": "Продекламуй зачин колядки.",
                "fragment": "Добрий вечір тобі.",
                "self_check": "Чи витримав ти спокійний, рівний тон зачину?",
                "self_checklist": checklist,
            }
        ],
    )
    reports: list[dict[str, Any]] = []

    def qg_runner() -> dict[str, Any]:
        report = _activity_schema_only_report(module_dir)
        reports.append(report)
        return report

    def writer_corrector(_context: linear_pipeline.CorrectionContext) -> str:
        raise AssertionError("self_check normalization must not call an LLM writer")

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        tmp_path / "plan.yaml",
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    rewritten = yaml.safe_load((module_dir / "activities.yaml").read_text("utf-8"))
    assert "self_check" not in rewritten[0]
    assert rewritten[0]["self_checklist"] == checklist
    assert linear_pipeline._activity_schema_gate(rewritten)["passed"] is True
    assert len(reports) == 2
    assert reports[0]["gates"]["activity_schema"]["passed"] is False
    assert reports[1]["gates"]["activity_schema"]["passed"] is True
    assert report["gates"]["activity_schema"]["passed"] is True
    assert report["gates"]["passed"] is True
    assert report["gates"].get("previously_passed_regression", {"passed": True})[
        "passed"
    ] is True

    correction = json.loads(
        (module_dir / "python_qg_correction_r1.json").read_text("utf-8")
    )
    assert correction["gate"] == "activity_schema"
    assert correction["correction"]["applied"] is True
    assert correction["correction"]["diagnostic"]["normalized_count"] == 1


def test_activity_schema_self_check_normalization_negative_cases() -> None:
    valid_list = [
        {
            "id": "valid-performance",
            "type": "performance",
            "prompt": "Продекламуй фрагмент.",
            "self_check": ["Дикція чітка."],
            "self_checklist": ["Дикція чітка."],
        }
    ]
    missing_checklist = [
        {
            "id": "invalid-performance",
            "type": "performance",
            "prompt": "Продекламуй фрагмент.",
            "self_check": "Дикція чітка.",
        }
    ]
    non_performance = [
        {
            "id": "dialogue-self-check",
            "type": "dialogue",
            "self_check": "Дикція чітка.",
            "self_checklist": ["Дикція чітка."],
        }
    ]

    normalized, diagnostic = linear_pipeline._normalize_performance_self_check_duplicates(
        valid_list
    )
    assert normalized == valid_list
    assert diagnostic["normalized_count"] == 0
    assert linear_pipeline._activity_schema_gate(normalized)["passed"] is True

    normalized, diagnostic = linear_pipeline._normalize_performance_self_check_duplicates(
        missing_checklist
    )
    assert normalized == missing_checklist
    assert diagnostic["normalized_count"] == 0
    assert linear_pipeline._activity_schema_gate(normalized)["passed"] is False

    normalized, diagnostic = linear_pipeline._normalize_performance_self_check_duplicates(
        non_performance
    )
    assert normalized == non_performance
    assert diagnostic["normalized_count"] == 0
