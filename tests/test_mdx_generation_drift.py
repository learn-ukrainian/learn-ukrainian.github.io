from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit import check_mdx_generation_drift as mdx_drift
from scripts.audit.check_mdx_generation_drift import PROJECT_ROOT, ModuleTarget, affected_module_keys

pytestmark = pytest.mark.reads_content


def test_detects_folder_module_source() -> None:
    path = PROJECT_ROOT / "curriculum/l2-uk-en/a1/things-have-gender/module.md"

    assert affected_module_keys([path]) == {("a1", "things-have-gender")}


def test_check_targets_fails_when_generation_changes_mdx(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    mdx_root = tmp_path / "site" / "src" / "content" / "docs"
    mdx_path = mdx_root / "a1" / "things-have-gender.mdx"
    mdx_path.parent.mkdir(parents=True)
    mdx_path.write_text("old mdx\n", encoding="utf-8")

    def regenerate(_target: ModuleTarget) -> None:
        mdx_path.write_text("new mdx\n", encoding="utf-8")

    monkeypatch.setattr(mdx_drift, "MDX_ROOT", mdx_root)
    monkeypatch.setattr(mdx_drift, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(mdx_drift, "_run_generator", regenerate)
    curriculum_root = tmp_path / "curriculum/l2-uk-en"
    module_dir = curriculum_root / "a1/things-have-gender"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("legacy source\n", encoding="utf-8")
    monkeypatch.setattr(mdx_drift, "CURRICULUM_ROOT", curriculum_root)

    rc = mdx_drift.check_targets(
        [ModuleTarget(level="a1", slug="things-have-gender", local_num=8)]
    )

    assert rc == 1

    captured = capsys.readouterr()
    assert "Generated MDX drift detected" in captured.out
    assert "Hint: if your branch predates generator changes" in captured.out
    assert "verify site/src/data/lexicon-manifest.json matches" in captured.out


def test_base_first_seminar_plan_without_module_is_skipped(
    tmp_path: Path, monkeypatch
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    plan_path = (
        curriculum_root
        / "plans"
        / "folk"
        / "rodynna-obriadovist-zvychai.yaml"
    )
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text("phase: base-first\n", encoding="utf-8")

    def fail_assemble(*_args: object, **_kwargs: object) -> str:
        raise AssertionError("base-first plan without module should not generate MDX")

    monkeypatch.setattr(mdx_drift, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(mdx_drift, "MDX_ROOT", tmp_path / "site")
    monkeypatch.setattr(mdx_drift.linear_pipeline, "assemble_mdx", fail_assemble)

    assert (
        mdx_drift.check_targets(
            [
                ModuleTarget(
                    level="folk",
                    slug="rodynna-obriadovist-zvychai",
                    local_num=7,
                )
            ]
        )
        == 0
    )
