from __future__ import annotations

from pathlib import Path

from scripts.audit import check_mdx_generation_drift as mdx_drift
from scripts.audit.check_mdx_generation_drift import PROJECT_ROOT, ModuleTarget, affected_module_keys


def test_detects_folder_module_source() -> None:
    path = PROJECT_ROOT / "curriculum/l2-uk-en/a1/things-have-gender/module.md"

    assert affected_module_keys([path]) == {("a1", "things-have-gender")}


def test_detects_folder_activity_source() -> None:
    path = PROJECT_ROOT / "curriculum/l2-uk-en/a1/things-have-gender/activities.yaml"

    assert affected_module_keys([path]) == {("a1", "things-have-gender")}


def test_detects_legacy_sibling_sources() -> None:
    paths = [
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/activities/things-have-gender.yaml",
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/vocabulary/things-have-gender.yaml",
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/meta/things-have-gender.yaml",
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/discovery/things-have-gender.yaml",
    ]

    assert affected_module_keys(paths) == {("a1", "things-have-gender")}


def test_detects_plan_source() -> None:
    path = PROJECT_ROOT / "curriculum/l2-uk-en/plans/a1/things-have-gender.yaml"

    assert affected_module_keys([path]) == {("a1", "things-have-gender")}


def test_ignores_unrelated_files() -> None:
    path = Path("docs/readme.md")

    assert affected_module_keys([path]) == set()


def test_check_targets_fails_when_generation_changes_mdx(
    tmp_path: Path, monkeypatch
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

    rc = mdx_drift.check_targets(
        [ModuleTarget(level="a1", slug="things-have-gender", local_num=8)]
    )

    assert rc == 1


def test_seminar_targets_use_assemble_mdx(tmp_path: Path, monkeypatch) -> None:
    mdx_root = tmp_path / "site" / "src" / "content" / "docs"
    mdx_path = mdx_root / "folk" / "kalendarna-obriadovist-zvychai.mdx"
    mdx_path.parent.mkdir(parents=True)

    def assemble(module_dir: Path, output_path: Path, plan_path: Path) -> str:
        assert module_dir.name == "kalendarna-obriadovist-zvychai"
        assert output_path == mdx_path
        assert plan_path.name == "kalendarna-obriadovist-zvychai.yaml"
        return "assembled mdx\n"

    def fail_legacy_generator(_args, **_kwargs):
        raise AssertionError("seminar targets must not use generate_mdx.py")

    monkeypatch.setattr(mdx_drift, "MDX_ROOT", mdx_root)
    monkeypatch.setattr(mdx_drift, "CURRICULUM_ROOT", tmp_path / "curriculum/l2-uk-en")
    monkeypatch.setattr(mdx_drift.linear_pipeline, "assemble_mdx", assemble)
    monkeypatch.setattr(mdx_drift.subprocess, "run", fail_legacy_generator)

    mdx_drift._run_generator(
        ModuleTarget(level="folk", slug="kalendarna-obriadovist-zvychai", local_num=2)
    )

    assert mdx_path.read_text(encoding="utf-8") == "assembled mdx\n"
