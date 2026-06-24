from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build import linear_pipeline, v7_build


def _artifacts_with_unnamed_module_fence() -> dict[str, str]:
    return {
        "module.md": "## Intro\n\n```\nunnamed fence allowed in iterative module body\n```\n",
        "activities.yaml": "[]\n",
        "vocabulary.yaml": "[]\n",
        "resources.yaml": "[]\n",
    }


def _write_artifacts(module_dir: Path, artifacts: dict[str, str]) -> None:
    for name, content in artifacts.items():
        (module_dir / name).write_text(content, encoding="utf-8")


def test_iterative_resume_reads_artifacts_without_single_shot_fence_parse(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts_with_unnamed_module_fence()
    _write_artifacts(tmp_path, artifacts)
    (tmp_path / "iterative_writer_sidecar.json").write_text(
        '{"s1": {"line_start": 1, "line_end": 4}}\n',
        encoding="utf-8",
    )
    writer_output = linear_pipeline.render_writer_artifacts_output(artifacts)

    resumed_artifacts, iterative_result = v7_build._writer_phase_artifacts(
        writer_mode="iterative",
        module_dir=tmp_path,
        writer_output=writer_output,
        iterative_result=None,
    )

    assert resumed_artifacts == artifacts
    assert iterative_result is not None
    assert iterative_result["module_md"] == artifacts["module.md"]
    assert iterative_result["sidecar"]["s1"]["line_start"] == 1


def test_single_shot_resume_still_rejects_unnamed_module_fence(
    tmp_path: Path,
) -> None:
    writer_output = linear_pipeline.render_writer_artifacts_output(
        _artifacts_with_unnamed_module_fence()
    )

    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="unnamed fenced block",
    ):
        v7_build._writer_phase_artifacts(
            writer_mode="single_shot",
            module_dir=tmp_path,
            writer_output=writer_output,
            iterative_result=None,
        )
