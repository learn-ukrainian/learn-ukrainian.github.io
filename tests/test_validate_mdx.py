"""Regression coverage for manifest-listed MDX validation."""

import sys
from pathlib import Path

import pytest

from scripts.validate import validate_mdx


def test_b1_folder_module_is_validated_and_missing_activity_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Catch silent skipping or passing of a manifest-listed B1 folder module."""
    curriculum_root = tmp_path / "curriculum"
    curriculum_path = curriculum_root / "l2-uk-en"
    module_path = curriculum_path / "b1" / "folder-lesson" / "module.md"
    module_path.parent.mkdir(parents=True)
    (curriculum_path / "curriculum.yaml").write_text(
        "levels:\n  b1:\n    modules:\n      - 01-folder-lesson\n", encoding="utf-8"
    )
    module_path.write_text("# Lesson\n\n## quiz: Practice\n", encoding="utf-8")
    mdx_root = tmp_path / "docs"
    mdx_path = mdx_root / "b1" / "folder-lesson.mdx"
    mdx_path.parent.mkdir(parents=True)
    complete_mdx = '# Lesson\n\n<Quiz title="Practice" />\n'
    mdx_path.write_text(complete_mdx, encoding="utf-8")

    monkeypatch.setattr(validate_mdx, "CURRICULUM_DIR", curriculum_root)
    monkeypatch.setattr(validate_mdx, "STARLIGHT_DOCS_DIR", mdx_root)
    monkeypatch.setattr(sys, "argv", ["validate_mdx.py", "l2-uk-en", "b1"])

    with pytest.raises(SystemExit) as valid:
        validate_mdx.main()
    assert valid.value.code == 0
    assert "Results: 1 passed, 0 failed" in capsys.readouterr().out

    mdx_path.write_text("# Lesson\n", encoding="utf-8")
    with pytest.raises(SystemExit) as missing_activity:
        validate_mdx.main()
    assert missing_activity.value.code == 1
    output = capsys.readouterr().out
    assert "Results: 0 passed, 1 failed" in output
    assert "Activity types missing in MDX: quiz" in output

    mdx_path.write_text(complete_mdx, encoding="utf-8")
    with pytest.raises(SystemExit) as restored:
        validate_mdx.main()
    assert restored.value.code == 0
    assert "Results: 1 passed, 0 failed" in capsys.readouterr().out
