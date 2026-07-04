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
    pedagogical: float,
    naturalness: float = 9.0,
    naturalness_findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    per_dim: dict[str, dict[str, Any]] = {}
    for dim in QG_DIMS:
        if dim == "pedagogical":
            score = pedagogical
        elif dim == "naturalness":
            score = naturalness
        else:
            score = 9.0
        entry: dict[str, Any] = {
            "score": score,
            "evidence": '"Anchor sentence."',
            "verdict": "PASS" if score >= 8.0 else "REVISE",
        }
        if dim == "naturalness" and naturalness_findings:
            entry["findings"] = naturalness_findings
            entry["issue_ids"] = [
                finding["issue_id"]
                for finding in naturalness_findings
                if isinstance(finding.get("issue_id"), str)
            ]
        per_dim[dim] = entry
    return linear_pipeline.aggregate_llm_review(per_dim, level)


def _python_qg_pass() -> dict[str, Any]:
    return {"gates": {"passed": True}}


def test_llm_qg_grammar_findings_do_not_coerce_explicit_non_grammar_issue_ids() -> None:
    llm_qg = {
        "dimensions": {
            "naturalness": {
                "issue_ids": ["UKRAINIAN_GRAMMAR_CALQUE"],
                "findings": [
                    {
                        "issue_id": "CONCEPTUAL_ERROR",
                        "quote": "This is not a grammar finding.",
                    },
                    {
                        "quote": "This inherits the dimension-level grammar issue.",
                    },
                ],
            }
        },
        "aggregate": {"failing_dims": ["naturalness"]},
    }

    findings = linear_pipeline._llm_qg_fixable_grammar_findings(llm_qg)

    assert [finding["quote"] for finding in findings] == [
        "This inherits the dimension-level grammar issue."
    ]
    assert findings[0]["issue_id"] == "UKRAINIAN_GRAMMAR_CALQUE"


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
    module_text = (module_dir / "module.md").read_text(encoding="utf-8")
    assert module_text.count("Self-check prompt.") == 1


def test_llm_qg_min_score_drop_within_noise_tolerance_does_not_stop(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path)
    reports = [
        _llm_report(pedagogical=7.0),
        _llm_report(pedagogical=6.5),
        _llm_report(pedagogical=6.6),
    ]

    def llm_runner(**_: Any) -> dict[str, Any]:
        return reports.pop(0)

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        round_id = len(reports)
        return (
            "<fixes><fix><insert_after>Anchor sentence.</insert_after>"
            f"<text>\n\nTolerance scaffold {round_id}.</text></fix></fixes>"
        )

    linear_pipeline.run_llm_qg_with_corrections(
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

    loop = json.loads((module_dir / "llm_qg_correction_loop.json").read_text(encoding="utf-8"))
    assert loop["stopped_reason"] == "max_rounds"
    assert [round_summary["round"] for round_summary in loop["rounds"]] == [1, 2, 3]


def test_llm_qg_min_score_drop_beyond_noise_tolerance_stops(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path)
    reports = [
        _llm_report(pedagogical=7.0),
        _llm_report(pedagogical=6.4),
    ]

    def llm_runner(**_: Any) -> dict[str, Any]:
        return reports.pop(0)

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        return (
            "<fixes><fix><insert_after>Anchor sentence.</insert_after>"
            "<text>\n\nRegression scaffold.</text></fix></fixes>"
        )

    linear_pipeline.run_llm_qg_with_corrections(
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

    loop = json.loads((module_dir / "llm_qg_correction_loop.json").read_text(encoding="utf-8"))
    assert loop["stopped_reason"] == "min_score_regressed"
    assert [round_summary["round"] for round_summary in loop["rounds"]] == [1, 2]


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


def test_llm_qg_python_qg_regression_discards_insert(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path)
    python_reports = [
        {"gates": {"passed": True, "activity_schema": {"passed": True}}},
        {"gates": {"passed": False, "activity_schema": {"passed": False}}},
    ]

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
        python_qg_runner=lambda: python_reports.pop(0),
        corrector=corrector,
        max_rounds=3,
    )

    assert result["aggregate"]["min_score"] == 6.0
    assert "Inserted scaffold." not in (module_dir / "module.md").read_text(encoding="utf-8")
    loop = json.loads((module_dir / "llm_qg_correction_loop.json").read_text(encoding="utf-8"))
    assert loop["stopped_reason"] == "python_qg_regressed"


def test_llm_qg_preexisting_python_qg_failure_does_not_discard_insert(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path)
    python_reports = [
        {"gates": {"passed": False, "plan_sections": {"passed": False}}},
        {"gates": {"passed": False, "plan_sections": {"passed": False}}},
        _python_qg_pass(),
        _python_qg_pass(),
    ]

    def llm_runner(**_: Any) -> dict[str, Any]:
        module_text = (module_dir / "module.md").read_text(encoding="utf-8")
        return _llm_report(pedagogical=8.0 if "Inserted scaffold." in module_text else 6.0)

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
        python_qg_runner=lambda: python_reports.pop(0),
        corrector=corrector,
        max_rounds=3,
    )

    assert result["aggregate"]["verdict"] == "PASS"
    assert "Inserted scaffold." in (module_dir / "module.md").read_text(encoding="utf-8")
    loop = json.loads((module_dir / "llm_qg_correction_loop.json").read_text(encoding="utf-8"))
    assert loop["corrections"][0]["python_qg_regressions"] == []
    assert loop["corrections"][0]["python_qg_frontier_regressed"] is False


def test_llm_qg_grammar_calque_correction_updates_patchable_artifacts(tmp_path: Path) -> None:
    bad = "У застереженні зміст інший: будь обережний, щоб небажаний результат не стався."
    good = "У застереженні зміст інший: є конкретний ризик, і мовець попереджає про нього."
    module_dir = _module_dir(tmp_path, f"# Lesson\n\n{bad}\n")
    (module_dir / "activities.yaml").write_text(
        "\n".join(
            [
                "version: '1.0'",
                "module: sample",
                "level: b1",
                "inline:",
                "  - id: act-1",
                "    type: cloze",
                f'    prompt: "{bad}"',
                "workbook: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text(
        f'- lemma: застереження\n  translation: warning\n  pos: noun\n  usage: "{bad}"\n',
        encoding="utf-8",
    )
    (module_dir / "resources.yaml").write_text(
        f'- title: Reference\n  role: reference\n  note: "{bad}"\n',
        encoding="utf-8",
    )
    plan_path = _plan_path(tmp_path, level="b1")
    finding = {
        "issue_id": "UKRAINIAN_GRAMMAR_CALQUE",
        "quote": bad,
        "replacement": good,
        "severity": "high",
        "explanation": "Learner-facing Ukrainian uses an unnatural grammar calque.",
    }
    review_calls = 0
    correction_contexts: list[linear_pipeline.CorrectionContext] = []

    def llm_runner(**_: Any) -> dict[str, Any]:
        nonlocal review_calls
        review_calls += 1
        if review_calls == 1:
            return _llm_report(
                level="b1",
                pedagogical=9.0,
                naturalness=8.4,
                naturalness_findings=[finding],
            )
        return _llm_report(level="b1", pedagogical=9.0, naturalness=9.2)

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        correction_contexts.append(context)
        assert context.gate == "llm_qg_grammar_calque"
        assert context.candidates[0].original == bad
        assert context.candidates[0].replacement == good
        return f"<fixes><fix><find>{bad}</find><replace>{good}</replace></fix></fixes>"

    result = linear_pipeline.run_llm_qg_with_corrections(
        plan={"level": "b1", "sequence": 1, "slug": "sample"},
        plan_path=plan_path,
        plan_content="plan",
        module_dir=module_dir,
        writer="codex-tools",
        llm_qg_runner=llm_runner,
        python_qg_runner=_python_qg_pass,
        corrector=corrector,
        max_rounds=2,
    )

    assert result["aggregate"]["verdict"] == "PASS"
    assert review_calls == 2
    assert len(correction_contexts) == 1
    for artifact in ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml"):
        text = (module_dir / artifact).read_text(encoding="utf-8")
        assert bad not in text
        assert good in text
    loop = json.loads((module_dir / "llm_qg_correction_loop.json").read_text(encoding="utf-8"))
    assert loop["stopped_reason"] == "pass"
    assert loop["corrections"][0]["gate"] == "llm_qg_grammar_calque"


def test_llm_qg_nonfixable_naturalness_failure_stops_without_guessing(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path, level="b1")

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        raise AssertionError("non-fixable LLM-QG failures must not call the corrector")

    def python_qg_runner() -> dict[str, Any]:
        raise AssertionError("non-fixable LLM-QG failures must not re-run python_qg")

    result = linear_pipeline.run_llm_qg_with_corrections(
        plan={"level": "b1", "sequence": 1, "slug": "sample"},
        plan_path=plan_path,
        plan_content="plan",
        module_dir=module_dir,
        writer="codex-tools",
        llm_qg_runner=lambda **_: _llm_report(level="b1", pedagogical=9.0, naturalness=7.0),
        python_qg_runner=python_qg_runner,
        corrector=corrector,
        max_rounds=2,
    )

    assert result["aggregate"]["min_score"] == 7.0
    loop = json.loads((module_dir / "llm_qg_correction_loop.json").read_text(encoding="utf-8"))
    assert loop["stopped_reason"] == "no_fixable_llm_qg_failure"
    assert loop["corrections"] == []


def test_llm_qg_explicit_max_rounds_one_is_noop(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = _plan_path(tmp_path, level="a1")
    review_calls = 0

    def llm_runner(**_: Any) -> dict[str, Any]:
        nonlocal review_calls
        review_calls += 1
        return _llm_report(level="a1", pedagogical=4.0)

    def corrector(context: linear_pipeline.CorrectionContext) -> str:
        raise AssertionError("core max_rounds=1 must not call the corrector")

    def python_qg_runner() -> dict[str, Any]:
        raise AssertionError("core max_rounds=1 must not re-run python_qg")

    result = linear_pipeline.run_llm_qg_with_corrections(
        plan={"level": "a1", "sequence": 1, "slug": "sample"},
        plan_path=plan_path,
        plan_content="plan",
        module_dir=module_dir,
        writer="codex-tools",
        llm_qg_runner=llm_runner,
        python_qg_runner=python_qg_runner,
        corrector=corrector,
        max_rounds=1,
    )

    assert review_calls == 1
    assert result["aggregate"]["min_score"] == 4.0
    assert (module_dir / "module.md").read_text(encoding="utf-8") == "# Lesson\n\nAnchor sentence.\n"


@pytest.mark.parametrize(
    ("level", "expected"),
    [("folk", 3), ("hist", 3), ("a1", 2), ("b2", 2)],
)
def test_llm_qg_round_budget_seminar_vs_core(level: str, expected: int) -> None:
    assert linear_pipeline.llm_qg_max_rounds_for_level(level) == expected


def test_pedagogical_correction_context_preserves_manifest_string(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    llm_qg = _llm_report(pedagogical=6.0)

    context = linear_pipeline.pedagogical_correction_context(
        plan={"level": "folk", "sequence": 1, "slug": "sample"},
        llm_qg=llm_qg,
        module_text=(module_dir / "module.md").read_text(encoding="utf-8"),
        plan_content="plan",
        wiki_manifest='{"sources": [{"id": "S1"}]}',
        obligation_checklist={"items": []},
    )

    assert context["WIKI_MANIFEST"] == '{"sources": [{"id": "S1"}]}'
    assert context["OBLIGATION_CHECKLIST"] == "items: []"
