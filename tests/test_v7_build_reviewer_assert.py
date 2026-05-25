from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.build import linear_pipeline, v7_build


def test_reviewer_override_normalizes_alias():
    args = v7_build.parse_args(
        ["b1", "genitive-nuances", "--writer", "codex-tools", "--reviewer", "cursor"]
    )

    assert v7_build._reviewer_for_writer(args.writer, args.reviewer) == "cursor-tools"


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
