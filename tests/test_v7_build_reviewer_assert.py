from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.build import linear_pipeline, v7_build


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
