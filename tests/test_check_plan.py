"""Tests for plan-type handling in check_plan."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.check_plan import check_plan, check_russicisms, detect_plan_type, main  # noqa: I001


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_check_plan_accepts_module_level_plan(tmp_path: Path) -> None:
    plan_path = tmp_path / "module-plan.yaml"
    plan_path.write_text(
        """
module: test-001
slug: test-module
version: "1.0"
level: A1
sequence: 1
title: Test Module
word_target: 10
phase: A1.1
content_outline:
  - section: Intro
    words: 10
    points:
      - Simple module plan.
vocabulary_hints: []
""".lstrip(),
        "utf-8",
    )

    assert check_plan(plan_path) == []


def test_check_plan_accepts_b2_without_legacy_phase_or_vocabulary_hints(
    tmp_path: Path,
) -> None:
    plan_path = tmp_path / "b2-module-plan.yaml"
    plan_path.write_text(
        """
module: b2-001
slug: b2-module
version: "1.0"
level: B2
sequence: 1
title: B2 Module
word_target: 10
content_outline:
- section: Intro
  words: 10
  points:
  - Simple B2 module plan.
""".lstrip(),
        "utf-8",
    )

    assert check_plan(plan_path) == []


def test_check_plan_requires_phase_and_vocabulary_hints_outside_b2(
    tmp_path: Path,
) -> None:
    plan_path = tmp_path / "a1-module-plan.yaml"
    plan_path.write_text(
        """
module: a1-001
slug: a1-module
version: "1.0"
level: A1
sequence: 1
title: A1 Module
word_target: 10
content_outline:
- section: Intro
  words: 10
  points:
  - Simple A1 module plan.
""".lstrip(),
        "utf-8",
    )

    messages = [issue.message for issue in check_plan(plan_path)]
    assert "Missing required field: vocabulary_hints" in messages
    assert "Missing required field: phase" in messages


def test_russicism_check_allows_toy_samyi_phrase() -> None:
    issues = check_russicisms(
        {
            "title": "Добірка текстів про один і той самий інноваційний проект",
            "subtitle": "Той самий інноваційний проект у різних регістрах",
        }
    )

    assert not issues


def test_russicism_check_rejects_samyi_superlative() -> None:
    issues = check_russicisms({"title": "самий кращий варіант"})

    assert any(issue.check == "RUSSICISM" for issue in issues)


def test_check_plan_accepts_track_level_plan_ruth() -> None:
    plan_path = REPO_ROOT / "curriculum" / "l2-uk-en" / "plans" / "ruth.yaml"

    assert check_plan(plan_path) == []


def test_check_plan_detects_ruth_as_track_level() -> None:
    plan = {"modules": 112, "phases": [], "linguistic_evolution": {}}

    assert detect_plan_type(plan) == "track-level"


def test_check_plan_clearly_rejects_unknown_schema(tmp_path: Path, capsys) -> None:
    plan_path = tmp_path / "unknown-plan.yaml"
    plan_path.write_text(
        """
title: Unknown Plan
notes: Missing expected markers.
""".lstrip(),
        "utf-8",
    )

    exit_code = main([str(plan_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Unknown plan schema" in output
    assert "notes, title" in output
    assert "phases" in output
    assert "module" in output
