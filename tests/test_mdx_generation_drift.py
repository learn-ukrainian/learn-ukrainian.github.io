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
    mdx_root = tmp_path / "starlight" / "src" / "content" / "docs"
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
