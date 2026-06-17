from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.build import linear_pipeline
from scripts.common.thresholds import QG_DIMS


def _module_dir(tmp_path: Path, module_text: str = "# Lesson\n\nAnchor sentence.\n") -> Path:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(module_text, encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def _plan_path(tmp_path: Path, level: str = "folk") -> Path:
    path = tmp_path / "plan.yaml"
    path.write_text(
        f"level: {level}\nsequence: 1\nslug: sample\n",
        encoding="utf-8",
    )
    return path


def _llm_report(
    *,
    level: str = "folk",
    profile: str | None = None,
    pedagogical: float = 9.0,
    scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    per_dim: dict[str, dict[str, Any]] = {}
    for dim in QG_DIMS:
        score = scores.get(dim, 9.0) if scores is not None else (pedagogical if dim == "pedagogical" else 9.0)
        per_dim[dim] = {
            "score": score,
            "evidence": '"Anchor sentence."',
            "evidence_quotes": ["Anchor sentence."],
            "verdict": "PASS" if score >= 8.0 else "REVISE",
        }
    return linear_pipeline.aggregate_llm_review(per_dim, level, profile=profile)


def _python_qg_pass() -> dict[str, Any]:
    return {"gates": {"passed": True}}


def test_llm_qg_needs_subjective_fix_selects_terminal_dims_only() -> None:
    seminar_report = _llm_report(
        profile="seminar",
        scores={
            "engagement": 7.2,
            "beauty": 7.5,
            "decolonization": 8.5,
            "naturalness": 7.0,
        },
    )
    assert linear_pipeline._llm_qg_needs_subjective_fix(seminar_report, "seminar") == (
        "decolonization",
        "engagement",
        "beauty",
    )

    decolonization_report = _llm_report(
        profile="seminar",
        scores={"decolonization": 8.5},
    )
    assert linear_pipeline._llm_qg_needs_subjective_fix(decolonization_report, "seminar") == (
        "decolonization",
    )
    assert linear_pipeline._llm_qg_needs_subjective_fix(seminar_report, "core") == ()


def test_llm_qg_best_round_uses_highest_aggregate_min_not_last(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path)
    reports = [
        _llm_report(pedagogical=6.0),
        _llm_report(pedagogical=7.0),
        _llm_report(pedagogical=6.0),
    ]

    def llm_runner(**_: Any) -> dict[str, Any]:
        return reports.pop(0)

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        return (
            "<fixes><fix><insert_after>Anchor sentence.</insert_after>"
            "<text>\n\nSelf-check prompt.</text></fix></fixes>"
        )

    result = linear_pipeline.run_llm_qg_with_corrections(
        plan={"level": "folk", "sequence": 1, "slug": "sample"},
        plan_path=plan_path,
        plan_content="plan",
        module_dir=module_dir,
        writer="codex-tools",
        llm_qg_runner=llm_runner,
        python_qg_runner=_python_qg_pass,
        corrector=corrector,
        max_rounds=3,
    )

    assert result["aggregate"]["min_score"] == 7.0
    loop = json.loads((module_dir / "llm_qg_correction_loop.json").read_text(encoding="utf-8"))
    assert loop["stopped_reason"] == "min_score_regressed"
    assert loop["best_round"] == 2
    module_text = (module_dir / "module.md").read_text(encoding="utf-8")
    assert module_text.count("Self-check prompt.") == 1


def test_llm_qg_insert_after_fix_is_reviewed_on_next_round(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path)
    seen_texts: list[str] = []

    def llm_runner(**_: Any) -> dict[str, Any]:
        text = (module_dir / "module.md").read_text(encoding="utf-8")
        seen_texts.append(text)
        return _llm_report(pedagogical=8.0 if "Inserted scaffold." in text else 6.0)

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        return (
            "<fixes><fix><insert_after>Anchor sentence.</insert_after>"
            "<text>\n\nInserted scaffold.</text></fix></fixes>"
        )

    result = linear_pipeline.run_llm_qg_with_corrections(
        plan={"level": "folk", "sequence": 1, "slug": "sample"},
        plan_path=plan_path,
        plan_content="plan",
        module_dir=module_dir,
        writer="codex-tools",
        llm_qg_runner=llm_runner,
        python_qg_runner=_python_qg_pass,
        corrector=corrector,
        max_rounds=3,
    )

    assert result["aggregate"]["verdict"] == "PASS"
    assert len(seen_texts) == 2
    assert "Inserted scaffold." in seen_texts[1]
    assert "Inserted scaffold." in (module_dir / "module.md").read_text(encoding="utf-8")
    assert json.loads((module_dir / "python_qg.json").read_text(encoding="utf-8")) == _python_qg_pass()


def test_llm_qg_loop_renders_one_prompt_for_multiple_terminal_dims(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path)
    prompts: list[str] = []
    gate_reports: list[dict[str, Any]] = []
    reports = [
        _llm_report(profile="seminar", scores={"engagement": 7.2, "beauty": 7.0}),
        _llm_report(profile="seminar", scores={"engagement": 8.0, "beauty": 8.0}),
    ]

    def llm_runner(**_: Any) -> dict[str, Any]:
        return reports.pop(0)

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        prompts.append(context.prompt)
        gate_reports.append(dict(context.gate_report))
        return (
            "<fixes><fix><find>Anchor sentence.</find>"
            "<replace>Anchor sentence, now vivid and memorable.</replace></fix></fixes>"
        )

    result = linear_pipeline.run_llm_qg_with_corrections(
        plan={"level": "folk", "sequence": 1, "slug": "sample"},
        plan_path=plan_path,
        plan_content="plan",
        module_dir=module_dir,
        writer="codex-tools",
        llm_qg_runner=llm_runner,
        profile="seminar",
        python_qg_runner=_python_qg_pass,
        corrector=corrector,
        max_rounds=3,
    )

    assert result["aggregate"]["verdict"] == "PASS"
    assert len(prompts) == 1
    assert "Failing terminal dimensions: engagement, beauty" in prompts[0]
    assert "engagement:" in prompts[0]
    assert "beauty:" in prompts[0]
    assert gate_reports[0]["failing_terminal_dims"] == ["engagement", "beauty"]


def test_llm_qg_python_qg_failure_discards_insert(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path)

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        return (
            "<fixes><fix><insert_after>Anchor sentence.</insert_after>"
            "<text>\n\nInserted scaffold.</text></fix></fixes>"
        )

    result = linear_pipeline.run_llm_qg_with_corrections(
        plan={"level": "folk", "sequence": 1, "slug": "sample"},
        plan_path=plan_path,
        plan_content="plan",
        module_dir=module_dir,
        writer="codex-tools",
        llm_qg_runner=lambda **_: _llm_report(pedagogical=6.0),
        python_qg_runner=lambda: {"gates": {"passed": False}},
        corrector=corrector,
        max_rounds=3,
    )

    assert result["aggregate"]["min_score"] == 6.0
    assert "Inserted scaffold." not in (module_dir / "module.md").read_text(encoding="utf-8")


def test_llm_qg_core_profile_terminal_failures_are_noop(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path, level="a1")
    review_calls = 0

    def llm_runner(**_: Any) -> dict[str, Any]:
        nonlocal review_calls
        review_calls += 1
        return _llm_report(
            level="a1",
            profile="core",
            scores={"pedagogical": 4.0, "engagement": 4.0, "beauty": 4.0},
        )

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        raise AssertionError("core profile must not call the corrector")

    def python_qg_runner() -> dict[str, Any]:
        raise AssertionError("core profile must not re-run python_qg")

    result = linear_pipeline.run_llm_qg_with_corrections(
        plan={"level": "a1", "sequence": 1, "slug": "sample"},
        plan_path=plan_path,
        plan_content="plan",
        module_dir=module_dir,
        writer="codex-tools",
        llm_qg_runner=llm_runner,
        profile="core",
        python_qg_runner=python_qg_runner,
        corrector=corrector,
        max_rounds=3,
    )

    assert review_calls == 1
    assert result["aggregate"]["min_score"] == 4.0
    loop = json.loads((module_dir / "llm_qg_correction_loop.json").read_text(encoding="utf-8"))
    assert loop["stopped_reason"] == "no_terminal_failure"
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "# Lesson\n\nAnchor sentence.\n"


@pytest.mark.parametrize(
    ("level", "expected"),
    [("folk", 3), ("hist", 3), ("a1", 1), ("b2", 1)],
)
def test_llm_qg_round_budget_seminar_vs_core(level: str, expected: int) -> None:
    assert linear_pipeline.llm_qg_max_rounds_for_level(level) == expected


def test_subjective_correction_context_preserves_manifest_string(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    llm_qg = _llm_report(pedagogical=6.0)

    context = linear_pipeline.subjective_correction_context(
        plan={"level": "folk", "sequence": 1, "slug": "sample"},
        llm_qg=llm_qg,
        failing_dims=("pedagogical",),
        module_text=(module_dir / "module.md").read_text(encoding="utf-8"),
        plan_content="plan",
        wiki_manifest='{"sources": [{"id": "S1"}]}',
        obligation_checklist={"items": []},
    )

    assert context["WIKI_MANIFEST"] == '{"sources": [{"id": "S1"}]}'
    assert context["OBLIGATION_CHECKLIST"] == "items: []"


def test_apply_subjective_fixes_accepts_replace_and_insert(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path, "# Lesson\n\nFlat sentence.\n")
    plan_path = _plan_path(tmp_path)

    result = linear_pipeline._apply_subjective_fixes(
        response=(
            "<fixes>"
            "<fix><find>Flat sentence.</find><replace>Vivid sentence.</replace></fix>"
            "<fix><insert_after>Vivid sentence.</insert_after><text>\n\nInserted detail.</text></fix>"
            "</fixes>"
        ),
        module_dir=module_dir,
        plan_path=plan_path,
    )

    assert result["applied"] is True
    assert result["rejected_fixes"] == []
    module_text = (module_dir / "module.md").read_text(encoding="utf-8")
    assert "Flat sentence." not in module_text
    assert "Vivid sentence.\n\nInserted detail." in module_text


def test_apply_subjective_fixes_rejects_oversize_replace(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path, "# Lesson\n\nFlat sentence.\n")
    plan_path = _plan_path(tmp_path)
    oversize_replace = "x" * 241

    result = linear_pipeline._apply_subjective_fixes(
        response=(
            "<fixes><fix><find>Flat sentence.</find>"
            f"<replace>{oversize_replace}</replace></fix></fixes>"
        ),
        module_dir=module_dir,
        plan_path=plan_path,
    )

    assert result["applied"] is False
    assert result["accepted_fixes"] == []
    assert result["rejected_fixes"] == [{"find": "Flat sentence.", "replace": oversize_replace}]
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "# Lesson\n\nFlat sentence.\n"
