from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.build import linear_pipeline


def _verify_except(missing: set[str]):
    def verify(words: list[str]) -> dict[str, list[dict[str, str]]]:
        return {
            word: ([] if word in missing else [{"lemma": word}])
            for word in words
        }

    return verify


def _write_artifacts(
    module_dir: Path,
    *,
    module_text: str = "## Гаївки\n\nУ весняному календарі гаївки мають живий ритм.\n",
    activities_text: str,
) -> None:
    module_dir.mkdir()
    (module_dir / "module.md").write_text(module_text, encoding="utf-8")
    (module_dir / "activities.yaml").write_text(activities_text, encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")


def _vesum_qg_report(module_dir: Path, *, missing: set[str]) -> dict[str, object]:
    gate = linear_pipeline._vesum_gate(
        module_text=(module_dir / "module.md").read_text(encoding="utf-8"),
        activities=yaml.safe_load(
            (module_dir / "activities.yaml").read_text(encoding="utf-8")
        ),
        vocabulary=yaml.safe_load(
            (module_dir / "vocabulary.yaml").read_text(encoding="utf-8")
        ),
        resources=yaml.safe_load(
            (module_dir / "resources.yaml").read_text(encoding="utf-8")
        ),
        verify_words_fn=_verify_except(missing),
    )
    return {"gates": {"vesum_verified": gate, "passed": gate["passed"]}}


def _correction_artifact(module_dir: Path) -> dict[str, object]:
    return json.loads(
        (module_dir / "python_qg_correction_r1.json").read_text(encoding="utf-8")
    )


def test_vesum_correction_patches_activities_yaml_and_rerun_passes(
    tmp_path: Path,
) -> None:
    module_dir = tmp_path / "module"
    _write_artifacts(
        module_dir,
        activities_text='- type: custom\n  prompt: "Знайди рядок про гаівки."\n',
    )

    def reviewer_corrector(context: linear_pipeline.CorrectionContext) -> str:
        assert context.gate == "vesum_verified"
        assert "activities.yaml" in context.prompt
        assert "Знайди рядок про гаівки" in context.prompt
        return "<fixes><fix><find>гаівки</find><replace>гаївки</replace></fix></fixes>"

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        tmp_path / "plan.yaml",
        qg_runner=lambda: _vesum_qg_report(module_dir, missing={"гаівки"}),
        reviewer_corrector=reviewer_corrector,
    )

    activities_text = (module_dir / "activities.yaml").read_text(encoding="utf-8")
    parsed_activities = yaml.safe_load(activities_text)
    correction = _correction_artifact(module_dir)
    activity_record = next(
        item
        for item in correction["correction"]["artifacts"]
        if item["artifact"] == "activities.yaml"
    )

    assert report["gates"]["passed"] is True
    assert "гаївки" in activities_text
    assert "гаівки" not in activities_text
    assert parsed_activities[0]["prompt"] == "Знайди рядок про гаївки."
    assert activity_record["changed"] is True
    assert activity_record["yaml_valid"] is True


def test_vesum_yaml_breaking_correction_rolls_back_and_fails_round(
    tmp_path: Path,
) -> None:
    module_dir = tmp_path / "module"
    original_activities = '- type: custom\n  prompt: "Знайди гаівки."\n'
    _write_artifacts(module_dir, activities_text=original_activities)

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        tmp_path / "plan.yaml",
        qg_runner=lambda: _vesum_qg_report(module_dir, missing={"гаівки"}),
        reviewer_corrector=lambda _context: (
            "<fixes><fix>"
            '<find>  prompt: "Знайди гаівки."</find>'
            '<replace>  prompt: "Знайди гаївки.</replace>'
            "</fix></fixes>"
        ),
    )

    correction = _correction_artifact(module_dir)
    activities_text = (module_dir / "activities.yaml").read_text(encoding="utf-8")

    assert report["gates"]["passed"] is False
    assert report["gates"]["correction_terminal"]["gate"] == "vesum_verified"
    assert correction["rolled_back"] is True
    assert correction["rollback_reason"] == "yaml_invalid"
    assert activities_text == original_activities
    assert yaml.safe_load(activities_text)[0]["prompt"] == "Знайди гаівки."


def test_vesum_unmatched_anchor_is_not_silently_exempted(
    tmp_path: Path,
) -> None:
    module_dir = tmp_path / "module"
    stressed_typo = "гаі\u0301вки"
    _write_artifacts(
        module_dir,
        activities_text=f'- type: custom\n  prompt: "Знайди рядок про {stressed_typo}."\n',
    )

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        tmp_path / "plan.yaml",
        qg_runner=lambda: _vesum_qg_report(module_dir, missing={"гаівки"}),
        reviewer_corrector=lambda _context: (
            "<fixes><fix><find>гаівки</find><replace>гаївки</replace></fix></fixes>"
        ),
    )

    activities_text = (module_dir / "activities.yaml").read_text(encoding="utf-8")
    missing = report["gates"]["vesum_verified"]["missing"]

    assert report["gates"]["passed"] is False
    assert "correction_terminal" in report["gates"]
    assert stressed_typo in activities_text
    assert {
        linear_pipeline._normalize_for_vesum(surface).lower()
        for surface in missing
    } == {"гаівки"}


def test_vesum_module_md_correction_does_not_touch_yaml_artifacts(
    tmp_path: Path,
) -> None:
    module_dir = tmp_path / "module"
    original_activities = '- type: custom\n  prompt: "Знайди рядок про гаївки."\n'
    _write_artifacts(
        module_dir,
        module_text="## Гаївки\n\nПомилковий рядок згадує гаівки у прозі.\n",
        activities_text=original_activities,
    )

    report = linear_pipeline.run_python_qg_with_corrections(
        module_dir,
        tmp_path / "plan.yaml",
        qg_runner=lambda: _vesum_qg_report(module_dir, missing={"гаівки"}),
        reviewer_corrector=lambda _context: (
            "<fixes><fix><find>гаівки</find><replace>гаївки</replace></fix></fixes>"
        ),
    )

    assert report["gates"]["passed"] is True
    assert "гаївки у прозі" in (module_dir / "module.md").read_text(encoding="utf-8")
    assert (module_dir / "activities.yaml").read_text(encoding="utf-8") == original_activities
