from __future__ import annotations

import json
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


def test_python_qg_seminar_restores_best_round_when_later_round_diverges(
    tmp_path: Path,
) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path, "folk")
    qg_calls = 0

    def qg_runner() -> dict[str, Any]:
        nonlocal qg_calls
        qg_calls += 1
        module_text = (module_dir / "module.md").read_text(encoding="utf-8")
        if "STATE2" in module_text:
            return _qg_report(
                vesum_missing=["new-a", "new-b", "new-c", "new-d", "new-e"],
            )
        if "STATE1" in module_text:
            return _qg_report(
                plan_sections=False,
                vesum_missing=["best-a", "best-b"],
            )
        return _qg_report(
            word_count=False,
            plan_sections=False,
            vesum_missing=["old-a", "old-b", "old-c"],
        )

    def writer_corrector(context: linear_pipeline.CorrectionContext) -> dict[str, str]:
        if context.gate == "word_count":
            return _writer_artifacts("STATE1\n", activity_prompt="best round")
        if context.gate == "plan_sections":
            return _writer_artifacts("STATE2\n", activity_prompt="churned round")
        raise AssertionError(f"unexpected correction gate: {context.gate}")

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    assert qg_calls == 3
    assert report["gates"]["vesum_verified"]["missing"] == ["best-a", "best-b"]
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "STATE1\n"
    restored_activities = yaml.safe_load(
        (module_dir / "activities.yaml").read_text(encoding="utf-8")
    )
    assert restored_activities[0]["prompt"] == "best round"

    loop = json.loads(
        (module_dir / "python_qg_correction_loop.json").read_text(encoding="utf-8")
    )
    assert loop["best_round"] == 2
    assert loop["stopped_reason"] == "min_score_regressed"
    assert [item["violation_count"] for item in loop["rounds"]] == [5, 3, 5]


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
            return _qg_report(vesum_missing=["regressed-vesum"])
        return _qg_report(word_count=False)

    def writer_corrector(context: linear_pipeline.CorrectionContext) -> dict[str, str]:
        assert context.gate == "word_count"
        return _writer_artifacts("STATE1\n", activity_prompt="dirty round")

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    assert report["gates"]["word_count"]["passed"] is False
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "STATE0\n"
    assert yaml.safe_load((module_dir / "activities.yaml").read_text("utf-8")) == []
    loop = json.loads(
        (module_dir / "python_qg_correction_loop.json").read_text(encoding="utf-8")
    )
    assert loop["stopped_reason"] == "previously_passed_regression"
    assert loop["best_round"] == 1


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
    assert linear_pipeline.python_qg_max_correction_rounds_for_level("a1") == 1
    assert linear_pipeline.python_qg_max_correction_rounds_for_level("folk") == 4
