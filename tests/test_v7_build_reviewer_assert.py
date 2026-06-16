import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from scripts.build import linear_pipeline, v7_build
from scripts.common.thresholds import QG_DIMS


def test_reviewer_override_normalizes_alias():
    args = v7_build.parse_args(
        ["b1", "genitive-nuances", "--writer", "codex-tools", "--reviewer", "cursor"]
    )

    assert v7_build._reviewer_for_writer(args.writer, args.reviewer) == "cursor-tools"


def test_seminar_llm_qg_routes_away_from_gemini_reviewer():
    assert (
        v7_build._llm_qg_reviewer_override_for_level(
            level="folk",
            writer="codex-tools",
            reviewer_override=None,
        )
        == "claude-tools"
    )
    assert (
        v7_build._llm_qg_reviewer_override_for_level(
            level="folk",
            writer="claude-tools",
            reviewer_override=None,
        )
        == "codex-tools"
    )
    assert (
        v7_build._llm_qg_reviewer_override_for_level(
            level="folk",
            writer="codex-tools",
            reviewer_override="gemini",
        )
        == "claude-tools"
    )
    assert (
        v7_build._llm_qg_reviewer_override_for_level(
            level="b1",
            writer="codex-tools",
            reviewer_override="gemini",
        )
        == "gemini-tools"
    )


def test_generated_content_includes_writer_preemit_audit_lines(tmp_path: Path):
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "writer_output.raw.md").write_text(
        "\n".join(
            [
                "<implementation_map_audit>manifest_obligations=8 covered_in_map=8 missing=[]</implementation_map_audit>",
                "<bad_form_audit>italic_bad_form_patterns_found=0 converted_to_marker=0 remaining=0</bad_form_audit>",
                "<activity_split_audit>",
                "level=B1 inline_n=6 workbook_n=11 inline_range=[5,7] workbook_range=[11,15] split_valid=true",
                "</activity_split_audit>",
                "````markdown file=module.md",
                "# Lesson",
                "````",
            ]
        ),
        encoding="utf-8",
    )
    for artifact in linear_pipeline.WRITER_ARTIFACTS:
        (module_dir / artifact).write_text(f"{artifact} body\n", encoding="utf-8")

    generated = v7_build._generated_content(module_dir)

    assert "## writer_output.raw.md pre-emit audit lines" in generated
    assert "<implementation_map_audit>" in generated
    assert "<bad_form_audit>" in generated
    assert "<activity_split_audit>" in generated
    assert "level=B1 inline_n=6" in generated
    assert generated.index("<activity_split_audit>") < generated.index("## module.md")


def test_writer_preemit_audit_context_extracts_all_three_tags(tmp_path: Path):
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "writer_output.raw.md").write_text(
        "\n".join(
            [
                "<implementation_map_audit>manifest_obligations=3 covered_in_map=3 missing=[]</implementation_map_audit>",
                "<bad_form_audit>italic_bad_form_patterns_found=1 converted_to_marker=1 remaining=0</bad_form_audit>",
                "<activity_split_audit>level=B1 inline_n=5 workbook_n=11 inline_range=[5,7] workbook_range=[11,15] split_valid=true</activity_split_audit>",
            ]
        ),
        encoding="utf-8",
    )

    context = v7_build._writer_preemit_audit_context(module_dir)

    assert "## writer_output.raw.md pre-emit audit lines" in context
    assert context.count("<implementation_map_audit>") == 1
    assert context.count("<bad_form_audit>") == 1
    assert context.count("<activity_split_audit>") == 1


def test_writer_preemit_audit_context_missing_tags_returns_empty(tmp_path: Path):
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "writer_output.raw.md").write_text("plain writer output\n", encoding="utf-8")

    assert v7_build._writer_preemit_audit_context(module_dir) == ""
    assert v7_build._writer_preemit_audit_context(tmp_path / "missing") == ""


def test_writer_preemit_audit_context_malformed_tags_do_not_match(tmp_path: Path):
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "writer_output.raw.md").write_text(
        "\n".join(
            [
                "<implementation_map_audit>manifest_obligations=3",
                "<bad_form_audit>remaining=0</activity_split_audit>",
                "<activity_split_audit level=B1 split_valid=true>",
            ]
        ),
        encoding="utf-8",
    )

    assert v7_build._writer_preemit_audit_context(module_dir) == ""


def test_reviewer_assert_v7_build(tmp_path: Path):
    """v7_build must assert if writer and reviewer use the same model."""
    plan = {"slug": "test-slug", "level": "a1"}
    plan_content = "content"
    module_dir = tmp_path / "module"
    module_dir.mkdir()

    # Contrive same-model situation
    # We can patch linear_pipeline.WRITER_DEFAULTS and REVIEWER_DEFAULTS
    contrived_writer_defaults = {"claude-tools": {"model": "same-model", "effort": "high"}}
    contrived_reviewer_defaults = {"gemini-tools": {"model": "same-model", "effort": "high"}}

    with patch.dict(linear_pipeline.WRITER_DEFAULTS, contrived_writer_defaults, clear=False):
        with patch.dict(linear_pipeline.REVIEWER_DEFAULTS, contrived_reviewer_defaults, clear=False):
            with patch("scripts.build.v7_build._reviewer_for_writer", return_value="gemini-tools"):
                with pytest.raises(AssertionError, match="same-model self-review forbidden"):
                    v7_build._run_llm_qg(
                        plan=plan, plan_content=plan_content, module_dir=module_dir, writer="claude-tools"
                    )

                with pytest.raises(AssertionError, match="same-model self-review forbidden"):
                    v7_build._run_wiki_coverage_review(
                        plan=plan,
                        plan_content=plan_content,
                        module_dir=module_dir,
                        writer="claude-tools",
                        wiki_manifest={},
                        wiki_coverage_gate={},
                    )


def _llm_qg_response(dim: str) -> str:
    return json.dumps(
        {
            "score": 8.5,
            "evidence": f'"{dim} evidence quote"',
            "verdict": "PASS",
        }
    )


def _patch_llm_qg_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "render_review_prompt",
        lambda *_args, **_kwargs: f"prompt::{_args[3]}",
    )
    monkeypatch.setattr(v7_build, "_generated_content", lambda _module_dir: "generated")


def test_llm_qg_retries_empty_dimension_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_qg_prompt(monkeypatch)
    first_dim = QG_DIMS[0]
    calls: list[str] = []

    def invoke(_agent: str, prompt: str, **_kwargs: object) -> SimpleNamespace:
        dim = prompt.split("::", 1)[1]
        calls.append(dim)
        if dim == first_dim and calls.count(dim) == 1:
            return SimpleNamespace(response="")
        return SimpleNamespace(response=_llm_qg_response(dim))

    monkeypatch.setattr("scripts.agent_runtime.runner.invoke", invoke)

    module_dir = tmp_path / "module"
    module_dir.mkdir()
    report = v7_build._run_llm_qg(
        plan={"slug": "test-slug", "level": "a1"},
        plan_content="plan",
        module_dir=module_dir,
        writer="claude-tools",
        reviewer_override="codex-tools",
    )

    assert calls.count(first_dim) == 2
    assert set(report["dimensions"]) == set(QG_DIMS)
    assert (module_dir / f"llm-qg-{first_dim}-response.raw.md").read_text(
        encoding="utf-8"
    ).strip()


def test_llm_qg_resumes_current_successful_dimension_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_qg_prompt(monkeypatch)
    resumed_dim = QG_DIMS[0]
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / f"llm-qg-{resumed_dim}-prompt.md").write_text(
        f"prompt::{resumed_dim}",
        encoding="utf-8",
    )
    (module_dir / f"llm-qg-{resumed_dim}-response.raw.md").write_text(
        _llm_qg_response(resumed_dim),
        encoding="utf-8",
    )
    calls: list[str] = []

    def invoke(_agent: str, prompt: str, **_kwargs: object) -> SimpleNamespace:
        dim = prompt.split("::", 1)[1]
        calls.append(dim)
        return SimpleNamespace(response=_llm_qg_response(dim))

    monkeypatch.setattr("scripts.agent_runtime.runner.invoke", invoke)

    report = v7_build._run_llm_qg(
        plan={"slug": "test-slug", "level": "a1"},
        plan_content="plan",
        module_dir=module_dir,
        writer="claude-tools",
        reviewer_override="codex-tools",
    )

    assert resumed_dim not in calls
    assert set(report["dimensions"]) == set(QG_DIMS)


def test_llm_qg_reports_malformed_dimension_response_clearly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_llm_qg_prompt(monkeypatch)

    def invoke(_agent: str, _prompt: str, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(response="not structured output")

    monkeypatch.setattr("scripts.agent_runtime.runner.invoke", invoke)

    module_dir = tmp_path / "module"
    module_dir.mkdir()
    with pytest.raises(linear_pipeline.LinearPipelineError) as exc_info:
        v7_build._run_llm_qg(
            plan={"slug": "test-slug", "level": "a1"},
            plan_content="plan",
            module_dir=module_dir,
            writer="claude-tools",
            reviewer_override="codex-tools",
        )

    message = str(exc_info.value)
    assert f"LLM QG {QG_DIMS[0]} failed after" in message
    assert "malformed backend response" in message
    assert "response.raw.md" in message
