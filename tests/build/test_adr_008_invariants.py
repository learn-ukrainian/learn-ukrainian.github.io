from __future__ import annotations

from pathlib import Path

from scripts.build import linear_pipeline


def _module_dir(tmp_path: Path) -> Path:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(
        "## Діалоги\n\nПожалуйста, read this line.\n",
        encoding="utf-8",
    )
    return module_dir


def _report(*failed: str) -> dict:
    gates = {
        gate: {"passed": gate not in failed}
        for gate in linear_pipeline.PYTHON_QG_GATE_ORDER
    }
    gates["previously_passed_regression"] = {"passed": True, "regressions": []}
    gates["mdx_render"] = {"passed": None, "message": "Run after publish stage"}
    gates["passed"] = not failed
    return {
        "module": "a1-020",
        "level": "A1",
        "slug": "my-morning",
        "pipeline": "linear-phase-4",
        "gates": gates,
    }


def test_no_writer_rewrite_in_correction() -> None:
    template = (
        linear_pipeline.PROJECT_ROOT
        / "scripts"
        / "build"
        / "phases"
        / "linear-writer-correction.md"
    ).read_text(encoding="utf-8")

    assert "modify in place via append/insert, never re-author or regenerate" in template
    for phrase in ("regenerate", "rewrite", "produce again", "start over"):
        assert phrase in template


def test_correction_fully_revalidates(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = tmp_path / "plan.yaml"
    validation_runs: list[list[str]] = []
    reports = [_report("word_count"), _report()]

    def qg_runner() -> dict:
        validation_runs.append(list(linear_pipeline.PYTHON_QG_GATE_ORDER))
        return reports.pop(0)

    def writer_corrector(context: linear_pipeline.CorrectionContext) -> None:
        assert context.gate == "word_count"

    result = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    assert result["gates"]["passed"] is True
    assert validation_runs[1] == list(linear_pipeline.PYTHON_QG_GATE_ORDER)


def test_correction_does_not_regress_passing_gates(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = tmp_path / "plan.yaml"
    reports = [_report("word_count"), _report("russianisms_clean")]

    def qg_runner() -> dict:
        return reports.pop(0)

    result = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=lambda _context: None,
    )

    regression = result["gates"]["previously_passed_regression"]
    assert regression["passed"] is False
    assert regression["regressions"] == ["russianisms_clean"]
    assert result["gates"]["passed"] is False


def test_pipeline_proposes_dictionary_candidates(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = tmp_path / "plan.yaml"
    first = _report("russianisms_clean")
    first["gates"]["russianisms_clean"] = {
        "passed": False,
        "hits": [r"\bпожалуйста\b"],
        "detections": [{"pattern": r"\bпожалуйста\b", "text": "пожалуйста"}],
    }
    reports = [first, _report()]
    events: list[str] = []

    def qg_runner() -> dict:
        return reports.pop(0)

    def dictionary_lookup(gate: str, original: str) -> list[dict[str, str]]:
        events.append("lookup")
        assert gate == "russianisms_clean"
        assert original == "пожалуйста"
        return [{"replacement": "будь ласка", "source": "mock Антоненко-Давидович"}]

    def reviewer_corrector(context: linear_pipeline.CorrectionContext) -> str:
        events.append("reviewer")
        assert context.candidates
        assert context.candidates[0].replacement == "будь ласка"
        assert "Pipeline-proposed candidates" in context.prompt
        assert "SELECT from these candidates" in context.prompt
        return (
            "<fixes>\n"
            '- find: "Пожалуйста"\n'
            '  replace: "Будь ласка"\n'
            "</fixes>"
        )

    result = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        reviewer_corrector=reviewer_corrector,
        dictionary_lookup_fn=dictionary_lookup,
    )

    assert events == ["lookup", "reviewer"]
    assert result["gates"]["passed"] is True


def test_one_attempt_per_gate(tmp_path: Path) -> None:
    module_dir = _module_dir(tmp_path)
    plan_path = tmp_path / "plan.yaml"
    attempts = 0

    def qg_runner() -> dict:
        return _report("word_count")

    def writer_corrector(_context: linear_pipeline.CorrectionContext) -> None:
        nonlocal attempts
        attempts += 1

    result = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        plan_path,
        qg_runner=qg_runner,
        writer_corrector=writer_corrector,
    )

    assert attempts == 1
    assert result["gates"]["correction_terminal"]["gate"] == "word_count"
