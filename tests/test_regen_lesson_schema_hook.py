"""Coverage for the lesson-schema pre-commit regeneration path."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from scripts.build import generate_lesson_schema
from scripts.pre_commit import regen_lesson_schema

REPO_ROOT = Path(__file__).resolve().parent.parent


def _lesson_schema_hook() -> dict[str, object]:
    config = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    for repo in config["repos"]:
        for hook in repo["hooks"]:
            if hook["id"] == "lesson-schema-drift":
                return hook
    raise AssertionError("lesson-schema-drift hook is missing")


def test_regen_lesson_schema_uses_canonical_generator(monkeypatch, capsys):
    calls: list[tuple[object, ...]] = []

    def fake_main() -> int:
        calls.append(())
        return 0

    monkeypatch.setattr(regen_lesson_schema.generate_lesson_schema, "main", fake_main)

    assert regen_lesson_schema.main() == 0
    assert calls == [()]
    assert capsys.readouterr().out == "Lesson schema written: docs/lesson-schema.yaml\n"


def test_lesson_schema_hook_regenerates_for_all_schema_inputs():
    hook = _lesson_schema_hook()

    assert hook["pass_filenames"] is False
    assert hook["stages"] == ["pre-commit"]
    assert "scripts/pre_commit/regen_lesson_schema.py" in hook["entry"]
    assert "git diff --exit-code docs/lesson-schema.yaml" in hook["entry"]

    pattern = hook["files"]
    schema_inputs = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in generate_lesson_schema.discover_components(generate_lesson_schema.COMPONENTS_DIR)
    ]
    schema_inputs.extend(
        [
            "scripts/build/generate_lesson_schema.py",
            "scripts/build/lesson_schema_extractor.mjs",
            "scripts/pipeline/config_tables.py",
            "docs/lesson-contract.md",
        ]
    )

    assert all(re.fullmatch(pattern, path) for path in schema_inputs)
    assert not re.fullmatch(pattern, "site/src/pages/index.astro")
