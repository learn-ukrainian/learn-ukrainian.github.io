from __future__ import annotations

import ast
import inspect
import json
import textwrap
from pathlib import Path
from typing import Any

import yaml

from scripts.build import linear_pipeline


def _module_dir(tmp_path: Path, module_text: str = "STATE0\n") -> Path:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(module_text, encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def _plan_path(tmp_path: Path, level: str) -> Path:
    path = tmp_path / f"{level}.yaml"
    path.write_text(f"level: {level}\nsequence: 1\nslug: sample\n", encoding="utf-8")
    return path


def _writer_artifacts(module_text: str, *, activity_prompt: str = "state") -> dict[str, str]:
    return {
        "module.md": module_text,
        "activities.yaml": yaml.safe_dump(
            [{"type": "note", "prompt": activity_prompt}],
            allow_unicode=True,
            sort_keys=False,
        ),
        "vocabulary.yaml": "[]\n",
        "resources.yaml": "[]\n",
    }


def _qg_report(
    *,
    word_count: bool = True,
    plan_sections: bool = True,
    vesum_missing: list[str] | None = None,
) -> dict[str, Any]:
    missing = vesum_missing or []
    gates = {
        "word_count": {
            "passed": word_count,
            "count": 120 if word_count else 90,
            "minimum": 120,
        },
        "plan_sections": {
            "passed": plan_sections,
            "missing_headings": [] if plan_sections else ["Ключові терміни"],
        },
        "vesum_verified": {
            "passed": not missing,
            "missing": missing,
        },
        "vocab_count": {"passed": True},
    }
    gates["passed"] = all(gate["passed"] for gate in gates.values())
    return {"gates": gates}


def _qg_report_from_gates(gates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ordered = dict(gates)
    ordered.setdefault("vocab_count", {"passed": True})
    ordered["passed"] = all(gate.get("passed") is True for gate in ordered.values())
    return {"gates": ordered}


def test_python_qg_seminar_advances_through_rotating_wall(
    tmp_path: Path,
) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path, "folk")
    qg_calls = 0
    corrected_gates: list[str] = []

    def qg_runner() -> dict[str, Any]:
        nonlocal qg_calls
        qg_calls += 1
        module_text = (module_dir / "module.md").read_text(encoding="utf-8")
        if "WORD_FIXED" in module_text:
            return _qg_report_from_gates(
                {
                    "activity_schema": {"passed": True, "violations": []},
                    "word_count": {"passed": True, "count": 120, "minimum": 120},
                    "vesum_verified": {"passed": False, "missing": ["**Дебат"]},
                }
            )
        if "SCHEMA_FIXED" in module_text:
            return _qg_report_from_gates(
                {
                    "activity_schema": {"passed": True, "violations": []},
                    "word_count": {"passed": False, "count": 90, "minimum": 120},
                    "vesum_verified": {"passed": False, "missing": ["**Дебат"]},
                }
            )
        return _qg_report_from_gates(
            {
                "activity_schema": {
                    "passed": False,
                    "violations": [{"message": "self_check must be a list"}],
                }
            }
        )

    def writer_corrector(context: linear_pipeline.CorrectionContext) -> dict[str, str]:
        corrected_gates.append(context.gate)
        if context.gate == "activity_schema":
            return _writer_artifacts(
                "SCHEMA_FIXED\n",
                activity_prompt="schema fixed",
            )
        if context.gate == "word_count":
            return _writer_artifacts("WORD_FIXED\n", activity_prompt="word count fixed")
        raise AssertionError(f"unexpected correction gate: {context.gate}")

    report = linear_pipeline._run_python_qg_with_bounded_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
        max_correction_rounds=2,
    )

    assert qg_calls == 3
    assert corrected_gates == ["activity_schema", "word_count"]
    assert report["gates"]["activity_schema"]["passed"] is True
    assert report["gates"]["word_count"]["passed"] is True
    assert report["gates"]["vesum_verified"]["missing"] == ["**Дебат"]
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "WORD_FIXED\n"
    restored_activities = yaml.safe_load(
        (module_dir / "activities.yaml").read_text(encoding="utf-8")
    )
    assert restored_activities[0]["prompt"] == "word count fixed"

    loop = json.loads(
        (module_dir / "python_qg_correction_loop.json").read_text(encoding="utf-8")
    )
    assert loop["best_round"] == 3
    assert loop["stopped_reason"] == "max_rounds"
    assert loop["min_regression_patience"] == 3
    assert loop["consecutive_regressions"] == 0
    assert [item["violation_count"] for item in loop["rounds"]] == [1, 2, 1]
    assert [item["frontier_gate"] for item in loop["rounds"]] == [
        "activity_schema",
        "word_count",
        "vesum_verified",
    ]
    assert loop["rounds"][1]["frontier"] > loop["rounds"][0]["frontier"]


def test_python_qg_best_round_prefers_frontier_then_violation_count() -> None:
    rounds = [
        {
            "report": _qg_report_from_gates(
                {
                    "activity_schema": {
                        "passed": False,
                        "violations": [{"message": "schema"}],
                    }
                }
            ),
            "violation_count": 1,
        },
        {
            "report": _qg_report_from_gates(
                {
                    "activity_schema": {"passed": True, "violations": []},
                    "word_count": {"passed": False, "violations": ["a", "b"]},
                }
            ),
            "violation_count": 2,
        },
        {
            "report": _qg_report_from_gates(
                {
                    "activity_schema": {"passed": True, "violations": []},
                    "word_count": {"passed": False, "violations": ["a"]},
                }
            ),
            "violation_count": 1,
        },
    ]

    assert linear_pipeline._python_qg_best_round_index(rounds) == 2


def test_python_qg_gate_order_covers_correctable_gate_families() -> None:
    correctable_gates = (
        linear_pipeline.WRITER_CORRECTION_GATES
        | linear_pipeline.DETERMINISTIC_VOCAB_FLOOR_GATES
        | linear_pipeline.REVIEWER_FIX_GATES
        | linear_pipeline.PIPELINE_INSERT_GATES
    )

    missing = correctable_gates - set(linear_pipeline.PYTHON_QG_GATE_ORDER)

    assert sorted(missing) == []


def test_python_qg_gate_order_covers_run_python_qg_content_gates() -> None:
    source = textwrap.dedent(inspect.getsource(linear_pipeline.run_python_qg))
    tree = ast.parse(source)
    recorded_gates = {
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "record"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    }
    emitted_content_gates = recorded_gates | set(linear_pipeline.QUALITY_FIELD_PATTERNS)

    missing = emitted_content_gates - set(linear_pipeline.PYTHON_QG_GATE_ORDER)

    assert sorted(missing) == []


def test_python_qg_frontier_does_not_rank_unmapped_failure_as_pass() -> None:
    report = _qg_report_from_gates(
        {
            "word_count": {"passed": True, "count": 120, "minimum": 120},
            "future_unmapped_gate": {"passed": False, "violations": ["hidden"]},
        }
    )

    assert linear_pipeline._python_qg_frontier(report) == (
        linear_pipeline.PYTHON_QG_UNMAPPED_FAILURE_FRONTIER
    )
    assert linear_pipeline._python_qg_frontier(report) < len(
        linear_pipeline.PYTHON_QG_GATE_ORDER
    )
    assert linear_pipeline._python_qg_frontier_gate(report) == "future_unmapped_gate"


def test_previous_regression_scans_actual_gate_key_union() -> None:
    before = _qg_report_from_gates(
        {
            "word_count": {"passed": False, "count": 90, "minimum": 120},
            "future_unmapped_gate": {"passed": True},
        }
    )
    after = _qg_report_from_gates(
        {
            "word_count": {"passed": True, "count": 120, "minimum": 120},
            "future_unmapped_gate": {"passed": False, "violations": ["hidden"]},
        }
    )

    assert linear_pipeline._previously_passing_regressions(before, after) == [
        "future_unmapped_gate"
    ]


def test_python_qg_plan_reference_regression_restores_non_regressed_round(
    tmp_path: Path,
) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path, "folk")
    qg_calls = 0

    def qg_runner() -> dict[str, Any]:
        nonlocal qg_calls
        qg_calls += 1
        module_text = (module_dir / "module.md").read_text(encoding="utf-8")
        if "WORD_FIXED_BAD_REF" in module_text:
            return _qg_report_from_gates(
                {
                    "word_count": {"passed": True, "count": 120, "minimum": 120},
                    "plan_reference_match": {
                        "passed": False,
                        "missing_plan_references": ["FOLK-1"],
                    },
                }
            )
        return _qg_report_from_gates(
            {
                "word_count": {"passed": False, "count": 90, "minimum": 120},
                "plan_reference_match": {"passed": True, "missing_plan_references": []},
            }
        )

    def writer_corrector(context: linear_pipeline.CorrectionContext) -> dict[str, str]:
        assert context.gate == "word_count"
        return _writer_artifacts(
            "WORD_FIXED_BAD_REF\n",
            activity_prompt="word count fixed but references regressed",
        )

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    assert qg_calls == 3
    assert report["gates"]["word_count"]["passed"] is False
    assert report["gates"]["plan_reference_match"]["passed"] is True
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "STATE0\n"
    loop = json.loads(
        (module_dir / "python_qg_correction_loop.json").read_text(encoding="utf-8")
    )
    assert loop["stopped_reason"] == "previously_passed_regression"
    assert loop["stopped_reason"] != "no_correctable_failure"
    assert loop["best_round"] == 1
    correction = json.loads(
        (module_dir / "python_qg_correction_r1.json").read_text(encoding="utf-8")
    )
    assert correction["rollback_reason"] == "previously_passed_regression"
    assert correction["regressions"] == ["plan_reference_match"]


def test_python_qg_seminar_breaks_immediately_on_pass(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path, "folk")
    corrected_gates: list[str] = []

    def qg_runner() -> dict[str, Any]:
        module_text = (module_dir / "module.md").read_text(encoding="utf-8")
        return _qg_report() if "PASS" in module_text else _qg_report(word_count=False)

    def writer_corrector(context: linear_pipeline.CorrectionContext) -> dict[str, str]:
        corrected_gates.append(context.gate)
        return _writer_artifacts("PASS\n", activity_prompt="passing round")

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    assert report["gates"]["passed"] is True
    assert corrected_gates == ["word_count"]
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "PASS\n"
    loop = json.loads(
        (module_dir / "python_qg_correction_loop.json").read_text(encoding="utf-8")
    )
    assert loop["best_round"] == 2
    assert loop["stopped_reason"] == "pass"
    assert [item["violation_count"] for item in loop["rounds"]] == [1, 0]


def test_python_qg_seminar_regression_restores_previous_snapshot(
    tmp_path: Path,
) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path, "folk")

    def qg_runner() -> dict[str, Any]:
        module_text = (module_dir / "module.md").read_text(encoding="utf-8")
        if "STATE1" in module_text:
            return _qg_report_from_gates(
                {
                    "activity_schema": {
                        "passed": False,
                        "violations": [{"message": "schema regressed"}],
                    },
                    "word_count": {"passed": True, "count": 120, "minimum": 120},
                    "plan_sections": {"passed": True, "missing_headings": []},
                }
            )
        return _qg_report_from_gates(
            {
                "activity_schema": {"passed": True, "violations": []},
                "word_count": {"passed": True, "count": 120, "minimum": 120},
                "plan_sections": {
                    "passed": False,
                    "missing_headings": ["Ключові терміни"],
                },
            }
        )

    def writer_corrector(context: linear_pipeline.CorrectionContext) -> dict[str, str]:
        assert context.gate == "plan_sections"
        return _writer_artifacts("STATE1\n", activity_prompt="dirty round")

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    assert report["gates"]["activity_schema"]["passed"] is True
    assert report["gates"]["plan_sections"]["passed"] is False
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "STATE0\n"
    assert yaml.safe_load((module_dir / "activities.yaml").read_text("utf-8")) == []
    loop = json.loads(
        (module_dir / "python_qg_correction_loop.json").read_text(encoding="utf-8")
    )
    assert loop["stopped_reason"] == "previously_passed_regression"
    assert loop["best_round"] == 1
    correction = json.loads(
        (module_dir / "python_qg_correction_r1.json").read_text(encoding="utf-8")
    )
    assert correction["rollback_reason"] == "previously_passed_regression"
    assert correction["regressions"] == ["activity_schema"]


def test_python_qg_core_uses_legacy_single_correction_path(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path, "a1")
    qg_calls = 0

    def qg_runner() -> dict[str, Any]:
        nonlocal qg_calls
        qg_calls += 1
        module_text = (module_dir / "module.md").read_text(encoding="utf-8")
        return _qg_report() if "PASS" in module_text else _qg_report(word_count=False)

    def writer_corrector(context: linear_pipeline.CorrectionContext) -> dict[str, str]:
        assert context.gate == "word_count"
        return _writer_artifacts("PASS\n", activity_prompt="core pass")

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    assert qg_calls == 2
    assert report["gates"]["passed"] is True
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "PASS\n"
    assert not (module_dir / "python_qg_correction_loop.json").exists()
    assert linear_pipeline.PYTHON_QG_SEMINAR_MAX_CORRECTION_ROUNDS == 8
    assert linear_pipeline.python_qg_max_correction_rounds_for_level("a1") == 1
    assert linear_pipeline.python_qg_max_correction_rounds_for_level("folk") == 8
