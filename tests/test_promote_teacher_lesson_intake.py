"""Regression coverage for teacher-lesson intake promotion defaults."""

from pathlib import Path

from scripts.lexicon.promote_teacher_lesson_intake import DEFAULT_FULL_DECISIONS, PROJECT_ROOT


def test_default_full_decisions_is_a_committed_repository_file() -> None:
    relative_path = DEFAULT_FULL_DECISIONS.relative_to(PROJECT_ROOT)

    assert relative_path == (
        Path("data")
        / "lexicon"
        / "source-inventory-review-decisions"
        / "2026-07-23-alona-full-document-intake.yaml"
    )
    assert DEFAULT_FULL_DECISIONS.is_file()
