from pathlib import Path

import pytest

from scripts.audit import check_mdx_generation_drift as drift

pytestmark = pytest.mark.reads_content


def test_archive_detection_uses_manifest_metadata(monkeypatch):
    monkeypatch.setattr(drift, "load_manifest", lambda: {
        "levels": {"future-archive": {"base_level": "a2"}},
    })
    assert drift._filter_generatable_targets([
        drift.ModuleTarget("future-archive", "test-module", 1),
    ]) == []


@pytest.mark.parametrize("source", [None, "module.md", "legacy.md"])
@pytest.mark.parametrize("lesson_split", [False, True])
def test_a1_requires_legacy_source_without_lessons(
    tmp_path: Path, monkeypatch, source, lesson_split
):
    monkeypatch.setattr(drift, "CURRICULUM_ROOT", tmp_path)
    module_dir = tmp_path / "a1/test-module"
    module_dir.mkdir(parents=True)
    if source is not None:
        path = module_dir / source if source == "module.md" else module_dir.with_suffix(".md")
        path.write_text("legacy content\n")
    if lesson_split:
        (module_dir / "lessons.yaml").write_text("lessons: []\n")
    target = drift.ModuleTarget("a1", "test-module", 1)

    assert drift._filter_generatable_targets([target]) == (
        [target] if source is not None and not lesson_split else []
    )
