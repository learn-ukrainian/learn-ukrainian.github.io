import sys
from pathlib import Path

import pytest

from scripts.audit import check_mdx_generation_drift as drift

pytestmark = pytest.mark.reads_content


@pytest.mark.parametrize("has_project_venv", [False, True])
def test_non_seminar_generator_selects_python(
    tmp_path: Path, monkeypatch, has_project_venv: bool
) -> None:
    project_venv_python = tmp_path / ".venv" / "bin" / "python"
    if has_project_venv:
        project_venv_python.parent.mkdir(parents=True)
        project_venv_python.touch()
    calls = []

    def capture_run(args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(drift, "VENV_PYTHON", project_venv_python)
    monkeypatch.setattr(drift.subprocess, "run", capture_run)

    drift._run_generator(drift.ModuleTarget("b1", "work-and-career", 1))

    selected_python = str(project_venv_python) if has_project_venv else sys.executable
    assert calls[0][0] == [
        selected_python,
        "scripts/generate_mdx.py",
        "l2-uk-en",
        "b1",
        "1",
        *(["--validate"] if has_project_venv else []),
    ]
    if has_project_venv:
        assert len(calls) == 1
    else:
        assert len(calls) == 2
        assert calls[1][0] == [
            sys.executable,
            "scripts/validate_mdx.py",
            "l2-uk-en",
            "b1",
            "1",
        ]
    assert all(kwargs["check"] is True for _, kwargs in calls)


def test_archive_keys_are_filtered_but_native_a2_remains(monkeypatch, capsys):
    keys = drift.affected_module_keys([
        drift.CURRICULUM_ROOT / "a1-v1/sounds-letters-and-hello/module.md",
        drift.CURRICULUM_ROOT / "a2/test-module/module.md",
    ])
    targets = [drift.ModuleTarget(level, slug, 1) for level, slug in sorted(keys)]
    generated = []
    monkeypatch.setattr(drift, "_run_generator", generated.append)

    assert drift.check_targets(targets) == 0
    assert generated == [drift.ModuleTarget("a2", "test-module", 1)]
    assert "archived level with base_level" in capsys.readouterr().out


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
